import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { CommandHeader } from './CommandHeader';
import { useHealth } from '../../hooks/useApi';
import { BackendOfflineBanner } from '../common/EmptyState';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { data: health } = useHealth();
  const degraded = health?.status === 'degraded';

  return (
    <div className="flex flex-col h-screen bg-canvas overflow-hidden">
      <CommandHeader />
      <div className="flex flex-1 min-h-0">
        {/* Desktop sidebar */}
        <div className="hidden md:flex flex-shrink-0">
          <Sidebar />
        </div>

        {/* Main area */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          {/* Degraded banner */}
          {degraded && (
            <div className="px-4 md:px-6 pt-4 flex-shrink-0">
              <BackendOfflineBanner />
            </div>
          )}

          {/* Page content */}
          <main
            id="main-content"
            className="flex-1 overflow-y-auto"
            tabIndex={-1}
          >
            <div className="px-4 md:px-6 py-6 max-w-screen-2xl mx-auto animate-fade-in">
              {children}
            </div>
          </main>

          {/* Footer */}
          <footer className="flex-shrink-0 border-t border-border px-4 md:px-6 py-3">
            <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted">
              <span>NEO-Guard — Near-Earth Object Intelligence</span>
              <span>
                Data: NASA/JPL SBDB &amp; CAD APIs ·{' '}
                <a href="/about" className="hover:text-white transition-colors underline underline-offset-2">
                  Methodology &amp; Limitations
                </a>
              </span>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}
