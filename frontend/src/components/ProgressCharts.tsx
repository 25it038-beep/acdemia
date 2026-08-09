'use client';

import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface ProgressChartsProps {
  weekly?: { day: string; hours: number }[];
  subjects?: { name: string; progress: number; color: string }[];
  trend?: { date: string; score: number; title: string }[];
}

const chartTooltipStyle = {
  background: 'rgba(15,15,26,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '12px',
  color: '#e2e8f0',
};

const palette = ['#6366f1', '#8b5cf6', '#a855f7', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#3b82f6'];

export default function ProgressCharts({ weekly = [], subjects = [], trend = [] }: ProgressChartsProps) {
  const subjectBars = subjects.length
    ? subjects
    : [{ name: 'No subjects yet', progress: 0, color: '#6366f1' }];

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="text-sm font-semibold text-white/70 mb-4">Weekly Study Pattern</h3>
          <div className="h-64">
            {weekly.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={weekly}>
                  <defs>
                    <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="day" stroke="rgba(255,255,255,0.3)" fontSize={12} />
                  <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} />
                  <Tooltip contentStyle={chartTooltipStyle} />
                  <Area type="monotone" dataKey="hours" stroke="#6366f1" fill="url(#colorHours)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center">
                <p className="text-sm text-white/30">No study activity yet — start a quiz or study session</p>
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <h3 className="text-sm font-semibold text-white/70 mb-4">Subject Progress</h3>
          <div className="space-y-4">
            {subjectBars.map((s, i) => (
              <div key={s.name}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-white/70">{s.name}</span>
                  <span className="text-sm text-white/50">{s.progress}%</span>
                </div>
                <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${s.progress}%`, background: s.color || palette[i % palette.length] }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Quiz Score Trend</h3>
        <div className="h-64">
          {trend.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" stroke="rgba(255,255,255,0.3)" fontSize={12} />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} domain={[0, 100]} />
                <Tooltip
                  contentStyle={chartTooltipStyle}
                  formatter={(value: number) => [`${value}%`, 'Score']}
                  labelFormatter={(label: string, payload: any[]) =>
                    payload?.[0]?.payload?.title || label
                  }
                />
                <Line type="monotone" dataKey="score" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center">
              <p className="text-sm text-white/30">No quizzes completed yet</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
