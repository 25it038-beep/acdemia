'use client';

import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const weeklyData = [
  { day: 'Mon', hours: 2.5, score: 75 },
  { day: 'Tue', hours: 3.0, score: 82 },
  { day: 'Wed', hours: 1.5, score: 68 },
  { day: 'Thu', hours: 4.0, score: 90 },
  { day: 'Fri', hours: 2.0, score: 78 },
  { day: 'Sat', hours: 5.0, score: 95 },
  { day: 'Sun', hours: 3.5, score: 85 },
];

const subjectData = [
  { name: 'Data Structures', progress: 85, color: '#6366f1' },
  { name: 'Algorithms', progress: 62, color: '#8b5cf6' },
  { name: 'Machine Learning', progress: 45, color: '#a855f7' },
  { name: 'Database Systems', progress: 78, color: '#06b6d4' },
  { name: 'Web Development', progress: 92, color: '#10b981' },
];

export default function ProgressCharts() {
  return (
    <>
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Weekly Study Pattern */}
        <div className="card">
          <h3 className="text-sm font-semibold text-white/70 mb-4">Weekly Study Pattern</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={weeklyData}>
                <defs>
                  <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" stroke="rgba(255,255,255,0.3)" fontSize={12} />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15,15,26,0.95)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    color: '#e2e8f0',
                  }}
                />
                <Area type="monotone" dataKey="hours" stroke="#6366f1" fill="url(#colorHours)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Subject Progress */}
        <div className="card">
          <h3 className="text-sm font-semibold text-white/70 mb-4">Subject Progress</h3>
          <div className="space-y-4">
            {subjectData.map((s) => (
              <div key={s.name}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-white/70">{s.name}</span>
                  <span className="text-sm text-white/50">{s.progress}%</span>
                </div>
                <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${s.progress}%`, background: s.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Weekly Score Trend */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Quiz Score Trend</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="day" stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(15,15,26,0.95)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  color: '#e2e8f0',
                }}
              />
              <Line type="monotone" dataKey="score" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
