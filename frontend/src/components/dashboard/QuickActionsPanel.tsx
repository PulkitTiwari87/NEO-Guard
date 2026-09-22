import { Link } from 'react-router-dom';
import { Terminal, Crosshair, BarChart3, BookOpen, Info } from 'lucide-react';
import { HudPanel } from './HudPanel';

/**
 * Honest replacement for the Stitch reference's "Tactical Intervention Toolbar"
 * (RUN DEFLECTION SIMULATION / RECALCULATE ORBIT / EXPORT MPC REPORT do not exist
 * in this system). Links only to real, working features.
 */
export function QuickActionsPanel() {
  return (
    <HudPanel title="Quick Actions" icon={<Terminal className="w-4 h-4" />}>
      <div className="flex flex-col gap-2">
        <Link
          to="/predict"
          className="w-full py-2.5 px-3 rounded bg-accent-dim border border-accent/40 text-accent font-mono text-xs font-bold hover:bg-accent hover:text-surface transition-all duration-150 flex items-center justify-between"
        >
          <span className="flex items-center gap-2">
            <Crosshair className="w-4 h-4" />
            RUN A CLASSIFICATION
          </span>
          <span className="text-[10px]">REAL MODEL</span>
        </Link>
        <Link
          to="/analytics"
          className="w-full py-2.5 px-3 rounded bg-surface-raised border border-border text-white hover:text-accent hover:border-accent/40 font-mono text-xs transition-all duration-150 flex items-center justify-between"
        >
          <span className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            VIEW FULL ANALYTICS
          </span>
        </Link>
        <Link
          to="/about"
          className="w-full py-2.5 px-3 rounded bg-surface-raised border border-border text-white hover:text-accent hover:border-accent/40 font-mono text-xs transition-all duration-150 flex items-center justify-between"
        >
          <span className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            METHODOLOGY &amp; LIMITATIONS
          </span>
        </Link>
      </div>
      <div className="p-2 rounded bg-white/5 border-l-2 border-accent text-[10px] font-mono text-muted flex items-start gap-2">
        <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-accent" />
        <span>
          This system classifies orbits from 7 elements only — it is not impact-risk prediction
          and does not control any real deflection or observation hardware.
        </span>
      </div>
    </HudPanel>
  );
}
