'use client';

import { useState, useEffect } from 'react';
import {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import { api } from '@/lib/api';
import { Map, BookOpen } from 'lucide-react';
import dynamic from 'next/dynamic';

const WorkflowMapFlow = dynamic(() => import('@/components/WorkflowMapFlow'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});



export default function WorkflowPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);
  const [loading, setLoading] = useState(true);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string>('');

  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    try {
      const data = await api.getSubjects();
      setSubjects(data);
    } finally { setLoading(false); }
  };

  const loadWorkflow = async (subjectId: string) => {
    setLoading(true);
    try {
      const data = await api.getWorkflow(subjectId);

      const flowNodes: Node[] = data.nodes.map((n: any) => ({
        id: n.id,
        type: n.type || 'default',
        position: { x: 0, y: 0 },
        data: { ...n.data, label: n.label },
      }));

      const unitNodes = flowNodes.filter(n => n.type === 'unit');
      const chapterNodes = flowNodes.filter(n => n.type === 'chapter');

      let y = 50;
      for (const unit of unitNodes) {
        unit.position = { x: 300, y };
        y += 80;
        const unitChapters = chapterNodes.filter(
          ch => data.edges.some((e: any) => e.source === unit.id && e.target === ch.id)
        );
        for (let ci = 0; ci < unitChapters.length; ci++) {
          unitChapters[ci].position = { x: 100 + ci * 220, y };
        }
        if (unitChapters.length > 0) y += 120;
      }

      const flowEdges: Edge[] = data.edges.map((e: any, i: number) => ({
        id: `e-${i}`,
        source: e.source,
        target: e.target,
        animated: true,
        style: { stroke: 'rgba(99, 102, 241, 0.3)', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(99, 102, 241, 0.5)' },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (err) {
      console.error('Failed to load workflow:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-7rem)] flex flex-col animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Map className="w-6 h-6 text-indigo-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Workflow Map</h1>
            <p className="text-sm text-white/40">Learning roadmap & progress tracker</p>
          </div>
        </div>
        <select
          value={selectedSubject}
          onChange={(e) => {
            setSelectedSubject(e.target.value);
            if (e.target.value) loadWorkflow(e.target.value);
          }}
          className="input-glass w-64 text-sm"
        >
          <option value="">Select a course...</option>
          {subjects.map((s: any) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mb-4 text-xs text-white/50">
        <span className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-green-500/50" /> Completed
        </span>
        <span className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-indigo-500/50" /> In Progress
        </span>
        <span className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-yellow-500/50" /> Pending
        </span>
        <span className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-red-500/50" /> Needs Review
        </span>
      </div>

      {/* Flow */}
      <div className="flex-1 glass rounded-2xl border border-white/10 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : !selectedSubject ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Map className="w-16 h-16 text-white/20 mb-4" />
            <p className="text-white/60 mb-2">Select a course to view its workflow</p>
            <p className="text-white/40 text-sm">Visualize your learning path and track progress</p>
          </div>
        ) : nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <BookOpen className="w-16 h-16 text-white/20 mb-4" />
            <p className="text-white/60 mb-2">No workflow data yet</p>
            <p className="text-white/40 text-sm">Add units and chapters to build the workflow</p>
          </div>
        ) : (
          <WorkflowMapFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
          />
        )}
      </div>
    </div>
  );
}