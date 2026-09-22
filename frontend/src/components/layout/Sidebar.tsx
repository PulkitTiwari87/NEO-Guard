import { NavLink, useLocation } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Globe, ExternalLink } from 'lucide-react';
import { useState } from 'react';
import { useHealth, useModels } from '../../hooks/useApi';
import { BASE_URL } from '../../services/api/client';
import { navItems } from './navItems';

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const health = useHealth();
  const models = useModels();

  const statusOk = health.data?.status === 'ok';
  const datasetVersion = models.data?.models[0]?.dataset_version;

  return (
    <aside
      className={`
        relative flex flex-col bg-surface border-r border-border transition-all duration-300 ease-in-out
        ${collapsed ? 'w-16' : 'w-64'}
      `}
    >
      {/* Rail header — real system status, not a fabricated DEFCON level */}
      <div className={`flex items-center gap-2.5 px-4 py-5 border-b border-border ${collapsed ? 'justify-center' : ''}`}>
        <div className="w-8 h-8 flex-shrink-0 bg-surface-raised border border-accent/30 rounded flex items-center justify-center">
          <Globe className="w-4 h-4 text-accent" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="text-sm font-bold text-white tracking-tight font-mono">NEO-GUARD</p>
            <p className="text-[10px] font-mono tracking-wider flex items-center gap-1 truncate">
              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${statusOk ? 'bg-accent animate-pulse' : 'bg-hazard'}`} />
              <span className={statusOk ? 'text-accent' : 'text-hazard'}>
                {health.isLoading ? 'CHECKING…' : statusOk ? 'SYSTEM OPERATIONAL' : 'SYSTEM DEGRADED'}
              </span>
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-2" aria-label="Main navigation">
        {navItems.map(({ to, label, icon: Icon, exact }) => {
          const isActive = exact
            ? location.pathname === to
            : location.pathname.startsWith(to);
          return (
            <NavLink
              key={to}
              to={to}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded text-sm font-mono font-medium transition-all duration-150
                focus:outline-none focus-visible:ring-2 focus-visible:ring-accent
                ${isActive
                  ? 'bg-surface-high text-accent border-l-2 border-accent'
                  : 'text-muted hover:text-white hover:bg-white/5 border-l-2 border-transparent'
                }
                ${collapsed ? 'justify-center' : ''}
              `}
              title={collapsed ? label : undefined}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Rail footer — real dataset version and API docs link, no fabricated uplink stats */}
      <div className="pt-3 border-t border-border px-2 pb-2 space-y-1">
        {!collapsed && datasetVersion && (
          <div className="px-3 py-2 text-[10px] font-mono text-muted truncate" title={datasetVersion}>
            DATASET: <span className="text-white/70">{datasetVersion}</span>
          </div>
        )}
        <a
          href={`${BASE_URL}/openapi.json`}
          target="_blank"
          rel="noreferrer"
          className={`flex items-center gap-3 px-3 py-2 rounded text-muted hover:text-white font-mono text-xs transition-colors ${collapsed ? 'justify-center' : ''}`}
          title="API schema"
        >
          <ExternalLink className="w-4 h-4 flex-shrink-0" />
          {!collapsed && <span>API Schema</span>}
        </a>
        <button
          onClick={() => setCollapsed(c => !c)}
          className="flex items-center justify-center w-full p-2 rounded text-muted hover:text-white hover:bg-white/5 transition-colors"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : (
            <span className="flex items-center gap-2 text-xs">
              <ChevronLeft className="w-4 h-4" />
              Collapse
            </span>
          )}
        </button>
      </div>
    </aside>
  );
}
