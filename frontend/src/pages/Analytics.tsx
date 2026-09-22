import { useAnalytics } from '../hooks/useApi';
import { PageSpinner } from '../components/common/Spinner';
import { ErrorState } from '../components/common/EmptyState';
import { Card } from '../components/common/Card';
import { ApiRequestError } from '../services/api/client';
import {
  OrbitClassChart, ApproachesByYearChart, HazardDonut, StatRow,
} from '../components/charts/Charts';
import { fmtCount, orbitClassName } from '../utils/format';

export function Analytics() {
  const { data, isLoading, error, refetch } = useAnalytics();

  if (isLoading) return <PageSpinner />;

  if (error) {
    return (
      <ErrorState
        title="Unable to load analytics"
        message={error instanceof ApiRequestError ? error.message : 'Analytics data could not be retrieved.'}
        onRetry={() => refetch()}
        is503={error instanceof ApiRequestError && error.status === 503}
      />
    );
  }

  if (!data) return null;

  const total = data.total_neos;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-heading text-white">Analytics</h1>
        <p className="text-body text-muted mt-1">
          Statistical overview of {fmtCount(total)} near-Earth objects and {fmtCount(data.total_approaches)} close approaches.
        </p>
      </div>

      {/* Population summary */}
      <div>
        <h2 className="text-subheading text-white mb-4">Population</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total NEOs', value: fmtCount(total), accent: 'text-white' },
            { label: 'Potentially Hazardous', value: fmtCount(data.hazardous_count), accent: 'text-hazard', pct: total > 0 ? `${(data.hazardous_count / total * 100).toFixed(1)}%` : undefined },
            { label: 'Non-Hazardous', value: fmtCount(data.non_hazardous_count), accent: 'text-safe', pct: total > 0 ? `${(data.non_hazardous_count / total * 100).toFixed(1)}%` : undefined },
            { label: 'Flag Unknown', value: fmtCount(data.unknown_hazard_count), accent: 'text-muted' },
          ].map(({ label, value, accent, pct }) => (
            <Card key={label} className="p-5">
              <p className="text-label uppercase tracking-widest text-muted mb-2">{label}</p>
              <p className={`text-2xl font-bold ${accent}`}>{value}</p>
              {pct && <p className="text-caption text-muted mt-1">{pct} of total</p>}
            </Card>
          ))}
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hazard donut */}
        <Card className="p-6">
          <h2 className="text-subheading text-white mb-1">Hazard Classification</h2>
          <p className="text-caption text-muted mb-4">
            JPL's official PHA flag. Objects without an Earth MOID are listed as unknown.
          </p>
          <HazardDonut
            hazardous={data.hazardous_count}
            nonHazardous={data.non_hazardous_count}
            unknown={data.unknown_hazard_count}
          />
        </Card>

        {/* Orbit class */}
        <Card className="p-6">
          <h2 className="text-subheading text-white mb-1">Orbit Class Distribution</h2>
          <p className="text-caption text-muted mb-4">
            {Object.entries(data.orbit_class_counts).map(([code, count]) =>
              `${orbitClassName(code)} (${code}): ${count.toLocaleString()}`
            ).join(' · ')}
          </p>
          <OrbitClassChart data={data.orbit_class_counts} />
        </Card>
      </div>

      {/* Approaches by year */}
      <Card className="p-6">
        <h2 className="text-subheading text-white mb-1">Close Approaches by Year</h2>
        <p className="text-caption text-muted mb-4">
          Earth approaches within 0.05 au, 2000–2100 (TDB). Past values are historical;
          future values are orbital predictions and include uncertainty bounds in the detail view.
        </p>
        <ApproachesByYearChart data={data.approaches_by_year} />
      </Card>

      {/* Physical properties summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-subheading text-white mb-4">Physical Properties</h2>
          <StatRow label="Diameter (km)" summary={data.summary.diameter_km} unit="km" />
          <StatRow label="Absolute Magnitude H" summary={data.summary.absolute_magnitude_h} unit="mag" precision={4} />
          <div className="pt-3 text-caption text-muted">
            Diameter measured for {data.summary.diameter_km ? data.summary.diameter_km.count.toLocaleString() : '—'} of {fmtCount(total)} objects (≈2.9%).
            Albedo similarly sparse. Most objects have only H.
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-subheading text-white mb-4">Close-Approach Properties</h2>
          <StatRow label="Relative velocity" summary={data.summary.relative_velocity_km_s} unit="km/s" precision={4} />
          <StatRow label="Miss distance" summary={data.summary.miss_distance_au} unit="au" />
          <div className="pt-3 text-caption text-muted">
            Based on {fmtCount(data.total_approaches)} Earth approaches. Velocities include close encounters from 2000–2100.
          </div>
        </Card>
      </div>

      {/* Data note */}
      <div className="bg-surface-raised border border-border rounded-card px-5 py-4">
        <p className="text-caption text-muted">
          <strong className="text-white/60">Note:</strong>{' '}
          All values computed from the stored JPL SBDB/CAD snapshot ({data.total_neos.toLocaleString()} objects).
          A fresh database would return zeros and nulls.
          Orbit parameters and PHA flags may change as new observations are made.
        </p>
      </div>
    </div>
  );
}
