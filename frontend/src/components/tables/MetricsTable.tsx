import type { ConfusionMatrix, Metrics } from '../../types/api';
import { fmtPct } from '../../utils/format';

interface ConfusionMatrixProps {
  cm: ConfusionMatrix;
}

export function ConfusionMatrixDisplay({ cm }: ConfusionMatrixProps) {
  const total = cm.tn + cm.fp + cm.fn + cm.tp;
  return (
    <div>
      <p className="text-caption text-muted mb-3 uppercase tracking-wider">Confusion Matrix</p>
      <div className="grid grid-cols-3 gap-1 text-xs text-center max-w-xs">
        {/* Header row */}
        <div />
        <div className="py-1 text-muted font-medium">Pred: Not PHA</div>
        <div className="py-1 text-safe font-medium">Pred: PHA</div>
        {/* Row 1 */}
        <div className="py-2 text-muted font-medium text-right pr-2 flex items-center justify-end">Actual: Not PHA</div>
        <div className="bg-safe/10 border border-safe/20 rounded py-2 px-2">
          <p className="font-bold text-safe text-base">{cm.tn.toLocaleString()}</p>
          <p className="text-muted text-[10px]">TN · {fmtPct(cm.tn / total)}</p>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 rounded py-2 px-2">
          <p className="font-bold text-red-400 text-base">{cm.fp.toLocaleString()}</p>
          <p className="text-muted text-[10px]">FP · {fmtPct(cm.fp / total)}</p>
        </div>
        {/* Row 2 */}
        <div className="py-2 text-hazard font-medium text-right pr-2 flex items-center justify-end">Actual: PHA</div>
        <div className="bg-red-500/10 border border-red-500/20 rounded py-2 px-2">
          <p className="font-bold text-red-400 text-base">{cm.fn.toLocaleString()}</p>
          <p className="text-muted text-[10px]">FN · {fmtPct(cm.fn / total)}</p>
        </div>
        <div className="bg-safe/10 border border-safe/20 rounded py-2 px-2">
          <p className="font-bold text-safe text-base">{cm.tp.toLocaleString()}</p>
          <p className="text-muted text-[10px]">TP · {fmtPct(cm.tp / total)}</p>
        </div>
      </div>
    </div>
  );
}

interface MetricsTableProps {
  metrics: Metrics;
  label: string;
}

export function MetricsTable({ metrics, label }: MetricsTableProps) {
  const rows = [
    { name: 'n', value: metrics.n.toLocaleString(), note: 'total samples' },
    { name: 'Positives (PHA)', value: metrics.n_positive.toLocaleString(), note: `${fmtPct(metrics.prevalence)} prevalence` },
    { name: 'Accuracy', value: fmtPct(metrics.accuracy) },
    { name: 'Precision', value: fmtPct(metrics.precision) },
    { name: 'Recall', value: fmtPct(metrics.recall) },
    { name: 'F1', value: fmtPct(metrics.f1) },
    { name: 'ROC-AUC', value: metrics.roc_auc !== null ? metrics.roc_auc.toFixed(4) : '—' },
    { name: 'PR-AUC', value: metrics.pr_auc !== null ? metrics.pr_auc.toFixed(4) : '—' },
    { name: 'Threshold', value: metrics.threshold.toFixed(4) },
  ];

  return (
    <div>
      <p className="text-caption text-muted mb-3 uppercase tracking-wider">{label}</p>
      <div className="space-y-1">
        {rows.map(row => (
          <div key={row.name} className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
            <span className="text-sm text-muted">{row.name}</span>
            <div className="text-right">
              <span className="text-sm font-mono text-white">{row.value}</span>
              {row.note && <p className="text-[10px] text-muted">{row.note}</p>}
            </div>
          </div>
        ))}
        {metrics.bootstrap_ci && (
          <div className="pt-2">
            <p className="text-[10px] text-muted uppercase tracking-wider mb-1">
              95% CI (bootstrap, n={metrics.bootstrap_ci.n_resamples.toLocaleString()})
            </p>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-surface-raised rounded p-2">
                <p className="text-[10px] text-muted">ROC-AUC</p>
                <p className="text-xs font-mono text-white">
                  [{metrics.bootstrap_ci.roc_auc[0].toFixed(3)}, {metrics.bootstrap_ci.roc_auc[1].toFixed(3)}]
                </p>
              </div>
              <div className="bg-surface-raised rounded p-2">
                <p className="text-[10px] text-muted">PR-AUC</p>
                <p className="text-xs font-mono text-white">
                  [{metrics.bootstrap_ci.pr_auc[0].toFixed(3)}, {metrics.bootstrap_ci.pr_auc[1].toFixed(3)}]
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
