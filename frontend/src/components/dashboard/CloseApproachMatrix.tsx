import { Link } from 'react-router-dom';
import { Table } from 'lucide-react';
import type { UpcomingApproach } from '../../types/api';
import { fmtTimeUntil, neoDisplayName, orbitClassName } from '../../utils/format';
import { HudPanel } from './HudPanel';

interface CloseApproachMatrixProps {
  approaches: UpcomingApproach[];
}

/** Real, stored close approaches — no fabricated "defense status" or "telemetry lock" states. */
export function CloseApproachMatrix({ approaches }: CloseApproachMatrixProps) {
  return (
    <HudPanel
      title="Close-Approach Encounter Matrix"
      icon={<Table className="w-4 h-4" />}
      meta={approaches.length > 0 ? `${approaches.length} UPCOMING (STORED DATA)` : undefined}
    >
      {approaches.length === 0 ? (
        <p className="text-xs font-mono text-muted py-4 text-center uppercase tracking-wider">
          No upcoming close approaches in the current snapshot
        </p>
      ) : (
        <div className="overflow-x-auto -mx-1">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-muted uppercase border-b border-border text-[10px]">
                <th className="py-2 px-1">Designation</th>
                <th className="py-2 px-1">Class</th>
                <th className="py-2 px-1">Rel. Velocity</th>
                <th className="py-2 px-1">Miss Distance</th>
                <th className="py-2 px-1">T-Minus</th>
                <th className="py-2 px-1 text-right">Hazard Flag</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {approaches.map(({ neo, approach }) => (
                <tr key={`${neo.id}-${approach.date}`} className="hover:bg-white/5 transition-colors">
                  <td className="py-2.5 px-1">
                    <Link to={`/neos/${neo.id}`} className="text-white font-semibold hover:text-accent transition-colors">
                      {neoDisplayName(neo)}
                    </Link>
                  </td>
                  <td className="py-2.5 px-1 text-muted">{orbitClassName(neo.orbit_class)}</td>
                  <td className="py-2.5 px-1 text-accent">{approach.relative_velocity_km_s.toFixed(2)} km/s</td>
                  <td className="py-2.5 px-1 text-white">{approach.miss_distance_au.toPrecision(3)} au</td>
                  <td className="py-2.5 px-1 text-muted">{fmtTimeUntil(approach.date)}</td>
                  <td className="py-2.5 px-1 text-right">
                    {neo.is_potentially_hazardous === null ? (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-white/5 text-muted border border-white/10">UNKNOWN</span>
                    ) : neo.is_potentially_hazardous ? (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-hazard-dim text-hazard border border-hazard/40">PHA</span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-safe-dim text-safe border border-safe/30">NON-PHA</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </HudPanel>
  );
}
