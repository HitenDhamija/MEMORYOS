"""
Knowledge Graph API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User
from app.api.deps import get_current_user
from app.services.graph_service import KnowledgeGraphService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
async def get_knowledge_graph(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get knowledge graph for current user.
    
    Returns nodes (memories, topics, collections), edges (relationships),
    clusters, and statistics for visualization.
    """
    try:
        graph_data = KnowledgeGraphService.build_graph(db, current_user.id)
        return graph_data
    except Exception as e:
        logger.error(f"Failed to get knowledge graph: {e}", exc_info=True)
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


@router.get("/nodes")
async def get_nodes(
    node_type: str = Query(None, description="Filter by node type: memory, topic, collection"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get graph nodes with optional type filtering."""
    try:
        graph_data = KnowledgeGraphService.build_graph(db, current_user.id)
        
        nodes = graph_data['nodes']
        if node_type:
            nodes = [n for n in nodes if n['type'] == node_type]
        
        return {
            'nodes': nodes,
            'total': len(nodes)
        }
    except Exception as e:
        logger.error(f"Failed to get graph nodes: {e}")
        return {'nodes': [], 'total': 0}


@router.get("/edges")
async def get_edges(
    edge_type: str = Query(None, description="Filter by edge type: similarity, topic, collection"),
    min_weight: float = Query(0.0, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get graph edges with optional filtering."""
    try:
        graph_data = KnowledgeGraphService.build_graph(db, current_user.id)
        
        edges = graph_data['edges']
        if edge_type:
            edges = [e for e in edges if e['type'] == edge_type]
        
        edges = [e for e in edges if e['weight'] >= min_weight]
        
        return {
            'edges': edges,
            'total': len(edges)
        }
    except Exception as e:
        logger.error(f"Failed to get graph edges: {e}")
        return {'edges': [], 'total': 0}


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get graph statistics."""
    try:
        graph_data = KnowledgeGraphService.build_graph(db, current_user.id)
        return graph_data['stats']
    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        return {
            'totalNodes': 0,
            'totalEdges': 0,
            'totalClusters': 0,
            'averageConnections': 0,
            'growthTopic': '',
            'growthRate': 0
        }
