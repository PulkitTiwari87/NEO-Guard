import { Radar } from 'lucide-react';
import type { UpcomingApproach } from '../../types/api';
import { fmtTimeUntil, neoDisplayName } from '../../utils/format';
import { HudPanel } from './HudPanel';

interface OrbitalRadarProps {
  approaches: UpcomingApproach[];
}

const PIN_COLORS = ['#00f2ff', '#ffb86f', '#cfbdff', '#7dd8de', '#5df6ff'];

/** Deterministic 0-360 angle from a designation string, so layout is stable across renders. */
function angleFor(designation: string): number {
  let hash = 0;
  for (let i = 0; i < designation.length; i++) hash = (hash * 31 + designation.charCodeAt(i)) >>> 0;
  return hash % 360;
}

/**
 * Schematic radar-style plot of real upcoming close approaches: an honest, labeled projection
 * (angle from a stable hash, radius from real miss distance) — not a live orbital simulator.
 */
export function OrbitalRadar({ approaches }: OrbitalRadarProps) {
  const pins = approaches.slice(0, 5);
  const maxDistance = Math.max(...pins.map(p => p.approach.miss_distance_au), 0.05);
  const center = 200;
  const maxRadius = 170;

  return (
    <HudPanel
      title="Orbital Approach Projection"
      icon={<Radar className="w-4 h-4" />}
      meta={pins.length > 0 ? `${pins.length} PLOTTED` : 'NO UPCOMING DATA'}
    >
      <p className="text-[10px] font-mono text-muted -mt-1">
        Schematic layout from stored orbit/approach data — angle is not a real bearing; not a live tracking feed.
      </p>
      <div className="relative w-full aspect-square max-h-[360px] mx-auto bg-canvas rounded border border-border overflow-hidden">
        <svg viewBox="0 0 400 400" className="absolute inset-0 w-full h-full">
          {[50, 110, 170].map(r => (
            <circle key={r} cx={center} cy={center} r={r} fill="none" stroke="#3a494b" strokeOpacity={0.4} strokeWidth={0.75} />
          ))}
          <line x1={center} x2={center} y1={20} y2={380} stroke="#3a494b" strokeOpacity={0.3} strokeWidth={0.5} strokeDasharray="3 3" />
          <line x1={20} x2={380} y1={center} y2={center} stroke="#3a494b" strokeOpacity={0.3} strokeWidth={0.5} strokeDasharray="3 3" />
          {pins.map((p, i) => {
            const angle = angleFor(p.neo.designation);
            const radius = 30 + (p.approach.miss_distance_au / maxDistance) * (maxRadius - 30);
            const rad = (angle * Math.PI) / 180;
            const x = center + radius * Math.cos(rad);
            const y = center + radius * Math.sin(rad);
            const color = PIN_COLORS[i % PIN_COLORS.length];
            return (
              <g key={p.neo.id}>
                <circle cx={x} cy={y} r={4} fill={color} />
                <circle cx={x} cy={y} r={8} fill="none" stroke={color} strokeOpacity={0.5} strokeWidth={1} />
              </g>
            );
          })}
        </svg>
        <div className="absolute z-10 flex flex-col items-center" style={{ left: '50%', top: '50%', transform: 'translate(-50%,-50%)' }}>
          <div className="w-3 h-3 rounded-full bg-surface-high border-2 border-accent" />
          <span className="text-[9px] font-mono text-accent mt-1 bg-canvas/80 px-1">EARTH</span>
        </div>
        {pins.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-xs font-mono text-muted uppercase tracking-wider">
            No upcoming approaches in stored data
          </div>
        )}
      </div>
      {pins.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] font-mono">
          {pins.map((p, i) => (
            <div key={p.neo.id} className="flex items-center gap-1.5 min-w-0">
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: PIN_COLORS[i % PIN_COLORS.length] }} />
              <span className="text-white truncate">{neoDisplayName(p.neo)}</span>
              <span className="text-muted shrink-0 ml-auto">
                {p.approach.relative_velocity_km_s.toFixed(1)} km/s · {fmtTimeUntil(p.approach.date)}
              </span>
            </div>
          ))}
        </div>
      )}
    </HudPanel>
  );
}
