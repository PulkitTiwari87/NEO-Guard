import { useState, type FormEvent } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Radar, Search, Menu, X } from 'lucide-react';
import { useHealth } from '../../hooks/useApi';
import { navItems } from './navItems';

/** Sticky command-console top bar: brand, real global search, nav, and a real health status pill. */
export function CommandHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const health = useHealth();

  function submitSearch(e: FormEvent) {
    e.preventDefault();
    const q = query.trim();
    navigate(q ? `/neos?q=${encodeURIComponent(q)}` : '/neos');
  }

  const statusOk = health.data?.status === 'ok';
  const statusLabel = health.isLoading ? 'CHECKING…' : statusOk ? 'OPERATIONAL' : 'DEGRADED';

  return (
    <header className="flex justify-between items-center w-full px-4 lg:px-6 h-14 z-50 sticky top-0 bg-surface/85 backdrop-blur-md border-b border-border">
      <div className="flex items-center gap-4 lg:gap-6 min-w-0">
        <NavLink to="/" className="flex items-center gap-2 shrink-0">
          <Radar className="w-5 h-5 text-accent" aria-hidden />
          <span className="hidden sm:inline text-xs font-mono font-bold tracking-widest text-accent uppercase">
            NEO-GUARD // ORBITAL DEFENSE
          </span>
        </NavLink>
        <form onSubmit={submitSearch} className="hidden lg:flex items-center bg-surface-raised border border-border px-2.5 py-1 rounded gap-2 text-muted focus-within:border-accent transition-colors">
          <Search className="w-3.5 h-3.5 shrink-0" aria-hidden />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="bg-transparent border-none text-xs font-mono text-white focus:ring-0 placeholder:text-muted p-0 w-56 uppercase tracking-wider"
            placeholder="Search NEO designation…"
            type="search"
            aria-label="Search near-Earth objects"
          />
        </form>
      </div>

      <nav className="hidden xl:flex items-center gap-5" aria-label="Primary navigation">
        {navItems.map(({ to, label, exact }) => {
          const isActive = exact ? location.pathname === to : location.pathname.startsWith(to);
          return (
            <NavLink
              key={to}
              to={to}
              className={`pb-1 text-[11px] font-mono font-semibold uppercase tracking-wider border-b-2 transition-colors ${
                isActive ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-white'
              }`}
              aria-current={isActive ? 'page' : undefined}
            >
              {label}
            </NavLink>
          );
        })}
      </nav>

      <div className="flex items-center gap-3">
        <div
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded border border-border text-[10px] font-mono uppercase tracking-wider"
          title="Live backend health check"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${statusOk ? 'bg-accent animate-pulse' : 'bg-hazard'}`} />
          <span className={statusOk ? 'text-accent' : 'text-hazard'}>{statusLabel}</span>
        </div>
        <button
          onClick={() => setMobileOpen(o => !o)}
          className="xl:hidden p-1.5 rounded text-muted hover:text-white transition-colors"
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileOpen}
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="fixed inset-0 top-14 z-40 bg-canvas/90 backdrop-blur-sm xl:hidden" onClick={() => setMobileOpen(false)}>
          <nav
            className="bg-surface border-b border-border py-3 px-4 space-y-1"
            onClick={e => e.stopPropagation()}
            aria-label="Mobile navigation"
          >
            <form onSubmit={submitSearch} className="flex items-center bg-surface-raised border border-border px-2.5 py-2 rounded gap-2 text-muted mb-2">
              <Search className="w-4 h-4 shrink-0" aria-hidden />
              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                className="bg-transparent border-none text-sm text-white focus:ring-0 placeholder:text-muted p-0 w-full"
                placeholder="Search NEO designation…"
                type="search"
              />
            </form>
            {navItems.map(({ to, label, icon: Icon, exact }) => {
              const isActive = exact ? location.pathname === to : location.pathname.startsWith(to);
              return (
                <NavLink
                  key={to}
                  to={to}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded text-sm font-medium transition-colors ${
                    isActive ? 'bg-accent-dim text-accent border border-accent/30' : 'text-muted hover:text-white hover:bg-white/5 border border-transparent'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </NavLink>
              );
            })}
          </nav>
        </div>
      )}
    </header>
  );
}
