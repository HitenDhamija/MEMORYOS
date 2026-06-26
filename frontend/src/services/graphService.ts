/**
 * Graph Service
 * 
 * Fetches knowledge graph data from the backend /graph endpoint.
 * Backend builds graph from memories, topics, collections, and embeddings.
 */

import { apiClient } from '@/utils/apiClient';

export interface GraphNode {
  id: string;
  label: string;
  type: 'memory' | 'collection' | 'topic';
  color: string;
  size: number;
  icon: string;
  metadata: any;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  type: 'similarity' | 'collection' | 'topic' | 'discovery';
  label?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  clusters: Cluster[];
  stats: GraphStats;
}

export interface Cluster {
  id: string;
  name: string;
  nodes: string[];
  color: string;
  size: number;
  growth: number;
}

export interface GraphStats {
  totalNodes: number;
  totalEdges: number;
  totalClusters: number;
  averageConnections: number;
  growthTopic: string;
  growthRate: number;
}

class GraphService {
  /**
   * Build complete knowledge graph from backend
   */
  async buildGraph(): Promise<GraphData> {
    try {
      const response = await apiClient.get('/v1/graph');
      const data = response.data;

      return {
        nodes: (data.nodes || []).map((n: any) => ({
          id: n.id,
          label: n.label,
          type: n.type,
          color: n.color || '#3b82f6',
          size: n.size || 20,
          icon: n.icon || '📄',
          metadata: n.metadata || {},
        })),
        edges: (data.edges || []).map((e: any) => ({
          source: e.source,
          target: e.target,
          weight: e.weight || 0.5,
          type: e.type || 'similarity',
          label: e.label || '',
        })),
        clusters: (data.clusters || []).map((c: any) => ({
          id: c.id,
          name: c.name,
          nodes: c.nodes || [],
          color: c.color || '#3b82f6',
          size: c.size || 1,
          growth: c.growth || 0,
        })),
        stats: {
          totalNodes: data.stats?.totalNodes || 0,
          totalEdges: data.stats?.totalEdges || 0,
          totalClusters: data.stats?.totalClusters || 0,
          averageConnections: data.stats?.averageConnections || 0,
          growthTopic: data.stats?.growthTopic || '',
          growthRate: data.stats?.growthRate || 0,
        },
      };
    } catch (error) {
      console.error('Failed to build graph:', error);
      return {
        nodes: [],
        edges: [],
        clusters: [],
        stats: {
          totalNodes: 0,
          totalEdges: 0,
          totalClusters: 0,
          averageConnections: 0,
          growthTopic: '',
          growthRate: 0,
        },
      };
    }
  }

  /**
   * Filter graph based on criteria
   */
  filterGraph(
    data: GraphData,
    filters: {
      topic?: string;
      collection?: string;
      minSimilarity?: number;
      nodeTypes?: string[];
    }
  ): GraphData {
    let nodes = [...data.nodes];
    let edges = [...data.edges];

    if (filters.topic) {
      const topicNodeId = nodes.find(
        n => n.type === 'topic' && n.label.toLowerCase() === filters.topic!.toLowerCase()
      )?.id;

      if (topicNodeId) {
        const connectedNodeIds = new Set<string>();
        connectedNodeIds.add(topicNodeId);
        edges
          .filter(e => e.source === topicNodeId || e.target === topicNodeId)
          .forEach(e => {
            connectedNodeIds.add(e.source);
            connectedNodeIds.add(e.target);
          });
        nodes = nodes.filter(n => connectedNodeIds.has(n.id));
        edges = edges.filter(e => connectedNodeIds.has(e.source) && connectedNodeIds.has(e.target));
      }
    }

    if (filters.nodeTypes && filters.nodeTypes.length > 0) {
      const typeSet = new Set(filters.nodeTypes);
      nodes = nodes.filter(n => typeSet.has(n.type));
      const nodeIds = new Set(nodes.map(n => n.id));
      edges = edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));
    }

    if (filters.minSimilarity !== undefined) {
      edges = edges.filter(
        e => e.type !== 'similarity' || e.weight >= filters.minSimilarity!
      );
    }

    return {
      nodes,
      edges,
      clusters: data.clusters,
      stats: {
        ...data.stats,
        totalNodes: nodes.length,
        totalEdges: edges.length,
      },
    };
  }

  /**
   * Get neighbors of a node
   */
  getNodeNeighbors(nodeId: string, data: GraphData, depth: number = 1): GraphData {
    const neighbors = new Set<string>();
    neighbors.add(nodeId);

    const processLayer = (currentLayer: Set<string>, currentDepth: number) => {
      if (currentDepth === 0) return;
      const nextLayer = new Set<string>();
      data.edges.forEach(edge => {
        if (currentLayer.has(edge.source)) {
          nextLayer.add(edge.target);
          neighbors.add(edge.target);
        } else if (currentLayer.has(edge.target)) {
          nextLayer.add(edge.source);
          neighbors.add(edge.source);
        }
      });
      processLayer(nextLayer, currentDepth - 1);
    };

    processLayer(neighbors, depth);

    const nodes = data.nodes.filter(n => neighbors.has(n.id));
    const edges = data.edges.filter(
      e => neighbors.has(e.source) && neighbors.has(e.target)
    );

    return {
      nodes,
      edges,
      clusters: data.clusters,
      stats: {
        ...data.stats,
        totalNodes: nodes.length,
        totalEdges: edges.length,
      },
    };
  }

  /**
   * Search nodes by label or metadata
   */
  searchNodes(query: string, data: GraphData): GraphNode[] {
    const q = query.toLowerCase();
    return data.nodes.filter(
      n => n.label.toLowerCase().includes(q) ||
           (n.metadata?.description?.toLowerCase().includes(q) || false)
    );
  }
}

export const graphService = new GraphService();
