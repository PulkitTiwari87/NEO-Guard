import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Crosshair, AlertTriangle, Info } from 'lucide-react';
import { predict } from '../services/api/predictionApi';
import { useModels } from '../hooks/useApi';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { ShapChart } from '../components/charts/Charts';
import { HazardBadge, StatusBadge } from '../components/common/Badge';
import { ApiRequestError } from '../services/api/client';
import type { PredictFeatures, PredictResponse } from '../types/api';

// Local type for 422 detail
type FieldError = { loc: string[]; msg: string; type: string };

// ─── Form field ───────────────────────────────────────────────────────────────

interface FieldInputProps {
  id: string;
  label: string;
  description: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
  placeholder?: string;
  unit?: string;
}

function FieldInput({ id, label, description, value, onChange, error, placeholder, unit }: FieldInputProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-white/80 mb-1">
        {label}
        {unit && <span className="text-muted ml-1 font-normal">[{unit}]</span>}
      </label>
      <p className="text-caption text-muted mb-1">{description}</p>
      <input
        id={id}
        type="number"
        step="any"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className={`
          w-full bg-surface border rounded-lg px-3 py-2 text-sm font-mono text-white
          placeholder:text-muted focus:outline-none focus:border-accent/60 transition-colors
          ${error ? 'border-red-500/50' : 'border-border'}
        `}
        aria-describedby={error ? `${id}-error` : undefined}
        aria-invalid={!!error}
      />
      {error && (
        <p id={`${id}-error`} className="text-xs text-red-400 mt-1">{error}</p>
      )}
    </div>
  );
}

// ─── Prediction result ────────────────────────────────────────────────────────

function PredictionResult({ result }: { result: PredictResponse }) {
  const isHazardous = result.prediction === 1;
  const pctProbability = (result.probability * 100).toFixed(1);
  const pctThreshold = (result.threshold * 100).toFixed(1);

  return (
    <div className="space-y-5 animate-slide-up">
      {/* Result card */}
      <Card className={`p-6 ${isHazardous ? 'border-hazard/20' : 'border-safe/20'}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-label uppercase tracking-widest text-muted mb-2">ML Classification</p>
            <div className="flex items-center gap-3 mb-3">
              <HazardBadge value={isHazardous} />
              <StatusBadge status={result.model_status} />
            </div>
            <p className="text-2xl font-bold font-mono text-white">
              {pctProbability}%
              <span className="text-sm font-normal text-muted ml-2">probability</span>
            </p>
            <p className="text-caption text-muted mt-1">
              Threshold: {pctThreshold}% · Model: {result.model_version}
            </p>
          </div>
          <div className={`p-3 rounded-xl ${isHazardous ? 'bg-hazard/10' : 'bg-safe/10'}`}>
            <Crosshair className={`w-6 h-6 ${isHazardous ? 'text-hazard' : 'text-safe'}`} />
          </div>
        </div>

        {/* Probability bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs text-muted mb-1">
            <span>0%</span>
            <span>Threshold {pctThreshold}%</span>
            <span>100%</span>
          </div>
          <div className="relative h-2 bg-surface-overlay rounded-full overflow-hidden">
            <div
              className={`absolute left-0 top-0 h-full rounded-full transition-all duration-500 ${isHazardous ? 'bg-hazard' : 'bg-safe'}`}
              style={{ width: `${result.probability * 100}%` }}
              role="progressbar"
              aria-valuenow={result.probability * 100}
              aria-valuemin={0}
              aria-valuemax={100}
            />
            <div
              className="absolute top-0 h-full w-0.5 bg-white/30"
              style={{ left: `${result.threshold * 100}%` }}
            />
          </div>
        </div>
      </Card>

      {/* Disclaimer — always shown */}
      <div className="flex gap-3 bg-surface-raised border border-border rounded-card px-4 py-3">
        <Info className="w-4 h-4 text-muted flex-shrink-0 mt-0.5" />
        <p className="text-caption text-muted">{result.disclaimer}</p>
      </div>

      {/* SHAP explanation */}
      {result.explanation && (
        <Card className="p-6">
          <h3 className="text-subheading text-white mb-4">Feature Influence (SHAP)</h3>
          <ShapChart
            contributions={result.explanation.contributions}
            outputSpace={result.explanation.output_space}
            baseValue={result.explanation.base_value}
          />
        </Card>
      )}
    </div>
  );
}

// ─── Prediction page ──────────────────────────────────────────────────────────

const INITIAL: Record<keyof PredictFeatures, string> = {
  semi_major_axis_au: '',
  eccentricity: '',
  inclination_deg: '',
  perihelion_distance_au: '',
  aphelion_distance_au: '',
  ascending_node_deg: '',
  argument_of_perihelion_deg: '',
};

export function Prediction() {
  const [searchParams] = useSearchParams();
  const models = useModels();
  const [fields, setFields] = useState<Record<keyof PredictFeatures, string>>(INITIAL);
  const [modelVersion, setModelVersion] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Pre-fill from URL params (coming from NEO detail page)
  useEffect(() => {
    const a = searchParams.get('a');
    const e = searchParams.get('e');
    const i = searchParams.get('i');
    const q = searchParams.get('q');
    const Q = searchParams.get('Q');
    const omega = searchParams.get('omega');
    const Omega = searchParams.get('Omega');
    if (a || e || i || q || Q || omega || Omega) {
      setFields({
        semi_major_axis_au: a ?? '',
        eccentricity: e ?? '',
        inclination_deg: i ?? '',
        perihelion_distance_au: q ?? '',
        aphelion_distance_au: Q ?? '',
        argument_of_perihelion_deg: omega ?? '',
        ascending_node_deg: Omega ?? '',
      });
    }
  }, [searchParams]);

  const mutation = useMutation({
    mutationFn: (req: Parameters<typeof predict>[0]) => predict(req),
  });

  function setField(key: keyof PredictFeatures, value: string) {
    setFields(prev => ({ ...prev, [key]: value }));
    setFieldErrors(prev => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  function parseFeatures(): PredictFeatures | null {
    const errors: Record<string, string> = {};
    const parsed: Partial<PredictFeatures> = {};

    for (const [k, v] of Object.entries(fields)) {
      const n = parseFloat(v);
      if (v.trim() === '' || isNaN(n)) {
        errors[k] = 'Required — enter a numeric value';
      } else {
        (parsed as Record<string, number>)[k] = n;
      }
    }

    if (Object.keys(errors).length) {
      setFieldErrors(errors);
      return null;
    }
    return parsed as PredictFeatures;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const features = parseFeatures();
    if (!features) return;

    const neoIdParam = searchParams.get('neo_id');

    mutation.mutate({
      features,
      model_version: modelVersion || undefined,
      neo_id: neoIdParam ? parseInt(neoIdParam, 10) : undefined,
    });
  }

  // Parse 422 field errors from backend
  function handle422Errors(err: ApiRequestError) {
    if (Array.isArray(err.detail)) {
      const fieldErrs: Record<string, string> = {};
      (err.detail as FieldError[]).forEach(d => {
        const field = d.loc[d.loc.length - 1];
        fieldErrs[field] = d.msg;
      });
      setFieldErrors(fieldErrs);
    }
  }

  const error = mutation.error;
  const is422 = error instanceof ApiRequestError && error.status === 422;

  // Show 422 errors in form
  useEffect(() => {
    if (is422 && error instanceof ApiRequestError) {
      handle422Errors(error);
    }
  }, [is422, error]);

  const formFields: Array<{
    key: keyof PredictFeatures;
    label: string;
    description: string;
    unit: string;
    placeholder: string;
  }> = [
    { key: 'semi_major_axis_au', label: 'Semi-major axis (a)', description: 'Mean orbital radius', unit: 'au', placeholder: '0.9' },
    { key: 'eccentricity', label: 'Eccentricity (e)', description: 'Orbital eccentricity, 0 ≤ e < 1', unit: '', placeholder: '0.19' },
    { key: 'inclination_deg', label: 'Inclination (i)', description: 'Orbital plane tilt, 0–180°', unit: 'deg', placeholder: '3.3' },
    { key: 'perihelion_distance_au', label: 'Perihelion distance (q)', description: 'q = a(1−e), must be ≤ 1.3 au', unit: 'au', placeholder: '0.746' },
    { key: 'aphelion_distance_au', label: 'Aphelion distance (Q)', description: 'Q = a(1+e)', unit: 'au', placeholder: '1.10' },
    { key: 'ascending_node_deg', label: 'Ascending node (Ω)', description: 'Longitude of ascending node, 0–360°', unit: 'deg', placeholder: '203.9' },
    { key: 'argument_of_perihelion_deg', label: 'Arg. of perihelion (ω)', description: 'Argument of perihelion, 0–360°', unit: 'deg', placeholder: '126.7' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-heading text-white">Prediction</h1>
        <p className="text-body text-muted mt-1">
          Classify a near-Earth object as Potentially Hazardous using 7 orbital elements.
          Only accepts objects with perihelion q ≤ 1.3 au (near-Earth scope).
        </p>
      </div>

      {/* Scientific framing */}
      <div className="flex gap-3 bg-yellow-500/10 border border-yellow-500/20 rounded-card px-4 py-3">
        <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-yellow-300">
          <strong>All models are Experimental.</strong>{' '}
          This is a statistical estimate from orbital elements only — not JPL's PHA designation and not an impact assessment.
          The best model (validation PR-AUC ≈ 0.18) has recall ≈ 0.39 on the test set: it misses most PHAs.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Form */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <h2 className="text-subheading text-white mb-4 flex items-center gap-2">
              <Crosshair className="w-4 h-4 text-accent" />
              Orbital Elements
            </h2>
            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              {formFields.map(f => (
                <FieldInput
                  key={f.key}
                  id={f.key}
                  label={f.label}
                  description={f.description}
                  value={fields[f.key]}
                  onChange={v => setField(f.key, v)}
                  error={fieldErrors[f.key]}
                  placeholder={f.placeholder}
                  unit={f.unit}
                />
              ))}

              {/* Model selector */}
              <div>
                <label htmlFor="model_version" className="block text-sm font-medium text-white/80 mb-1">
                  Model version
                </label>
                <p className="text-caption text-muted mb-1">Leave blank to use the best available model.</p>
                <select
                  id="model_version"
                  value={modelVersion}
                  onChange={e => setModelVersion(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent/60 transition-colors"
                >
                  <option value="">Best available (auto)</option>
                  {(models.data?.models ?? [])
                    .filter(m => m.status !== 'deprecated')
                    .map(m => (
                      <option key={m.version} value={m.version}>
                        {m.name} ({m.status})
                      </option>
                    ))}
                </select>
              </div>

              {/* Generic error (non-422, non-field-level) */}
              {error && !is422 && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                  <p className="text-sm text-red-400">
                    {error instanceof ApiRequestError ? error.message : 'Prediction failed.'}
                  </p>
                </div>
              )}

              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={mutation.isPending}
                className="w-full"
              >
                Classify
              </Button>
            </form>
          </Card>
        </div>

        {/* Result */}
        <div className="lg:col-span-3">
          {mutation.isPending && (
            <Card className="p-8 text-center">
              <div className="flex flex-col items-center gap-3">
                <Crosshair className="w-8 h-8 text-accent animate-pulse" />
                <p className="text-body text-muted">Running classification…</p>
                <p className="text-caption text-muted">First prediction may take ~1.5s to load the model</p>
              </div>
            </Card>
          )}
          {mutation.isSuccess && mutation.data && (
            <PredictionResult result={mutation.data} />
          )}
          {!mutation.isPending && !mutation.isSuccess && (
            <Card className="p-8 text-center">
              <Crosshair className="w-10 h-10 text-muted mx-auto mb-3 opacity-30" />
              <p className="text-body text-muted">Enter orbital elements and click Classify.</p>
              <p className="text-caption text-muted mt-2">
                You can navigate from a NEO detail page to pre-fill the form.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
