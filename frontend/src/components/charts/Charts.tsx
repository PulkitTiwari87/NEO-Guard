import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, AreaChart, Area, CartesianGrid,
} from 'recharts';
import type { YearCount } from '../../types/api';
import { orbitClassName } from '../../utils/format';
import { EmptyState } from '../common/EmptyState';
import { BarChart3 } from 'lucide-react';

// Shared chart styles — colors mirror the Tailwind design tokens in tailwind.config.js
// (Recharts renders inline SVG and cannot consume Tailwind utility classes directly).
const ACCENT = '#00f2ff';
const SECONDARY = '#cfbdff';
const HAZARD = '#ffb86f';
const SAFE = '#7dd8de';
const ERROR = '#ffb4ab';

const tooltipStyle = {
  backgroundColor: '#191c21',
  border: '1px solid rgba(58,73,75,0.5)',
  borderRadius: '4px',
  padding: '8px 12px',
  color: '#fff',
  fontSize: '13px',
  fontFamily: 'JetBrains Mono, ui-monospace, monospace',
};

const ORBIT_COLORS: Record<string, string> = {
  APO: ACCENT,
  AMO: SECONDARY,
  ATE: HAZARD,
  IEO: SAFE,
};

// ─── Orbit Class Distribution ─────────────────────────────────────────────────

interface OrbitClassChartProps {
  data: Record<string, number>;
}

export function OrbitClassChart({ data }: OrbitClassChartProps) {
  const chartData = Object.entries(data)
    .sort((a, b) => b[1] - a[1])
    .map(([code, count]) => ({
      name: code,
      label: `${orbitClassName(code)} (${code})`,
      count,
    }));

  if (chartData.length === 0) {
    return <EmptyState title="No orbit class data" icon={<BarChart3 className="w-6 h-6" />} />;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData} margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
        <XAxis
          dataKey="name"
          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => v.toLocaleString()}
          width={52}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          formatter={(v: number, _: string, props: { payload?: { label: string } }) => [
            v.toLocaleString(),
            props?.payload?.label ?? '',
          ]}
        />
        <Bar dataKey="count" radius={[2, 2, 0, 0]}>
          {chartData.map(entry => (
            <Cell key={entry.name} fill={ORBIT_COLORS[entry.name] ?? ACCENT} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ─── Approaches By Year ───────────────────────────────────────────────────────

interface ApproachesByYearProps {
  data: YearCount[];
}

export function ApproachesByYearChart({ data }: ApproachesByYearProps) {
  if (data.length === 0) {
    return <EmptyState title="No approach data" icon={<BarChart3 className="w-6 h-6" />} />;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
        <defs>
          <linearGradient id="approachGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={ACCENT} stopOpacity={0.3} />
            <stop offset="95%" stopColor={ACCENT} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
        <XAxis
          dataKey="year"
          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickCount={8}
        />
        <YAxis
          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={40}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          cursor={{ stroke: 'rgba(255,255,255,0.1)' }}
          formatter={(v: number) => [v.toLocaleString(), 'Approaches']}
        />
        <Area
          type="monotone"
          dataKey="count"
          stroke={ACCENT}
          strokeWidth={2}
          fill="url(#approachGrad)"
          dot={false}
          activeDot={{ r: 4, fill: ACCENT }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ─── SHAP Contribution Bar Chart ──────────────────────────────────────────────

import type { Contribution } from '../../types/api';
import { humanFeatureName } from '../../utils/format';

interface ShapChartProps {
  contributions: Contribution[];
  outputSpace: 'log_odds' | 'probability';
  baseValue: number;
}

export function ShapChart({ contributions, outputSpace, baseValue }: ShapChartProps) {
  const unit = outputSpace === 'log_odds' ? 'log-odds' : 'probability';
  const chartData = contributions.map(c => ({
    feature: humanFeatureName(c.feature),
    value: c.shap_value,
    positive: Math.max(c.shap_value, 0),
    negative: Math.min(c.shap_value, 0),
    rawValue: c.value,
  }));

  return (
    <div>
      <p className="text-caption text-muted mb-3">
        Feature influence on model output ({unit}). Base value: {baseValue.toFixed(4)}.
        <br />
        <span className="text-[10px]">
          SHAP values describe how this model uses its inputs — not physical causes.
        </span>
      </p>
      <ResponsiveContainer width="100%" height={Math.max(200, contributions.length * 36)}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 60, left: 8, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="feature"
            tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={160}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(v: number, name: string, props: { payload?: { rawValue: number } }) => {
              if (name === 'positive' || name === 'negative') {
                return [`${v > 0 ? '+' : ''}${v.toFixed(4)} ${unit}`, `Input: ${props.payload?.rawValue?.toFixed(4) ?? '—'}`];
              }
              return [v, name];
            }}
            cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          />
          <Bar dataKey="positive" fill={ACCENT} stackId="shap" radius={[0, 2, 2, 0]} />
          <Bar dataKey="negative" fill={ERROR} stackId="shap" radius={[2, 0, 0, 2]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Hazard Donut ─────────────────────────────────────────────────────────────

import { PieChart, Pie, Legend } from 'recharts';

interface HazardDonutProps {
  hazardous: number;
  nonHazardous: number;
  unknown: number;
}

export function HazardDonut({ hazardous, nonHazardous, unknown }: HazardDonutProps) {
  const data = [
    { name: 'Potentially Hazardous', value: hazardous, fill: HAZARD },
    { name: 'Non-Hazardous', value: nonHazardous, fill: SAFE },
    { name: 'Unknown (no MOID)', value: unknown, fill: '#3a494b' },
  ].filter(d => d.value > 0);

  if (data.length === 0) {
    return <EmptyState title="No classification data" icon={<BarChart3 className="w-6 h-6" />} />;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="45%"
          innerRadius="45%"
          outerRadius="70%"
          strokeWidth={0}
        >
          {data.map(entry => (
            <Cell key={entry.name} fill={entry.fill} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(v: number) => [v.toLocaleString(), '']}
        />
        <Legend
          wrapperStyle={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', paddingTop: '8px' }}
          iconType="circle"
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

// ─── Mini Metric Bar ──────────────────────────────────────────────────────────

import type { NumericSummary } from '../../types/api';

interface StatRowProps {
  label: string;
  summary: NumericSummary | null;
  unit?: string;
  precision?: number;
}

export function StatRow({ label, summary, unit = '', precision = 3 }: StatRowProps) {
  if (!summary) {
    return (
      <div className="py-3 border-b border-border last:border-0">
        <p className="text-caption text-muted uppercase tracking-wider mb-1">{label}</p>
        <p className="text-sm text-muted">No data</p>
      </div>
    );
  }

  const fmt = (v: number) => `${v.toPrecision(precision)}${unit ? ` ${unit}` : ''}`;

  return (
    <div className="py-3 border-b border-border last:border-0">
      <div className="flex items-center justify-between mb-1">
        <p className="text-caption text-muted uppercase tracking-wider">{label}</p>
        <p className="text-caption text-muted">n={summary.count.toLocaleString()}</p>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div>
          <p className="text-[10px] text-muted-subtle">Min</p>
          <p className="text-sm font-mono text-white/80">{fmt(summary.min)}</p>
        </div>
        <div>
          <p className="text-[10px] text-muted-subtle">Median</p>
          <p className="text-sm font-mono text-white font-medium">{fmt(summary.median)}</p>
        </div>
        <div>
          <p className="text-[10px] text-muted-subtle">Max</p>
          <p className="text-sm font-mono text-white/80">{fmt(summary.max)}</p>
        </div>
      </div>
    </div>
  );
}

// ─── Mini Line Chart (sparkline) ─────────────────────────────────────────────

interface SparklineProps {
  data: { value: number }[];
  color?: string;
}

export function Sparkline({ data, color = ACCENT }: SparklineProps) {
  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
