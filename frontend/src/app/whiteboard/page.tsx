'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';
import { PenSquare, Square, Circle, Type, Minus, ArrowUpRight, Eraser, Undo2, Redo2, Download, Save, Trash2, Plus, Check, X } from 'lucide-react';

export default function WhiteboardPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [tool, setTool] = useState('pen');
  const [color, setColor] = useState('#6366f1');
  const [lineWidth, setLineWidth] = useState(3);
  const [boards, setBoards] = useState<any[]>([]);
  const [currentBoard, setCurrentBoard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Text tool state
  const [textInput, setTextInput] = useState('');
  const [textPos, setTextPos] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    loadBoards();
  }, []);

  const loadBoards = async () => {
    try {
      const data = await api.getWhiteboards();
      setBoards(data);
    } finally { setLoading(false); }
  };

  const createBoard = async () => {
    const board = await api.createWhiteboard({ name: `Board ${boards.length + 1}` });
    setCurrentBoard(board);
    loadBoards();
  };

  const getCtx = () => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    return canvas.getContext('2d');
  };

  const startDrawing = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = getCtx();
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Text tool: show input overlay on click
    if (tool === 'text') {
      setTextPos({ x, y });
      setTextInput('');
      return;
    }

    setIsDrawing(true);
    ctx.beginPath();
    ctx.moveTo(x, y);

    if (tool === 'eraser') {
      ctx.strokeStyle = '#1a1a2e';
      ctx.lineWidth = lineWidth * 4;
      ctx.globalCompositeOperation = 'source-over';
    } else {
      ctx.strokeStyle = color;
      ctx.lineWidth = lineWidth;
      ctx.globalCompositeOperation = 'source-over';
    }
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  };

  const draw = (e: React.MouseEvent) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = getCtx();
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (isDrawing) {
      const ctx = getCtx();
      if (ctx) ctx.globalCompositeOperation = 'source-over';
      setIsDrawing(false);
    }
  };

  const confirmText = () => {
    if (!textInput || !textPos) return;
    const ctx = getCtx();
    if (!ctx) return;

    ctx.font = `${lineWidth * 8}px sans-serif`;
    ctx.fillStyle = color;
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillText(textInput, textPos.x, textPos.y);
    setTextPos(null);
    setTextInput('');
  };

  const cancelText = () => {
    setTextPos(null);
    setTextInput('');
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = getCtx();
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  const saveBoard = async () => {
    if (!currentBoard) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL();
    await api.updateWhiteboard(currentBoard.id, {
      elements: [{ type: 'image', data: dataUrl }],
    });
  };

  const tools = [
    { id: 'pen', icon: PenSquare, label: 'Pen' },
    { id: 'line', icon: Minus, label: 'Line' },
    { id: 'rect', icon: Square, label: 'Rectangle' },
    { id: 'circle', icon: Circle, label: 'Circle' },
    { id: 'text', icon: Type, label: 'Text' },
    { id: 'eraser', icon: Eraser, label: 'Eraser' },
  ];

  return (
    <div className="h-[calc(100vh-7rem)] flex flex-col animate-fade-in">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <PenSquare className="w-6 h-6 text-indigo-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Whiteboard</h1>
            <p className="text-sm text-white/40">Draw, sketch, brainstorm</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={currentBoard?.id || ''}
            onChange={(e) => {
              const board = boards.find(b => b.id === e.target.value);
              setCurrentBoard(board);
            }}
            className="input-glass text-sm w-48"
          >
            <option value="">Select board...</option>
            {boards.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
          <button onClick={createBoard} className="btn-secondary p-2">
            <Plus className="w-4 h-4" />
          </button>
          <button onClick={saveBoard} className="btn-primary flex items-center gap-2 text-sm">
            <Save className="w-4 h-4" />
            Save
          </button>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 flex gap-4">
        {/* Tool Palette */}
        <div className="w-16 space-y-2">
          {tools.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => setTool(t.id)}
                className={`w-full h-12 rounded-xl flex items-center justify-center transition-all ${
                  tool === t.id
                    ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/20'
                    : 'glass glass-hover text-white/50'
                }`}
                title={t.label}
              >
                <Icon className="w-5 h-5" />
              </button>
            );
          })}

          <hr className="border-white/10 my-2" />

          <input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            className="w-full h-10 rounded-xl cursor-pointer"
          />

          <input
            type="range"
            min={1}
            max={10}
            value={lineWidth}
            onChange={(e) => setLineWidth(Number(e.target.value))}
            className="w-full"
          />

          <div className="flex gap-1">
            <button onClick={clearCanvas} className="flex-1 h-10 rounded-xl glass glass-hover flex items-center justify-center" title="Clear">
              <Trash2 className="w-4 h-4 text-red-400" />
            </button>
            <button className="flex-1 h-10 rounded-xl glass glass-hover flex items-center justify-center" title="Download">
              <Download className="w-4 h-4 text-white/50" />
            </button>
          </div>
        </div>

        {/* Canvas */}
        <div className="flex-1 glass rounded-2xl border border-white/10 overflow-hidden relative">
          <canvas
            ref={canvasRef}
            width={1200}
            height={800}
            onMouseDown={startDrawing}
            onMouseMove={draw}
            onMouseUp={stopDrawing}
            onMouseLeave={stopDrawing}
            className="w-full h-full cursor-crosshair"
            style={{ background: '#1a1a2e' }}
          />

          {/* Text input overlay */}
          {textPos && (
            <div
              className="absolute"
              style={{ left: textPos.x, top: textPos.y - 12 }}
            >
              <div className="flex items-center gap-1 bg-gray-900 border border-indigo-500/30 rounded-lg px-2 py-1">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') confirmText(); if (e.key === 'Escape') cancelText(); }}
                  className="bg-transparent text-white text-sm outline-none w-32"
                  placeholder="Type here..."
                  autoFocus
                />
                <button onClick={confirmText} className="p-1 hover:text-green-400 text-green-500">
                  <Check className="w-4 h-4" />
                </button>
                <button onClick={cancelText} className="p-1 hover:text-red-400 text-red-500">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
