import { Link } from 'react-router-dom';
import { Globe, AlertTriangle, Activity, Cpu, ArrowRight, Database, TrendingUp } from 'lucide-react';
import { useAnalytics, useHealth, useModels } from '../hooks/useApi';
import { MetricCard, Card } from '../components/common/Card';
import { SkeletonCard, Skeleton } from '../components/common/Spinner';
import { ErrorState } from '../components/common/EmptyState';
import { OrbitClassChart, ApproachesByYearChart } from '../components/charts/Charts';
import { HudPanel } from '../components/dashboard/HudPanel';
import { OrbitalRadar } from '../components/dashboard/OrbitalRadar';
import { CloseApproachMatrix } from '../components/dashboard/CloseApproachMatrix';
import { DataSourcesPanel } from '../components/dashboard/DataSourcesPanel';
import { QuickActionsPanel } from '../components/dashboard/QuickActionsPanel';
import { fmtCount, fmtDateTime } from '../utils/format';
import { StatusBadge } from '../components/common/Badge';

export function Dashboard() {
  const analytics = useAnalytics();
  const health = useHealth();
  const models = useModels();

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-label text-muted uppercase tracking-widest font-mono">
          <Globe className="w-3.5 h-3.5" />
          <span>Near-Earth Object Intelligence</span>
        </div>
        <h1 className="text-display font-heading text-white">NEO-Guard</h1>
        <p className="text-body text-muted max-w-xl">
          Explore real NASA/JPL asteroid data through explainable machine learning.
          Classification from orbital elements only — not impact prediction.
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Link
            to="/neos"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-accent text-surface rounded text-sm font-bold hover:bg-accent-hover transition-colors shadow-glow"
          >
            Explore NEOs
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/analytics"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-surface-raised text-white/80 border border-border rounded text-sm font-semibold hover:border-border-strong hover:text-white transition-all"
          >
            View Analytics
          </Link>
        </div>
      </div>

      {/* KPI HUD row */}
      {analytics.error ? (
        <ErrorState
          message="Unable to load analytics data."
          onRetry={() => analytics.refetch()}
          is503={analytics.error?.message?.includes('503') || analytics.error?.message?.includes('unavailable')}
        />
      ) : analytics.isLoading ? (
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : analytics.data ? (
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          <MetricCard
            label="Cataloged Targets"
            value={fmtCount(analytics.data.total_neos)}
            subtext="discovered near-Earth objects"
            accent="neutral"
            icon={<Globe className="w-5 h-5" />}
          />
          <MetricCard
            label="Active PHAs Tracked"
            value={fmtCount(analytics.data.hazardous_count)}
            subtext={`${analytics.data.unknown_hazard_count} with unknown flag`}
            accent="amber"
            icon={<AlertTriangle className="w-5 h-5" />}
          />
          <MetricCard
            label="Close Approaches"
            value={fmtCount(analytics.data.total_approaches)}
            subtext="Earth approaches 2000–2100"
            accent="blue"
            icon={<Activity className="w-5 h-5" />}
          />
          <MetricCard
            label="ML Models"
            value={models.data ? String(models.data.models.length) : '—'}
            subtext={models.data?.models.length ? `${models.data.models.filter(m => m.status !== 'deprecated').length} active` : 'loading'}
            accent="neutral"
            icon={<Cpu className="w-5 h-5" />}
          />
        </div>
      ) : null}

      {/* Main tactical grid */}
      {analytics.data && (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
          {/* Center/left: 8 columns */}
          <div className="xl:col-span-8 flex flex-col gap-5">
            <OrbitalRadar approaches={analytics.data.upcoming_close_approaches} />
            <HudPanel title="Close Approaches by Year" icon={<TrendingUp className="w-4 h-4" />} meta="REAL COUNTS, 2000–2100 (TDB)">
              <ApproachesByYearChart data={analytics.data.approaches_by_year} />
            </HudPanel>
            <CloseApproachMatrix approaches={analytics.data.upcoming_close_approaches} />
          </div>

          {/* Right rail: 4 columns */}
          <div className="xl:col-span-4 flex flex-col gap-5">
            <HudPanel title="Orbit Class Distribution">
              <p className="text-[10px] font-mono text-muted -mt-1">
                APO = Apollo · AMO = Amor · ATE = Aten · IEO = Atira
              </p>
              <OrbitClassChart data={analytics.data.orbit_class_counts} />
            </HudPanel>
            <DataSourcesPanel
              totalNeos={analytics.data.total_neos}
              totalApproaches={analytics.data.total_approaches}
              datasetVersion={models.data?.models[0]?.dataset_version}
            />
            <QuickActionsPanel />
          </div>
        </div>
      )}

      {/* System status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-subheading font-heading text-white mb-4">System Status</h2>
          {health.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-48" />
            </div>
          ) : health.data ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-sm text-muted flex items-center gap-2">
                  <Database className="w-4 h-4" /> API Status
                </span>
                <span className={`text-sm font-medium ${health.data.status === 'ok' ? 'text-safe' : 'text-hazard'}`}>
                  {health.data.status === 'ok' ? 'Operational' : 'Degraded'}
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-sm text-muted">Database</span>
                <span className={`text-sm font-medium ${health.data.database === 'ok' ? 'text-safe' : 'text-hazard'}`}>
                  {health.data.database === 'ok' ? 'Connected' : 'Unavailable'}
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-sm text-muted">API Version</span>
                <span className="text-sm font-mono text-white">{health.data.version}</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-sm text-muted">Last Checked</span>
                <span className="text-sm text-muted">{fmtDateTime(health.data.timestamp)}</span>
              </div>
            </div>
          ) : null}
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-subheading font-heading text-white">ML Models</h2>
            <Link to="/models" className="text-xs text-accent hover:text-accent-hover transition-colors">
              View all →
            </Link>
          </div>
          {models.isLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-10" />)}
            </div>
          ) : models.data?.models.length === 0 ? (
            <p className="text-sm text-muted">No models trained yet.</p>
          ) : (
            <div className="space-y-2">
              {(models.data?.models ?? []).slice(0, 4).map(m => (
                <div key={m.version} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <div>
                    <p className="text-sm text-white">{m.name}</p>
                    <p className="text-caption text-muted font-mono">{m.version}</p>
                  </div>
                  <div className="text-right space-y-1">
                    <StatusBadge status={m.status} />
                    {m.metrics.validation?.pr_auc !== undefined && (
                      <p className="text-[10px] text-muted">
                        Val PR-AUC: {m.metrics.validation.pr_auc?.toFixed(3) ?? '—'}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Data provenance note */}
      <div className="bg-surface-raised border border-border rounded-card px-5 py-4">
        <p className="text-caption text-muted">
          <strong className="text-white/60">Data source:</strong>{' '}
          NASA/JPL Small-Body Database (SBDB) and Close Approach Data (CAD) APIs. Single snapshot.
          Orbit data and PHA flags may change as new observations are made.
          {' '}
          <Link to="/about" className="text-accent hover:text-accent-hover underline underline-offset-2">
            Methodology &amp; limitations
          </Link>
        </p>
      </div>
    </div>
  );
}
