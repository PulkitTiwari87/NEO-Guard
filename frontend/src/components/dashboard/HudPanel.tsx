import type { ReactNode } from 'react';

interface HudPanelProps {
  title: string;
  icon?: ReactNode;
  meta?: ReactNode;
  children: ReactNode;
  className?: string;
}

/** Shared command-console panel shell for the Dashboard's HUD-style sections. */
export function HudPanel({ title, icon, meta, children, className = '' }: HudPanelProps) {
  return (
    <div className={`hud-bracket bg-surface border border-border rounded p-4 flex flex-col gap-3 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2.5">
        <div className="flex items-center gap-2 text-accent">
          {icon}
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">{title}</span>
        </div>
        {meta && <div className="text-[10px] font-mono text-muted">{meta}</div>}
      </div>
      {children}
    </div>
  );
}
