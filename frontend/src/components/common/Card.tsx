import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  as?: 'div' | 'article' | 'section';
}

export function Card({ children, className = '', hover = false, as: As = 'div' }: CardProps) {
  return (
    <As
      className={`
        hud-bracket bg-surface rounded-card border border-border shadow-card
        ${hover ? 'transition-all duration-200 hover:shadow-card-hover hover:border-border-strong cursor-pointer' : ''}
        ${className}
      `}
    >
      {children}
    </As>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  subtext?: string;
  accent?: 'blue' | 'amber' | 'green' | 'red' | 'neutral';
  icon?: ReactNode;
}

const accentColors = {
  blue: 'text-accent',
  amber: 'text-hazard',
  green: 'text-safe',
  red: 'text-red-400',
  neutral: 'text-white',
};

export function MetricCard({ label, value, subtext, accent = 'neutral', icon }: MetricCardProps) {
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-label uppercase tracking-widest text-muted-subtle mb-2">{label}</p>
          <p className={`text-3xl font-mono font-bold tracking-tight ${accentColors[accent]}`}>{value}</p>
          {subtext && <p className="text-caption text-muted mt-1">{subtext}</p>}
        </div>
        {icon && (
          <div className="text-muted">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}
