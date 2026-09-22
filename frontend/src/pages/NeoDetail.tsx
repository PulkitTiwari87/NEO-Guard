import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Crosshair, Calendar, Gauge, Atom, Info } from 'lucide-react';
import { useNeo } from '../hooks/useApi';
import { PageSpinner } from '../components/common/Spinner';
import { ErrorState } from '../components/common/EmptyState';
import { Card } from '../components/common/Card';
import { HazardBadge, OrbitClassBadge } from '../components/common/Badge';
import { ApiRequestError } from '../services/api/client';
import {
  fmtAu, fmtKm, fmtKmS, fmtDeg, fmtDays, fmt, fmtApproachDate, fmtDate,
} from '../utils/format';
import type { Approach, OrbitalData } from '../types/api';

function DataRow({ label, value, mono = true }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <span className="text-sm text-muted">{label}</span>
      <span className={`text-sm text-white ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  );
}

function OrbitalDataSection({ orbital }: { orbital: OrbitalData }) {
  return (
    <Card className="p-6">
      <h2 className="text-subheading text-white mb-4 flex items-center gap-2">
        <Atom className="w-4 h-4 text-accent" />
        Orbital Elements
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8">
        <div>
          <DataRow label="Semi-major axis (a)" value={fmtAu(orbital.semi_major_axis_au)} />
          <DataRow label="Eccentricity (e)" value={orbital.eccentricity.toFixed(6)} />
          <DataRow label="Inclination (i)" value={fmtDeg(orbital.inclination_deg)} />
          <DataRow label="Perihelion (q)" value={fmtAu(orbital.perihelion_distance_au)} />
          <DataRow label="Aphelion (Q)" value={fmtAu(orbital.aphelion_distance_au)} />
          <DataRow label="Ascending node (Ω)" value={fmtDeg(orbital.ascending_node_deg)} />
          <DataRow label="Arg. perihelion (ω)" value={fmtDeg(orbital.argument_of_perihelion_deg)} />
        </div>
        <div>
          <DataRow label="Mean anomaly (M)" value={fmtDeg(orbital.mean_anomaly_deg)} />
          <DataRow label="Orbital period" value={fmtDays(orbital.orbital_period_days)} />
          <DataRow label="Mean motion" value={`${orbital.mean_motion_deg_per_day.toFixed(4)}°/d`} />
          <DataRow label="Earth MOID" value={orbital.earth_moid_au !== null ? fmtAu(orbital.earth_moid_au) : '—'} />
          <DataRow label="Epoch (JD)" value={orbital.epoch_jd.toFixed(1)} />
          <DataRow label="Observations" value={fmt(orbital.n_obs_used)} />
          <DataRow label="Data arc" value={orbital.data_arc_days !== null ? `${orbital.data_arc_days.toLocaleString()} days` : '—'} />
          <DataRow label="First obs." value={fmtDate(orbital.first_obs_date)} />
          <DataRow label="Last obs." value={fmtDate(orbital.last_obs_date)} />
          <DataRow label="RMS residual" value={orbital.rms.toFixed(5)} />
        </div>
      </div>
    </Card>
  );
}

function ApproachRow({ approach }: { approach: Approach }) {
  return (
    <div className="py-4 border-b border-border last:border-0">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-mono text-white">{fmtApproachDate(approach.date)}</p>
          <p className="text-caption text-muted">{approach.orbiting_body}</p>
          {approach.time_uncertainty && (
            <p className="text-[10px] text-muted-subtle">Uncertainty: ±{approach.time_uncertainty}</p>
          )}
        </div>
        <div className="text-right">
          <p className="text-sm font-mono text-white">{fmtKm(approach.miss_distance_km, 0)}</p>
          <p className="text-caption text-muted">{fmtAu(approach.miss_distance_au)}</p>
          <p className="text-[10px] text-muted-subtle">
            [{approach.miss_distance_min_au.toExponential(2)} – {approach.miss_distance_max_au.toExponential(2)} au]
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm font-mono text-white">{fmtKmS(approach.relative_velocity_km_s)}</p>
          {approach.v_inf_km_s !== null && (
            <p className="text-caption text-muted">v∞ = {fmtKmS(approach.v_inf_km_s)}</p>
          )}
        </div>
      </div>
    </div>
  );
}

export function NeoDetail() {
  const { id } = useParams<{ id: string }>();
  const neoId = parseInt(id ?? '0', 10);
  const [showPredictPrompt, setShowPredictPrompt] = useState(false);

  const { data: neo, isLoading, error, refetch } = useNeo(neoId);

  if (isLoading) return <PageSpinner />;

  if (error) {
    const is404 = error instanceof ApiRequestError && error.status === 404;
    return (
      <div className="space-y-4">
        <Link to="/neos" className="inline-flex items-center gap-2 text-muted hover:text-white text-sm transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to NEO Explorer
        </Link>
        <ErrorState
          title={is404 ? 'NEO not found' : 'Unable to load NEO'}
          message={is404 ? `No NEO found with ID ${neoId}.` : (error instanceof ApiRequestError ? error.message : 'An unexpected error occurred.')}
          onRetry={is404 ? undefined : () => refetch()}
        />
      </div>
    );
  }

  if (!neo) return null;

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Back */}
      <Link to="/neos" className="inline-flex items-center gap-2 text-muted hover:text-white text-sm transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to NEO Explorer
      </Link>

      {/* Object header */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-start gap-3">
          <div>
            <p className="text-caption text-muted uppercase tracking-widest mb-1">Near-Earth Object</p>
            <h1 className="text-heading text-white">{neo.full_name}</h1>
            {neo.name && <p className="text-body text-muted">{neo.name}</p>}
            <p className="text-caption text-muted font-mono">SPK-ID: {neo.id}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <HazardBadge value={neo.is_potentially_hazardous} />
          <OrbitClassBadge orbitClass={neo.orbit_class} />
        </div>
      </div>

      {/* Physical properties */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Absolute Magnitude (H)', value: neo.absolute_magnitude_h !== null ? `${neo.absolute_magnitude_h.toFixed(2)} mag` : '—', icon: <Gauge className="w-4 h-4" /> },
          { label: 'Diameter', value: fmtKm(neo.diameter_km, 3), icon: <Atom className="w-4 h-4" /> },
          { label: 'Albedo', value: neo.albedo !== null ? neo.albedo.toFixed(3) : '—', icon: <Info className="w-4 h-4" /> },
          { label: 'Close Approaches', value: fmt(neo.close_approaches.length), icon: <Calendar className="w-4 h-4" /> },
        ].map(({ label, value, icon }) => (
          <Card key={label} className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-muted">{icon}</span>
              <p className="text-label uppercase tracking-widest text-muted">{label}</p>
            </div>
            <p className="text-xl font-bold font-mono text-white">{value}</p>
          </Card>
        ))}
      </div>

      {/* Predict for this object */}
      {!showPredictPrompt ? (
        <Card className="p-5">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="text-subheading text-white">ML Classification</h3>
              <p className="text-caption text-muted mt-0.5">
                Run a hazard classification using this object's orbital elements.
              </p>
            </div>
            <button
              onClick={() => setShowPredictPrompt(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-lg text-sm font-semibold hover:bg-accent-hover transition-colors"
            >
              <Crosshair className="w-4 h-4" />
              Predict for this NEO
            </button>
          </div>
        </Card>
      ) : (
        <Card className="p-5 border-accent/20">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-subheading text-white flex items-center gap-2">
              <Crosshair className="w-4 h-4 text-accent" />
              Run Prediction
            </h3>
            <button onClick={() => setShowPredictPrompt(false)} className="text-muted hover:text-white text-xs">
              Dismiss
            </button>
          </div>
          <p className="text-body text-muted mb-4">
            Use the Prediction page to classify this object. Its orbital elements will be pre-filled.
          </p>
          <Link
            to={`/predict?neo_id=${neo.id}&a=${neo.orbital_data.semi_major_axis_au}&e=${neo.orbital_data.eccentricity}&i=${neo.orbital_data.inclination_deg}&q=${neo.orbital_data.perihelion_distance_au}&Q=${neo.orbital_data.aphelion_distance_au}&omega=${neo.orbital_data.argument_of_perihelion_deg}&Omega=${neo.orbital_data.ascending_node_deg}`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-lg text-sm font-semibold hover:bg-accent-hover transition-colors"
          >
            Open Prediction Page
            <ArrowLeft className="w-4 h-4 rotate-180" />
          </Link>
        </Card>
      )}

      {/* Orbital data */}
      <OrbitalDataSection orbital={neo.orbital_data} />

      {/* Close approaches */}
      <Card className="p-6">
        <h2 className="text-subheading text-white mb-1 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-accent" />
          Close Approaches ({neo.close_approaches.length})
        </h2>
        <p className="text-caption text-muted mb-4">
          Earth approaches ≤ 0.05 au, 2000–2100. Dates in TDB. Future values are predictions with uncertainty bounds shown.
        </p>
        {neo.close_approaches.length === 0 ? (
          <p className="text-sm text-muted py-4">No close approaches found for this object in the database.</p>
        ) : (
          <div>
            <div className="flex text-label uppercase tracking-widest text-muted text-xs border-b border-border pb-2 mb-1">
              <span className="flex-1">Date (TDB)</span>
              <span className="text-right w-36">Miss Distance</span>
              <span className="text-right w-28">Velocity</span>
            </div>
            {neo.close_approaches.map((approach, i) => (
              <ApproachRow key={i} approach={approach} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
