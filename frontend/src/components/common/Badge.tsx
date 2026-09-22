interface BadgeProps {
  children: React.ReactNode;
  variant?: 'hazardous' | 'safe' | 'unknown' | 'experimental' | 'validated' | 'production' | 'deprecated' | 'neutral';
  size?: 'sm' | 'md';
}

const variantClasses: Record<string, string> = {
  hazardous: 'bg-hazard-dim text-hazard border border-hazard/40',
  safe: 'bg-safe-dim text-safe border border-safe/30',
  unknown: 'bg-white/5 text-muted border border-white/10',
  experimental: 'bg-hazard-dim text-hazard border border-hazard/40',
  validated: 'bg-accent-dim text-accent border border-accent/30',
  production: 'bg-safe-dim text-safe border border-safe/30',
  deprecated: 'bg-white/5 text-muted border border-white/10',
  neutral: 'bg-white/5 text-white/70 border border-white/10',
};

const sizeClasses = {
  sm: 'text-[10px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-1',
};

export function Badge({ children, variant = 'neutral', size = 'md' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center font-mono font-semibold rounded uppercase tracking-wider ${variantClasses[variant]} ${sizeClasses[size]}`}>
      {children}
    </span>
  );
}

export function HazardBadge({ value }: { value: boolean | null }) {
  if (value === null) return <Badge variant="unknown">Unknown</Badge>;
  if (value) return <Badge variant="hazardous">PHA</Badge>;
  return <Badge variant="safe">Non-PHA</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  const variant = status as BadgeProps['variant'];
  const labels: Record<string, string> = {
    experimental: 'Experimental',
    validated: 'Validated',
    production: 'Production',
    deprecated: 'Deprecated',
  };
  return <Badge variant={variant ?? 'neutral'}>{labels[status] ?? status}</Badge>;
}

export function OrbitClassBadge({ orbitClass }: { orbitClass: string }) {
  const colors: Record<string, string> = {
    APO: 'bg-accent-dim text-accent border border-accent/30',
    AMO: 'bg-secondary-dim text-secondary border border-secondary/30',
    ATE: 'bg-hazard-dim text-hazard border border-hazard/30',
    IEO: 'bg-safe-dim text-safe border border-safe/30',
  };
  const cls = colors[orbitClass] ?? 'bg-white/5 text-white/70 border border-white/10';
  return (
    <span className={`inline-flex items-center text-xs font-mono font-semibold px-2 py-1 rounded ${cls}`}>
      {orbitClass}
    </span>
  );
}
