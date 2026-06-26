/**
 * Knowledge Graph Card - Apple Design Language
 */

'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { graphService, GraphData } from '@/services/graphService';
import { ArrowRight, Loader2 } from 'lucide-react';

export const KnowledgeGraphCard: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadGraph = async () => {
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
    loadGraph();
  }, []);

  if (loading) {
    return (
      <div className="apple-utility-card flex items-center justify-center min-h-[300px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-apple-blue mx-auto mb-2" />
          <p className="text-apple-caption text-apple-ink-48">Building knowledge graph…</p>
        </div>
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="apple-utility-card">
        <p className="text-apple-body text-apple-ink-48">Unable to load knowledge graph</p>
      </div>
    );
  }

  return (
    <div className="apple-utility-card">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-apple-display-md text-apple-ink mb-1">Knowledge Graph</h3>
          <p className="text-apple-caption text-apple-ink-48">Interactive visualization of your knowledge network</p>
        </div>
        <div className="text-3xl" aria-hidden="true">🧠</div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 rounded-apple-sm border border-apple-hairline bg-apple-parchment">
          <p className="text-apple-fine-print text-apple-ink-48 mb-1">Nodes</p>
          <p className="text-apple-display-md text-apple-ink">{graphData.stats.totalNodes}</p>
        </div>
        <div className="p-4 rounded-apple-sm border border-apple-hairline bg-apple-parchment">
          <p className="text-apple-fine-print text-apple-ink-48 mb-1">Connections</p>
          <p className="text-apple-display-md text-apple-ink">{graphData.stats.totalEdges}</p>
        </div>
        <div className="p-4 rounded-apple-sm border border-apple-hairline bg-apple-parchment">
          <p className="text-apple-fine-print text-apple-ink-48 mb-1">Clusters</p>
          <p className="text-apple-display-md text-apple-ink">{graphData.stats.totalClusters}</p>
        </div>
      </div>

      <div className="mb-6">
        <h4 className="text-apple-caption-strong text-apple-ink mb-3">Top Knowledge Areas</h4>
        <div className="space-y-2">
          {graphData.clusters.slice(0, 3).map((cluster) => (
            <div key={cluster.id} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: cluster.color }} />
                <span className="text-apple-caption text-apple-ink truncate">{cluster.name}</span>
              </div>
              <span className="text-apple-fine-print text-apple-ink-48">{cluster.size} items</span>
            </div>
          ))}
        </div>
      </div>

      {graphData.stats.growthTopic && (
        <div className="p-4 rounded-apple-sm border border-apple-hairline bg-apple-parchment mb-6">
          <p className="text-apple-fine-print text-apple-ink-48 mb-1">Fastest Growing</p>
          <div className="flex items-center justify-between">
            <p className="text-apple-body-strong text-apple-ink">{graphData.stats.growthTopic}</p>
            <p className="text-apple-body-strong text-apple-blue">📈 {graphData.stats.growthRate.toFixed(0)}%</p>
          </div>
        </div>
      )}

      <Link href="/knowledge-graph" className="apple-btn-primary w-full">
        Explore Graph <ArrowRight size={18} className="ml-2" />
      </Link>
    </div>
  );
};

export default KnowledgeGraphCard;
