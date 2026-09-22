import { Satellite } from 'lucide-react';
import { fmtCount } from '../../utils/format';
import { HudPanel } from './HudPanel';

interface DataSourcesPanelProps {
  totalNeos: number;
  totalApproaches: number;
  datasetVersion?: string;
}

/**
 * Honest replacement for the Stitch reference's fabricated "Sensor Array Telemetry" panel
 * (no real telescope/sensor feed exists). Shows the two real, documented NASA/JPL sources
 * this system actually ingests from, with real record counts (docs/DATA_SOURCE.md).
 */
export function DataSourcesPanel({ totalNeos, totalApproaches, datasetVersion }: DataSourcesPanelProps) {
  const sources = [
    { name: 'JPL SBDB Query API', detail: 'Orbital elements & physical parameters', count: totalNeos, unit: 'objects' },
    { name: 'JPL CAD API', detail: 'Predicted Earth close approaches', count: totalApproaches, unit: 'approaches' },
  ];

  return (
    <HudPanel
      title="Data Sources"
      icon={<Satellite className="w-4 h-4" />}
      meta={<span className="px-1.5 py-0.5 rounded bg-accent-dim text-accent border border-accent/30">CONNECTED</span>}
    >
      <div className="space-y-3">
        {sources.map(s => (
          <div key={s.name} className="p-2.5 rounded bg-surface-raised border border-border">
            <div className="flex items-center justify-between mb-1">
              <span className="font-mono font-bold text-white text-xs">{s.name}</span>
              <span className="text-[10px] font-mono text-accent">REAL DATA</span>
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono text-muted">
              <span>{s.detail}</span>
              <span className="text-white">{fmtCount(s.count)} {s.unit}</span>
            </div>
          </div>
        ))}
      </div>
      {datasetVersion && (
        <p className="text-[10px] font-mono text-muted truncate" title={datasetVersion}>
          DATASET SNAPSHOT: <span className="text-white/70">{datasetVersion}</span>
        </p>
      )}
      <p className="text-[10px] font-mono text-muted">
        Single ingested snapshot, not a live feed — see{' '}
        <a href="/about" className="text-accent hover:underline">Data Provenance</a>.
      </p>
    </HudPanel>
  );
}
