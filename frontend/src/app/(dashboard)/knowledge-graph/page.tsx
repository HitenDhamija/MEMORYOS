'use client';

import React, { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import KnowledgeGraph from '@/components/KnowledgeGraph';
import { graphService, GraphData, GraphNode } from '@/services/graphService';
import { Loader2, X } from 'lucide-react';

export default function KnowledgeGraphPage() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [filters, setFilters] = useState({ topic: '', nodeType: 'all', minSimilarity: 0 });

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        setLoading(true);
        const data = await graphService.buildGraph();
        setGraphData(data);
      } catch (error) {
        console.error('Failed to load graph:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, []);

  const filteredData = graphData ? graphService.filterGraph(graphData, {
    topic: filters.topic,
    nodeTypes: filters.nodeType === 'all' ? undefined : [filters.nodeType],
    minSimilarity: filters.minSimilarity / 100,
  }) : null;

  if (loading || !graphData) {
    return (
      <ProtectedRoute>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
            <p className="text-gray-500">Building your knowledge graph…</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  const uniqueTopics = graphData.nodes.filter(n => n.type === 'topic').map(n => n.label).sort();

  return (
    <ProtectedRoute>
      <div className="-mx-6 -mt-4 flex h-[calc(100vh-140px)] min-h-0">
        {/* Sidebar */}
        <div className="w-72 shrink-0 bg-gray-50 border-r border-gray-200 overflow-y-auto">
          <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Knowledge Graph</h1>

            <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Nodes</span><span className="font-semibold text-gray-900">{filteredData?.stats.totalNodes}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Connections</span><span className="font-semibold text-gray-900">{filteredData?.stats.totalEdges}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Clusters</span><span className="font-semibold text-gray-900">{filteredData?.stats.totalClusters}</span></div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-2">Filter by Topic</label>
                <select value={filters.topic} onChange={(e) => setFilters({ ...filters, topic: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
                  <option value="">All topics</option>
                  {uniqueTopics.map(topic => <option key={topic} value={topic}>{topic}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-2">Node Type</label>
                <select value={filters.nodeType} onChange={(e) => setFilters({ ...filters, nodeType: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
                  <option value="all">All types</option>
                  <option value="memory">📄 Memories</option>
                  <option value="collection">📂 Collections</option>
                  <option value="topic">🏷️ Topics</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-2">Min Similarity: {filters.minSimilarity}%</label>
                <input type="range" min="0" max="100" step="10" value={filters.minSimilarity} onChange={(e) => setFilters({ ...filters, minSimilarity: parseInt(e.target.value) })} className="w-full" />
              </div>
            </div>

            <div className="mt-8 pt-8 border-t border-gray-200">
              <h2 className="text-sm font-semibold text-gray-900 mb-4">Top Clusters</h2>
              <div className="space-y-3">
                {graphData.clusters.slice(0, 5).map(cluster => (
                  <div key={cluster.id} className="p-3 rounded-lg border border-gray-200 bg-white">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cluster.color }} />
                      <p className="text-xs font-semibold text-gray-900">{cluster.name}</p>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{cluster.size} items</span>
                      <span>{cluster.growth > 0 ? '📈' : '→'} {cluster.growth.toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Main Graph Area */}
        <div className="flex-1 flex min-w-0 min-h-0">
          <div className="flex-1 min-h-0">
            {filteredData && <KnowledgeGraph data={filteredData} onNodeClick={setSelectedNode} />}
          </div>

          {/* Node Detail Panel */}
          {selectedNode && (
            <div className="w-80 shrink-0 bg-white border-l border-gray-200 overflow-y-auto">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="text-2xl mb-1">{selectedNode.icon}</div>
                    <h2 className="text-lg font-bold text-gray-900">{selectedNode.label}</h2>
                    <p className="text-xs text-gray-500 mt-1">
                      {selectedNode.type === 'memory' ? '📄 Memory' : selectedNode.type === 'collection' ? '📂 Collection' : '🏷️ Topic'}
                    </p>
                  </div>
                  <button onClick={() => setSelectedNode(null)} className="p-2 hover:bg-gray-100 rounded-lg transition"><X size={20} /></button>
                </div>

                {selectedNode.metadata?.description && (
                  <p className="text-sm text-gray-600 mb-6">{selectedNode.metadata.description}</p>
                )}

                {selectedNode.type === 'memory' && selectedNode.metadata?.collections?.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-xs font-semibold text-gray-700 mb-3">Collections</h3>
                    <div className="space-y-2">
                      {selectedNode.metadata.collections.map((collection: any) => (
                        <div key={collection.id} className="px-3 py-2 rounded-lg border border-gray-200 text-sm text-gray-700">📂 {collection.name}</div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedNode.type === 'memory' && selectedNode.metadata?.topics?.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-xs font-semibold text-gray-700 mb-3">Topics</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedNode.metadata.topics.map((topic: string) => (
                        <span key={topic} className="px-3 py-1 rounded-full border border-gray-200 text-xs text-gray-700">🏷️ {topic}</span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="p-4 rounded-lg border border-gray-200 bg-gray-50 mb-6 space-y-3 text-sm">
                  {selectedNode.type === 'memory' && (
                    <>
                      <div className="flex justify-between"><span className="text-gray-500">Views</span><span className="font-semibold text-gray-900">{selectedNode.metadata?.viewCount || 0}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Discoveries</span><span className="font-semibold text-gray-900">{selectedNode.metadata?.discoveryCount || 0}</span></div>
                    </>
                  )}
                  {selectedNode.type === 'collection' && (
                    <>
                      <div className="flex justify-between"><span className="text-gray-500">Items</span><span className="font-semibold text-gray-900">{selectedNode.metadata?.memoryCount || 0}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Capacity</span><span className="font-semibold text-gray-900">{selectedNode.metadata?.maxMemories || 100}</span></div>
                    </>
                  )}
                  {selectedNode.type === 'topic' && (
                    <div className="flex justify-between"><span className="text-gray-500">Related Items</span><span className="font-semibold text-gray-900">{selectedNode.metadata?.count || 0}</span></div>
                  )}
                </div>

                <div className="text-xs text-gray-500 p-3 rounded-lg border border-gray-200">Size: {selectedNode.size?.toFixed(1)}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
