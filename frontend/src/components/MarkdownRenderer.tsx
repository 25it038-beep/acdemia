'use client';

import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

function MermaidDiagram({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const render = async () => {
      try {
        const mermaid = (await import('mermaid')).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: 'dark',
          themeVariables: {
            primaryColor: '#1e1b4b',
            primaryTextColor: '#e0e7ff',
            primaryBorderColor: '#6366f1',
            lineColor: '#818cf8',
            secondaryColor: '#1e293b',
            tertiaryColor: '#0f172a',
            fontSize: '14px',
          },
          fontFamily: 'ui-sans-serif, system-ui',
        });
        if (ref.current) {
          const id = `mmd-${Math.random().toString(36).slice(2)}`;
          const { svg } = await mermaid.render(id, code);
          if (!cancelled && ref.current) ref.current.innerHTML = svg;
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Diagram failed to render');
      }
    };
    render();
    return () => { cancelled = true; };
  }, [code]);

  if (error) {
    return (
      <div className="rounded-lg bg-red-500/10 border border-red-400/20 p-3 text-xs text-red-300/70">
        Diagram could not be rendered: {error}
      </div>
    );
  }

  return (
    <div className="my-4 rounded-xl bg-[#0f172a]/60 border border-white/10 p-4 overflow-x-auto flex justify-center">
      <div ref={ref} className="mermaid-svg [&_svg]:max-w-full" />
    </div>
  );
}

const components = {
  code({ node, className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || '');
    const lang = match ? match[1] : '';
    const code = String(children).replace(/\n$/, '');
    if (lang === 'mermaid') {
      return <MermaidDiagram code={code} />;
    }
    if (lang === 'math') {
      return <div className="my-3 overflow-x-auto text-white/80">{code}</div>;
    }
    if (lang) {
      return (
        <pre className="rounded-lg bg-black/40 border border-white/10 p-3 text-xs text-emerald-200 overflow-x-auto my-3">
          <code className={className}>{children}</code>
        </pre>
      );
    }
    return (
      <code
        className="bg-black/40 px-1.5 py-0.5 rounded text-emerald-200 text-xs"
        {...props}
      >
        {children}
      </code>
    );
  },
  blockquote({ children }: any) {
    return (
      <blockquote className="border-l-4 border-indigo-500/50 pl-4 my-3 text-white/60 italic">
        {children}
      </blockquote>
    );
  },
  table({ children }: any) {
    return (
      <div className="overflow-x-auto my-4 rounded-lg border border-white/10">
        <table className="w-full text-sm text-white/70 border-collapse">{children}</table>
      </div>
    );
  },
  th({ children }: any) {
    return (
      <th className="bg-white/5 px-3 py-2 text-left font-semibold text-white border-b border-white/10">
        {children}
      </th>
    );
  },
  td({ children }: any) {
    return (
      <td className="px-3 py-2 border-b border-white/5 align-top">{children}</td>
    );
  },
};

export default function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
