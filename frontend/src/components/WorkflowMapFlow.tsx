'use client';

import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

const statusColors: Record<string, string> = {
  completed: '#22c55e',
  strong: '#22c55e',
  in_progress: '#6366f1',
  pending: '#eab308',
  weak: '#ef4444',
};

const typeIcons: Record<string, string> = {
  unit: '📚',
  chapter: '📖',
  topic: '📝',
};

function WorkflowNodeComponent({ data }: { data: any }) {
  const status = data.status || 'pending';
  const color = statusColors[status] || '#6366f1';

  return (
    <div
      className="glass rounded-xl px-4 py-3 border-2 min-w-[180px] transition-all"
      style={{ borderColor: `${color}40` }}
    >
      <Handle type="target" position={Position.Top} style={{ background: color }} />
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{typeIcons[data.type] || '📌'}</span>
        <span className="text-sm font-medium text-white truncate">{data.label}</span>
      </div>
      <div className="flex items-center gap-2 mt-1">
        <div className="flex-1 h-1 rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${(data.confidence || 0) * 100}%`, background: color }}
          />
        </div>
        {status === 'completed' && <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />}
        {status === 'in_progress' && <Clock className="w-3.5 h-3.5 text-indigo-400" />}
        {status === 'weak' && <AlertTriangle className="w-3.5 h-3.5 text-red-400" />}
        {status === 'pending' && <Clock className="w-3.5 h-3.5 text-yellow-400" />}
      </div>
      {data.estimated_hours && (
        <p className="text-[10px] text-white/30 mt-1">{data.estimated_hours}h estimated</p>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: color }} />
    </div>
  );
}

const nodeTypes = {
  workflow: WorkflowNodeComponent,
  unit: WorkflowNodeComponent,
  chapter: WorkflowNodeComponent,
  topic: WorkflowNodeComponent,
};

interface WorkflowMapFlowProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: any;
  onEdgesChange: any;
}

export default function WorkflowMapFlow({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
}: WorkflowMapFlowProps) {
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      fitView
      attributionPosition="bottom-left"
    >
      <Background color="rgba(255,255,255,0.03)" gap={20} />
      <Controls className="glass" />
      <MiniMap
        style={{ background: 'rgba(15,15,26,0.9)' }}
        nodeColor={(node: any) => statusColors[node.data?.status || 'pending'] || '#6366f1'}
        maskColor="rgba(0,0,0,0.6)"
      />
    </ReactFlow>
  );
}
