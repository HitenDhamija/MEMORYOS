'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { GraphData, GraphNode } from '@/services/graphService';
import { ZoomIn, ZoomOut, RotateCcw, Search } from 'lucide-react';

interface KnowledgeGraphProps {
  data: GraphData;
  onNodeClick?: (node: GraphNode) => void;
}

interface ViewState {
  scale: number;
  offsetX: number;
  offsetY: number;
}

interface NodePosition {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ data, onNodeClick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [viewState, setViewState] = useState<ViewState>({ scale: 1, offsetX: 0, offsetY: 0 });
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const nodePositionsRef = useRef<Map<string, NodePosition>>(new Map());
  const animFrameRef = useRef<number>();

  // Initialize node positions — spread across a larger area
  useEffect(() => {
    const positions = new Map<string, NodePosition>();
    const count = data.nodes.length;
    if (count === 0) { nodePositionsRef.current = positions; return; }

    // Use a wider spread based on node count
    const baseRadius = Math.max(200, Math.sqrt(count) * 60);

    data.nodes.forEach((node, index) => {
      // Golden angle distribution for better spread
      const angle = index * 2.39996323; // golden angle in radians
      const radius = baseRadius * Math.sqrt((index + 1) / count);
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;
      positions.set(node.id, { x, y, vx: 0, vy: 0 });
    });

    nodePositionsRef.current = positions;
  }, [data.nodes]);

  // Resize canvas
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      const ctx = canvas.getContext('2d');
      if (ctx) ctx.scale(dpr, dpr);
    };

    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // Auto-zoom to fit all nodes after layout stabilizes
  const autoFit = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const positions = nodePositionsRef.current;
    if (positions.size === 0) return;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    positions.forEach(pos => {
      minX = Math.min(minX, pos.x);
      maxX = Math.max(maxX, pos.x);
      minY = Math.min(minY, pos.y);
      maxY = Math.max(maxY, pos.y);
    });

    const graphWidth = maxX - minX + 100;
    const graphHeight = maxY - minY + 100;
    const scaleX = rect.width / graphWidth;
    const scaleY = rect.height / graphHeight;
    const scale = Math.min(scaleX, scaleY, 1.5) * 0.85;

    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    setViewState({
      scale,
      offsetX: -centerX * scale,
      offsetY: -centerY * scale,
    });
  }, []);

  // Force-directed simulation — stronger forces
  useEffect(() => {
    let running = true;
    let tickCount = 0;
    const MAX_TICKS = 300;

    const simulate = () => {
      if (!running || tickCount >= MAX_TICKS) return;
      tickCount++;

      const positions = nodePositionsRef.current;
      const nodeCount = data.nodes.length;

      // Damping — stronger at start, weaker later
      const damping = tickCount < 100 ? 0.85 : 0.92;
      positions.forEach(pos => {
        pos.vx *= damping;
        pos.vy *= damping;
      });

      // Repulsion — much stronger, scales with node count
      const repulsionStrength = Math.max(500, nodeCount * 30);
      data.nodes.forEach((nodeA, i) => {
        data.nodes.forEach((nodeB, j) => {
          if (i >= j) return;
          const posA = positions.get(nodeA.id);
          const posB = positions.get(nodeB.id);
          if (!posA || !posB) return;

          const dx = posB.x - posA.x;
          const dy = posB.y - posA.y;
          const distSq = dx * dx + dy * dy;
          const dist = Math.sqrt(distSq) + 0.1;
          const repulsion = repulsionStrength / distSq;

          const fx = (dx / dist) * repulsion;
          const fy = (dy / dist) * repulsion;
          posA.vx -= fx;
          posA.vy -= fy;
          posB.vx += fx;
          posB.vy += fy;
        });
      });

      // Attraction along edges — stronger
      data.edges.forEach(edge => {
        const posA = positions.get(edge.source);
        const posB = positions.get(edge.target);
        if (!posA || !posB) return;

        const dx = posB.x - posA.x;
        const dy = posB.y - posA.y;
        const dist = Math.sqrt(dx * dx + dy * dy) + 0.1;
        const idealDist = 120;
        const attraction = (dist - idealDist) * 0.08;

        const fx = (dx / dist) * attraction;
        const fy = (dy / dist) * attraction;
        posA.vx += fx;
        posA.vy += fy;
        posB.vx -= fx;
        posB.vy -= fy;
      });

      // Center gravity — pull nodes toward center to prevent drift
      const centerStrength = 0.01;
      positions.forEach(pos => {
        pos.vx -= pos.x * centerStrength;
        pos.vy -= pos.y * centerStrength;
      });

      // Apply velocities with bounds
      const maxSpeed = 10;
      positions.forEach(pos => {
        const speed = Math.sqrt(pos.vx * pos.vx + pos.vy * pos.vy);
        if (speed > maxSpeed) {
          pos.vx = (pos.vx / speed) * maxSpeed;
          pos.vy = (pos.vy / speed) * maxSpeed;
        }
        pos.x += pos.vx;
        pos.y += pos.vy;
      });

      // Auto-fit after layout stabilizes
      if (tickCount === 80) {
        autoFit();
      }

      animFrameRef.current = requestAnimationFrame(simulate);
    };

    animFrameRef.current = requestAnimationFrame(simulate);

    return () => {
      running = false;
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [data.nodes, data.edges, autoFit]);

  // Rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let active = true;

    const render = () => {
      if (!active) return;
      const container = containerRef.current;
      if (!container) { requestAnimationFrame(render); return; }
      const rect = container.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;

      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, w, h);

      const { scale, offsetX, offsetY } = viewState;
      ctx.save();
      ctx.translate(w / 2 + offsetX, h / 2 + offsetY);
      ctx.scale(scale, scale);

      // Draw edges
      ctx.strokeStyle = 'rgba(180, 180, 180, 0.3)';
      ctx.lineWidth = 1 / scale;
      data.edges.forEach(edge => {
        const posA = nodePositionsRef.current.get(edge.source);
        const posB = nodePositionsRef.current.get(edge.target);
        if (!posA || !posB) return;
        ctx.beginPath();
        ctx.moveTo(posA.x, posA.y);
        ctx.lineTo(posB.x, posB.y);
        ctx.stroke();
      });

      // Draw nodes
      data.nodes.forEach(node => {
        const pos = nodePositionsRef.current.get(node.id);
        if (!pos) return;
        const isHovered = hoveredNode === node.id;
        const isSelected = selectedNode === node.id;
        const isSearchMatch = searchQuery && node.label.toLowerCase().includes(searchQuery.toLowerCase());
        const baseRadius = Math.max(8, (node.size || 12));
        const radius = baseRadius * (isHovered || isSelected ? 1.3 : 1);

        // Node circle
        ctx.fillStyle = isSearchMatch ? '#3b82f6' : node.color;
        ctx.globalAlpha = (searchQuery && !isSearchMatch) ? 0.3 : 1;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
        ctx.fill();

        // Selection/hover ring
        if (isSelected) {
          ctx.strokeStyle = '#000';
          ctx.lineWidth = 3 / scale;
          ctx.stroke();
        } else if (isHovered) {
          ctx.strokeStyle = '#666';
          ctx.lineWidth = 2 / scale;
          ctx.stroke();
        }

        ctx.globalAlpha = 1;

        // Label — BELOW the node, not on top
        ctx.fillStyle = '#333';
        ctx.font = `bold ${11 / scale}px -apple-system, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        const label = node.label.length > 20 ? node.label.substring(0, 17) + '...' : node.label;
        ctx.fillText(label, pos.x, pos.y + radius + 4 / scale);
      });

      ctx.restore();
      requestAnimationFrame(render);
    };

    requestAnimationFrame(render);
    return () => { active = false; };
  }, [data.nodes, data.edges, viewState, hoveredNode, selectedNode, searchQuery]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const { scale, offsetX, offsetY } = viewState;
    const x = (e.clientX - rect.left - rect.width / 2 - offsetX) / scale;
    const y = (e.clientY - rect.top - rect.height / 2 - offsetY) / scale;

    let nearestNode: string | null = null;
    let minDist = 25 / scale;

    data.nodes.forEach(node => {
      const pos = nodePositionsRef.current.get(node.id);
      if (!pos) return;
      const dist = Math.sqrt(Math.pow(pos.x - x, 2) + Math.pow(pos.y - y, 2));
      if (dist < minDist) {
        minDist = dist;
        nearestNode = node.id;
      }
    });

    setHoveredNode(nearestNode);
  }, [data.nodes, viewState]);

  const handleClick = () => {
    if (hoveredNode) {
      const node = data.nodes.find(n => n.id === hoveredNode);
      if (node) {
        setSelectedNode(hoveredNode);
        onNodeClick?.(node);
      }
    }
  };

  const handleZoom = (delta: number) => {
    setViewState(prev => ({
      ...prev,
      scale: Math.max(0.2, Math.min(5, prev.scale * (1 + delta * 0.15))),
    }));
  };

  const handleReset = () => {
    setSelectedNode(null);
    setSearchQuery('');
    autoFit();
  };

  // Mouse wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -1 : 1;
    handleZoom(delta);
  }, []);

  return (
    <div ref={containerRef} className="w-full h-full flex flex-col bg-white overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 shrink-0">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search nodes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>

        <div className="flex items-center gap-2 ml-4">
          <button onClick={() => handleZoom(-1)} className="p-2 hover:bg-gray-100 rounded-lg transition" title="Zoom out">
            <ZoomOut size={18} />
          </button>
          <button onClick={() => handleZoom(1)} className="p-2 hover:bg-gray-100 rounded-lg transition" title="Zoom in">
            <ZoomIn size={18} />
          </button>
          <button onClick={handleReset} className="p-2 hover:bg-gray-100 rounded-lg transition" title="Reset view">
            <RotateCcw size={18} />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative min-h-0">
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onClick={handleClick}
          onWheel={handleWheel}
          className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing"
        />
      </div>

      {/* Stats */}
      <div className="p-3 border-t border-gray-200 text-sm text-gray-500 shrink-0">
        <span>{data.stats.totalNodes} nodes</span>
        <span className="mx-2">•</span>
        <span>{data.stats.totalEdges} connections</span>
        <span className="mx-2">•</span>
        <span>{data.stats.totalClusters} clusters</span>
      </div>
    </div>
  );
};

export default KnowledgeGraph;
