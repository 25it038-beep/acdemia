'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import { api } from '@/lib/api';
import { KnowledgeGraphData } from '@/types';
import { motion } from 'framer-motion';
import { Brain, Search, Filter } from 'lucide-react';
import dynamic from 'next/dynamic';

const KnowledgeGraphFlow = dynamic(() => import('@/components/KnowledgeGraphFlow'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

const conceptNodeStyle = {
  background: 'rgba(99, 102, 241, 0.15)',
  border: '1px solid rgba(99, 102, 241, 0.3)',
  borderRadius: '12px',
  padding: '12px 20px',
  color: '#e2e8f0',
  fontSize: '13px',
  fontWeight: 500,
  backdropFilter: 'blur(8px)',
  minWidth: '120px',
  textAlign: 'center' as const,
};

export default function KnowledgeGraphPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadGraph();
  }, []);

  const loadGraph = async () => {
    try {
      const data: KnowledgeGraphData = await api.getKnowledgeGraph();
      const flowNodes: Node[] = data.nodes.map((n, i) => ({
        id: n.id,
        type: 'default',
        position: {
          x: Math.cos((i / data.nodes.length) * 2 * Math.PI) * 300 + 400,
          y: Math.sin((i / data.nodes.length) * 2 * Math.PI) * 300 + 300,
        },
        data: { label: n.name },
        style: {
          ...conceptNodeStyle,
          borderColor: n.importance > 7
            ? 'rgba(99, 102, 241, 0.6)'
            : n.difficulty > 3
              ? 'rgba(239, 68, 68, 0.4)'
              : 'rgba(99, 102, 241, 0.3)',
          background: n.importance > 7
            ? 'rgba(99, 102, 241, 0.25)'
            : 'rgba(99, 102, 241, 0.1)',
        },
      }));

      const flowEdges: Edge[] = data.edges.map((e, i) => ({
        id: `e-${i}`,
        source: e.source,
        target: e.target,
        animated: true,
        style: {
          stroke: 'rgba(99, 102, 241, 0.3)',
          strokeWidth: e.weight,
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(99, 102, 241, 0.5)' },
        label: e.type,
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (err) {
      console.error('Failed to load knowledge graph:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredNodes = nodes.filter(n =>
    String(n.data.label).toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-[calc(100vh-7rem)] flex flex-col animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Brain className="w-6 h-6 text-indigo-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Knowledge Graph</h1>
            <p className="text-sm text-white/40">Interactive concept map</p>
          </div>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            type="text"
            placeholder="Search concepts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-glass pl-10 h-10 w-64 text-sm"
          />
        </div>
      </div>

      {/* Graph */}
      <div className="flex-1 glass rounded-2xl border border-white/10 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Brain className="w-16 h-16 text-white/20 mb-4" />
            <p className="text-white/60 mb-2">No concepts yet</p>
            <p className="text-white/40 text-sm">Upload learning materials to build your knowledge graph</p>
          </div>
        ) : (
          <KnowledgeGraphFlow
            nodes={filteredNodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
          />
        )}
      </div>
    </div>
  );
}