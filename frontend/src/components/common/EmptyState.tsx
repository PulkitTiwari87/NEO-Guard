import { AlertTriangle, RefreshCw, Database, Wifi } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      {icon && (
        <div className="mb-4 p-4 bg-white/5 rounded border border-border text-muted">
          {icon}
        </div>
      )}
      <h3 className="text-subheading text-white/80 mb-2">{title}</h3>
      {description && <p className="text-body text-muted max-w-md">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  is503?: boolean;
}

export function ErrorState({ title = 'Unable to load data', message, onRetry, is503 }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="mb-4 p-4 bg-red-500/10 rounded border border-red-500/20 text-red-400">
        {is503 ? <Database className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
      </div>
      <h3 className="text-subheading text-white/80 mb-2">{title}</h3>
      <p className="text-body text-muted max-w-md mb-6">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 bg-surface-raised border border-border rounded text-white/80 text-sm font-medium hover:border-border-strong hover:text-white transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      )}
    </div>
  );
}

export function BackendOfflineBanner() {
  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm">
      <Wifi className="w-4 h-4 flex-shrink-0" />
      <span>
        <strong>Database unavailable.</strong> The backend is running but the database is unreachable.
        Data may be stale or unavailable.
      </span>
    </div>
  );
}
