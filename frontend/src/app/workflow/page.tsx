'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import { api } from '@/lib/api';
import { Map, BookOpen, Sparkles, ClipboardList, X, RefreshCw } from 'lucide-react';
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
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <WorkflowPageInner />
    </Suspense>
  );
}

function WorkflowPageInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);
  const [loading, setLoading] = useState(true);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [selectedUnit, setSelectedUnit] = useState<any>(null);
  const [exploration, setExploration] = useState<any>(null);
  const [exploring, setExploring] = useState(false);
  const [startingQuiz, setStartingQuiz] = useState(false);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);
  const [nextWorkflow, setNextWorkflow] = useState<any>(null);
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    loadSubjects();
  }, []);

  useEffect(() => {
    const subjectParam = searchParams.get('subject');
    if (subjectParam) {
      setSelectedSubject(subjectParam);
      loadWorkflow(subjectParam);
    }
  }, [searchParams]);

  useEffect(() => {
    if (!selectedSubject) return;
    const timer = setInterval(() => loadWorkflow(selectedSubject, true), 15000);
    const onFocus = () => loadWorkflow(selectedSubject, true);
    window.addEventListener('focus', onFocus);
    return () => {
      clearInterval(timer);
      window.removeEventListener('focus', onFocus);
    };
  }, [selectedSubject]);

  const loadSubjects = async () => {
    try {
      const data = await api.getSubjects();
      setSubjects(data);
    } finally { setLoading(false); }
  };

  const loadWorkflow = async (subjectId: string, silent = false) => {
    if (!silent) setLoading(true);
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
      setNextWorkflow(data.next_workflow || null);
    } catch (err) {
      console.error('Failed to load workflow:', err);
    } finally {
      setLoading(false);
    }
  };

  const openUnit = (unit: any) => {
    setSelectedUnit(unit);
    setExploration(null);
  };

  const startExploration = async () => {
    if (!selectedUnit) return;
    setExploring(true);
    try {
      const res = await api.exploreUnit(selectedUnit.id);
      setExploration(res);
    } catch (err) {
      console.error('Failed to explore:', err);
    } finally {
      setExploring(false);
    }
  };

  const startAssessment = async () => {
    if (!selectedUnit) return;
    setAssessmentError(null);
    setStartingQuiz(true);
    try {
      const res = await api.createUnitAssessment(selectedUnit.id);
      router.push(`/quizzes?quiz_id=${res.quiz_id}`);
    } catch (err: any) {
      console.error('Failed to start assessment:', err);
      setAssessmentError(err.response?.data?.detail || err.message || 'Failed to start the unit assessment. Please try again.');
    } finally {
      setStartingQuiz(false);
    }
  };

  const nodeClicked = (_: any, node: Node) => {
    if (node.type === 'unit') {
      openUnit(node.data);
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
          <div className="flex h-full">
            <div className="flex-1 relative">
              <WorkflowMapFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={nodeClicked}
              />
              {nextWorkflow && (
                <div className="absolute top-3 right-3 glass rounded-xl px-4 py-2 text-xs text-white/70 z-10">
                  Next: <span className="text-indigo-300 font-medium">{nextWorkflow.unit_name}</span>
                  {nextWorkflow.unit_status === 'locked' && ' (locked — finish the previous workflow)'}
                </div>
              )}
            </div>
            {selectedUnit && (
              <div className="w-96 border-l border-white/10 overflow-y-auto animate-fade-in">
                <div className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-white">📚 {selectedUnit.label}</h3>
                      <p className="text-xs text-white/40 mt-1">
                        {selectedUnit.completed_chapters ?? 0}/{selectedUnit.total_chapters ?? 0} chapters done
                      </p>
                    </div>
                    <button
                      onClick={() => setSelectedUnit(null)}
                      className="text-white/40 hover:text-white transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {assessmentError && (
                    <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-300">
                      {assessmentError}
                    </div>
                  )}

                  {selectedUnit.status === 'locked' ? (
                    <div className="text-sm text-white/50">
                      <p className="mb-3">This workflow is locked. Complete the previous workflow to unlock it.</p>
                      <div className="flex items-center gap-2 text-xs text-white/30">
                        <RefreshCw className="w-3 h-3" /> Progress is tracked automatically
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <button
                        onClick={startExploration}
                        disabled={exploring}
                        className="w-full flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 hover:bg-indigo-500/30 transition-all disabled:opacity-50"
                      >
                        <Sparkles className="w-4 h-4" />
                        {exploring ? 'Generating...' : (exploration?.cached ? 'Refresh Deep Exploration' : 'Start Deep Exploration')}
                      </button>
                      <button
                        onClick={startAssessment}
                        disabled={startingQuiz}
                        className="w-full flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium bg-green-500/20 border border-green-400/30 text-green-200 hover:bg-green-500/30 transition-all disabled:opacity-50"
                      >
                        <ClipboardList className="w-4 h-4" />
                        {startingQuiz ? 'Preparing...' : 'Take Unit Assessment'}
                      </button>
                    </div>
                  )}

                  {exploration && (
                    <div className="mt-5">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-semibold text-white/80">Deep Exploration</h4>
                        {exploration.cached && (
                          <span className="text-[10px] text-white/30">from cache</span>
                        )}
                      </div>
                      <div className="prose prose-invert prose-sm max-w-none text-white/60">
                        {exploration.content.split('\n').map((line: string, i: number) => {
                          if (!line.trim()) return null;
                          if (line.startsWith('#')) {
                            return (
                              <p key={i} className="text-white font-semibold mt-3 mb-1">{line.replace(/^#+\s*/, '')}</p>
                            );
                          }
                          if (line.startsWith('-') || line.startsWith('*')) {
                            return <li key={i} className="ml-4 text-white/60">{line.replace(/^[-*]\s*/, '')}</li>;
                          }
                          return <p key={i} className="mb-2">{line}</p>;
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}