import { useState } from 'react';
import { ChevronDown, ChevronUp, Cpu } from 'lucide-react';
import { useModels, useModel } from '../hooks/useApi';
import { PageSpinner } from '../components/common/Spinner';
import { EmptyState, ErrorState } from '../components/common/EmptyState';
import { Card } from '../components/common/Card';
import { StatusBadge } from '../components/common/Badge';
import { MetricsTable, ConfusionMatrixDisplay } from '../components/tables/MetricsTable';
import { ApiRequestError } from '../services/api/client';
import { fmtDateTime } from '../utils/format';

function ModelDetail({ version }: { version: string }) {
  const { data, isLoading } = useModel(version);

  if (isLoading) {
    return <div className="py-4 text-sm text-muted animate-pulse">Loading model detail…</div>;
  }
  if (!data) return null;

  return (
    <div className="border-t border-border pt-6 space-y-6">
      {/* Parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <p className="text-caption text-muted uppercase tracking-wider mb-2">Model Configuration</p>
          <div className="space-y-1">
            {Object.entries(data.parameters).map(([k, v]) => (
              <div key={k} className="flex items-start justify-between py-1 border-b border-border last:border-0">
                <span className="text-sm text-muted">{k}</span>
                <span className="text-sm font-mono text-white text-right ml-4">{JSON.stringify(v)}</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="text-caption text-muted uppercase tracking-wider mb-2">Train/Val/Test Split</p>
          <div className="space-y-1">
            {Object.entries(data.split).map(([k, v]) => (
              <div key={k} className="flex items-start justify-between py-1 border-b border-border last:border-0">
                <span className="text-sm text-muted">{k}</span>
                <span className="text-sm font-mono text-white">{JSON.stringify(v)}</span>
              </div>
            ))}
          </div>
          {data.input_features && (
            <div className="mt-4">
              <p className="text-caption text-muted uppercase tracking-wider mb-2">Input Features (for /predict)</p>
              <div className="flex flex-wrap gap-1">
                {data.input_features.map(f => (
                  <span key={f} className="text-[11px] font-mono bg-surface-raised border border-border px-2 py-0.5 rounded text-white/70">
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.metrics.validation && (
          <div className="space-y-4">
            <MetricsTable metrics={data.metrics.validation} label="Validation Set" />
            <ConfusionMatrixDisplay cm={data.metrics.validation.confusion_matrix} />
          </div>
        )}
        {data.metrics.test && (
          <div className="space-y-4">
            <MetricsTable metrics={data.metrics.test} label="Test Set" />
            <ConfusionMatrixDisplay cm={data.metrics.test.confusion_matrix} />
          </div>
        )}
      </div>

      {/* Interpretation */}
      <div className="bg-surface-raised border border-border/50 rounded-lg px-4 py-3">
        <p className="text-caption text-muted">
          <strong className="text-white/60">Interpreting metrics:</strong>{' '}
          No-skill PR-AUC baseline ≈ prevalence (
          {data.metrics.test ? (data.metrics.test.prevalence * 100).toFixed(1) : '?'}% on test set).
          All six models are <strong className="text-yellow-400">experimental</strong> and have not received expert review.
          The confusion matrix (test set) shows the model misses many PHAs (high false negatives) —
          do not use these predictions for actual hazard assessment.
        </p>
      </div>
    </div>
  );
}

export function Models() {
  const { data, isLoading, error, refetch } = useModels();
  const [expandedVersion, setExpandedVersion] = useState<string | null>(null);

  if (isLoading) return <PageSpinner />;

  if (error) {
    return (
      <ErrorState
        title="Unable to load models"
        message={error instanceof ApiRequestError ? error.message : 'Model registry could not be retrieved.'}
        onRetry={() => refetch()}
      />
    );
  }

  const models = data?.models ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-heading text-white">ML Models</h1>
        <p className="text-body text-muted mt-1">
          Trained classifiers for JPL's Potentially Hazardous Asteroid (PHA) flag.
          All models predict from 7 orbital elements only.
        </p>
      </div>

      {/* Scientific framing warning */}
      <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-card px-5 py-4">
        <p className="text-sm text-yellow-300">
          <strong>All models are Experimental.</strong>{' '}
          They predict which orbits <em>can approach Earth closely</em> — not impact risk.
          The target (JPL's PHA flag) depends on H magnitude and MOID; both are excluded from model inputs
          to avoid leakage. Models have weak precision/recall and do not reproduce JPL's designation.
          Compare PR-AUC to the no-skill baseline (≈ prevalence) when evaluating model quality.
        </p>
      </div>

      {models.length === 0 ? (
        <EmptyState
          title="No models trained yet"
          description="Run the ML pipeline to train and register models."
          icon={<Cpu className="w-6 h-6" />}
        />
      ) : (
        <div className="space-y-4">
          {models.map(model => {
            const isExpanded = expandedVersion === model.version;
            const valPrAuc = model.metrics.validation?.pr_auc;
            const testPrAuc = model.metrics.test?.pr_auc;

            return (
              <Card key={model.version} className="p-6">
                {/* Model header */}
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h2 className="text-subheading text-white">{model.name}</h2>
                      <StatusBadge status={model.status} />
                    </div>
                    <p className="text-caption font-mono text-muted">{model.version}</p>
                    <div className="flex flex-wrap gap-3 text-caption text-muted mt-1">
                      <span>Algorithm: <span className="text-white/70">{model.algorithm}</span></span>
                      <span>Dataset: <span className="font-mono text-white/70">{model.dataset_version}</span></span>
                      <span>Features: <span className="font-mono text-white/70">{model.feature_version}</span></span>
                      <span>Trained: <span className="text-white/70">{fmtDateTime(model.created_at)}</span></span>
                    </div>
                  </div>
                  {/* Quick metrics */}
                  <div className="flex flex-wrap gap-3 text-right">
                    {valPrAuc !== undefined && valPrAuc !== null && (
                      <div>
                        <p className="text-[10px] text-muted uppercase tracking-wider">Val PR-AUC</p>
                        <p className="text-sm font-mono font-bold text-white">{valPrAuc.toFixed(4)}</p>
                      </div>
                    )}
                    {testPrAuc !== undefined && testPrAuc !== null && (
                      <div>
                        <p className="text-[10px] text-muted uppercase tracking-wider">Test PR-AUC</p>
                        <p className="text-sm font-mono font-bold text-white">{testPrAuc.toFixed(4)}</p>
                      </div>
                    )}
                    {model.metrics.test?.recall !== undefined && (
                      <div>
                        <p className="text-[10px] text-muted uppercase tracking-wider">Test Recall</p>
                        <p className="text-sm font-mono font-bold text-white">
                          {(model.metrics.test.recall * 100).toFixed(1)}%
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Expand toggle */}
                <button
                  onClick={() => setExpandedVersion(isExpanded ? null : model.version)}
                  className="mt-4 flex items-center gap-2 text-xs text-muted hover:text-white transition-colors"
                  aria-expanded={isExpanded}
                >
                  {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  {isExpanded ? 'Hide' : 'Show'} full metrics &amp; parameters
                </button>

                {/* Expanded detail */}
                {isExpanded && <ModelDetail version={model.version} />}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
