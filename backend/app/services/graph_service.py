"""
Knowledge Graph Service

Builds a knowledge graph from memories, topics, and relationships.
Nodes: Memories, Topics, Collections
Edges: Similarity, Topic relationships, Collection membership
"""

import logging
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json

from app.models.models import Memory
from app.models.processed_document import ProcessedDocument
from app.models.collection import Collection, CollectionMembership
from app.services.embeddings.orchestrator import EmbeddingOrchestrator

logger = logging.getLogger(__name__)


class GraphNode:
    """Knowledge graph node."""
    def __init__(self, id: str, label: str, node_type: str, metadata: dict = None):
        self.id = id
        self.label = label
        self.type = node_type
        self.metadata = metadata or {}
        self.color = self._get_color()
        self.size = self._get_size()
        self.icon = self._get_icon()

    def _get_color(self) -> str:
        colors = {'memory': '#3b82f6', 'topic': '#8b5cf6', 'collection': '#ec4899'}
        return colors.get(self.type, '#6b7280')

    def _get_size(self) -> int:
        if self.type == 'memory':
            return 30
        elif self.type == 'collection':
            return 25
        else:
            return 20

    def _get_icon(self) -> str:
        icons = {'memory': 'file', 'topic': 'tag', 'collection': 'folder'}
        return icons.get(self.type, 'circle')

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'type': self.type,
            'color': self.color,
            'size': self.size,
            'icon': self.icon,
            'metadata': self.metadata
        }


class GraphEdge:
    """Knowledge graph edge."""
    def __init__(self, source: str, target: str, weight: float, edge_type: str, label: str = None):
        self.source = source
        self.target = target
        self.weight = min(1.0, max(0.0, weight))
        self.type = edge_type
        self.label = label or f"{weight:.2f}"

    def to_dict(self):
        return {
            'source': self.source,
            'target': self.target,
            'weight': self.weight,
            'type': self.type,
            'label': self.label
        }


class KnowledgeGraphService:
    """Build and manage knowledge graphs."""

    @staticmethod
    def build_graph(db: Session, user_id: int) -> Dict:
        """
        Build knowledge graph for user.
        Works even with partial data (no embeddings, no collections, etc.)
        """
        try:
            nodes = []
            edges = []
            topic_nodes = {}
            memory_ids = {}
            collection_ids = {}

            # 1. Get all non-deleted memories for user
            memories = db.query(Memory).filter(
                and_(
                    Memory.user_id == user_id,
                    Memory.is_deleted == False,
                )
            ).all()

            # Create memory nodes
            for mem in memories:
                node_id = f"mem_{mem.id}"
                memory_ids[mem.id] = node_id
                node = GraphNode(
                    node_id,
                    mem.title,
                    'memory',
                    metadata={
                        'file_type': mem.file_type,
                        'upload_date': mem.upload_date.isoformat() if mem.upload_date else None,
                        'size': mem.file_size
                    }
                )
                nodes.append(node)

            # 2. Get topics from processed documents
            for mem in memories:
                proc_doc = db.query(ProcessedDocument).filter(
                    ProcessedDocument.memory_id == mem.id
                ).first()

                if proc_doc and proc_doc.topics:
                    topics_data = proc_doc.topics
                    if isinstance(topics_data, str):
                        try:
                            topics_data = json.loads(topics_data)
                        except (json.JSONDecodeError, TypeError):
                            topics_data = {}

                    if isinstance(topics_data, dict):
                        for key in ['technologies', 'general', 'keywords']:
                            if key in topics_data:
                                items = topics_data[key]
                                if isinstance(items, list):
                                    for item in items[:5]:
                                        topic_name = None
                                        if isinstance(item, dict) and 'name' in item:
                                            topic_name = item['name']
                                        elif isinstance(item, str):
                                            topic_name = item

                                        if topic_name and len(topic_name) > 1:
                                            topic_id = f"topic_{topic_name.lower().replace(' ', '_').replace('/', '_')}"

                                            # Create topic node if new
                                            if topic_id not in topic_nodes:
                                                node = GraphNode(topic_id, topic_name, 'topic')
                                                nodes.append(node)
                                                topic_nodes[topic_id] = {'name': topic_name, 'memories': []}

                                            topic_nodes[topic_id]['memories'].append(mem.id)

                                            # Create edge from memory to topic
                                            if mem.id in memory_ids:
                                                edge = GraphEdge(memory_ids[mem.id], topic_id, 0.8, 'topic', 'related')
                                                edges.append(edge)

            # 3. Create topic-to-topic edges (topics that share memories)
            topic_list = list(topic_nodes.items())
            for i in range(len(topic_list)):
                for j in range(i + 1, len(topic_list)):
                    t1_id, t1_data = topic_list[i]
                    t2_id, t2_data = topic_list[j]
                    shared = set(t1_data['memories']) & set(t2_data['memories'])
                    if shared:
                        weight = min(1.0, len(shared) * 0.3)
                        edge = GraphEdge(t1_id, t2_id, weight, 'topic', 'co-occurring')
                        edges.append(edge)

            # 4. Get collections and create nodes
            collections = db.query(Collection).filter(
                and_(
                    Collection.user_id == user_id,
                    Collection.is_deleted == False
                )
            ).all()

            for coll in collections:
                node_id = f"coll_{coll.id}"
                collection_ids[coll.id] = node_id
                node = GraphNode(
                    node_id,
                    coll.name,
                    'collection',
                    metadata={'description': coll.description}
                )
                nodes.append(node)

            # 5. Add collection membership edges
            for membership in db.query(CollectionMembership).filter(
                CollectionMembership.user_id == user_id
            ).all():
                if membership.memory_id in memory_ids and membership.collection_id in collection_ids:
                    edge = GraphEdge(
                        memory_ids[membership.memory_id],
                        collection_ids[membership.collection_id],
                        1.0,
                        'collection',
                        'in'
                    )
                    edges.append(edge)

            # 6. Add similarity edges between related memories (best-effort)
            try:
                orchestrator = EmbeddingOrchestrator()
                for mem in memories[:50]:  # Limit to 50 to avoid slow queries
                    proc_doc = db.query(ProcessedDocument).filter(
                        ProcessedDocument.memory_id == mem.id
                    ).first()

                    if proc_doc:
                        try:
                            related = orchestrator.find_related_documents(
                                db, proc_doc.id, user_id, top_k=3, min_similarity=0.3
                            )
                            for related_mem_id, similarity_score in related:
                                if related_mem_id in memory_ids and related_mem_id != mem.id:
                                    edge = GraphEdge(
                                        memory_ids[mem.id],
                                        memory_ids[related_mem_id],
                                        similarity_score,
                                        'similarity',
                                        f"{similarity_score:.0%}"
                                    )
                                    edges.append(edge)
                        except Exception as e:
                            logger.debug(f"Failed to find related for memory {mem.id}: {e}")
            except Exception as e:
                logger.debug(f"Embedding orchestrator unavailable for similarity: {e}")

            # 7. Calculate clusters and stats
            clusters = KnowledgeGraphService._extract_clusters(nodes, collection_ids, topic_nodes)
            stats = KnowledgeGraphService._calculate_stats(nodes, edges, clusters)

            return {
                'nodes': [n.to_dict() for n in nodes],
                'edges': [e.to_dict() for e in edges],
                'clusters': clusters,
                'stats': stats
            }

        except Exception as e:
            logger.error(f"Failed to build graph: {e}", exc_info=True)
            return {
                'nodes': [],
                'edges': [],
                'clusters': [],
                'stats': {
                    'totalNodes': 0,
                    'totalEdges': 0,
                    'totalClusters': 0,
                    'averageConnections': 0,
                    'growthTopic': '',
                    'growthRate': 0
                }
            }

    @staticmethod
    def _extract_clusters(nodes: List[GraphNode], collection_ids: Dict, topic_nodes: Dict) -> List[Dict]:
        """Extract clusters from collections and topics."""
        clusters = []

        # Each collection is a cluster
        for coll_id, node_id in collection_ids.items():
            cluster = {
                'id': f"cluster_{coll_id}",
                'name': next((n.label for n in nodes if n.id == node_id), 'Cluster'),
                'nodes': [node_id],
                'color': '#ec4899',
                'size': 1,
                'growth': 0
            }
            clusters.append(cluster)

        # Each topic with 2+ connected memories is a cluster
        for topic_id, topic_data in topic_nodes.items():
            if len(topic_data['memories']) >= 2:
                cluster = {
                    'id': f"cluster_{topic_id}",
                    'name': topic_data['name'],
                    'nodes': [f"mem_{mid}" for mid in topic_data['memories']],
                    'color': '#8b5cf6',
                    'size': len(topic_data['memories']),
                    'growth': 0
                }
                clusters.append(cluster)

        return clusters

    @staticmethod
    def _calculate_stats(nodes: List[GraphNode], edges: List[GraphEdge], clusters: List[Dict]) -> Dict:
        """Calculate graph statistics."""
        node_degrees = {}
        for edge in edges:
            node_degrees[edge.source] = node_degrees.get(edge.source, 0) + 1
            node_degrees[edge.target] = node_degrees.get(edge.target, 0) + 1

        avg_connections = sum(node_degrees.values()) / len(node_degrees) if node_degrees else 0

        growth_topic = ''
        max_connections = 0
        for node in nodes:
            if node.type == 'topic':
                connections = node_degrees.get(node.id, 0)
                if connections > max_connections:
                    max_connections = connections
                    growth_topic = node.label

        return {
            'totalNodes': len(nodes),
            'totalEdges': len(edges),
            'totalClusters': len(clusters),
            'averageConnections': round(avg_connections, 1),
            'growthTopic': growth_topic,
            'growthRate': round(max_connections / max(len(nodes), 1) * 100, 1) if nodes else 0
        }
