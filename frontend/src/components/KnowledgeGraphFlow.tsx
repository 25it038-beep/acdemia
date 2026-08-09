'use client';

import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface KnowledgeGraphFlowProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: any;
  onEdgesChange: any;
}

export default function KnowledgeGraphFlow({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
}: KnowledgeGraphFlowProps) {
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      fitView
      attributionPosition="bottom-left"
      defaultEdgeOptions={{
        style: { stroke: 'rgba(99, 102, 241, 0.3)', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(99, 102, 241, 0.5)' },
      }}
    >
      <Background color="rgba(255,255,255,0.03)" gap={20} />
      <Controls className="glass" />
      <MiniMap
        style={{ background: 'rgba(15,15,26,0.9)' }}
        nodeColor="rgba(99,102,241,0.5)"
        maskColor="rgba(0,0,0,0.6)"
      />
    </ReactFlow>
  );
}
