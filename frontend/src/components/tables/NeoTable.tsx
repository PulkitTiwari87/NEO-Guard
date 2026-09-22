import { Link } from 'react-router-dom';
import { ChevronUp, ChevronDown, ChevronsUpDown, ExternalLink } from 'lucide-react';
import { HazardBadge, OrbitClassBadge } from '../common/Badge';
import { fmtKm, fmt } from '../../utils/format';
import type { NeoSummary, NeoSortField } from '../../types/api';

const SORTABLE_FIELDS: { key: string; label: string }[] = [
  { key: 'designation', label: 'Object' },
  { key: 'absolute_magnitude_h', label: 'H (mag)' },
  { key: 'diameter_km', label: 'Diameter' },
  { key: '', label: 'Orbit' },
  { key: '', label: 'Hazard' },
];

interface NeoTableProps {
  neos: NeoSummary[];
  sort: NeoSortField;
  onSort: (field: NeoSortField) => void;
}

function SortIcon({ field, currentSort }: { field: string; currentSort: NeoSortField }) {
  const isAsc = currentSort === field;
  const isDesc = currentSort === `-${field}`;
  if (isAsc) return <ChevronUp className="w-3 h-3 text-accent" />;
  if (isDesc) return <ChevronDown className="w-3 h-3 text-accent" />;
  return <ChevronsUpDown className="w-3 h-3 text-muted" />;
}

export function NeoTable({ neos, sort, onSort }: NeoTableProps) {
  function handleSort(field: string) {
    if (!field) return;
    const typedField = field as NeoSortField;
    if (sort === typedField) {
      onSort(`-${typedField}` as NeoSortField);
    } else {
      onSort(typedField);
    }
  }

  return (
    <div className="overflow-x-auto rounded-card border border-border">
      <table className="w-full text-sm" aria-label="Near-Earth Objects">
        <thead>
          <tr className="border-b border-border bg-surface-raised">
            {SORTABLE_FIELDS.map(({ key, label }) => (
              <th
                key={label}
                className={`
                  px-4 py-3 text-left text-label uppercase tracking-widest text-muted font-medium
                  ${key ? 'cursor-pointer hover:text-white transition-colors select-none' : ''}
                `}
                onClick={() => key && handleSort(key)}
                aria-sort={
                  sort === key ? 'ascending'
                  : sort === `-${key}` ? 'descending'
                  : key ? 'none' : undefined
                }
              >
                <span className="flex items-center gap-1">
                  {label}
                  {key && <SortIcon field={key} currentSort={sort} />}
                </span>
              </th>
            ))}
            <th className="px-4 py-3 text-left text-label uppercase tracking-widest text-muted font-medium">
              Detail
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {neos.map(neo => (
            <tr
              key={neo.id}
              className="hover:bg-white/3 transition-colors"
            >
              <td className="px-4 py-3">
                <div>
                  <p className="font-medium text-white">{neo.designation}</p>
                  {neo.name && (
                    <p className="text-caption text-muted">{neo.name}</p>
                  )}
                  <p className="text-[11px] text-muted-subtle font-mono truncate max-w-[200px]">{neo.full_name}</p>
                </div>
              </td>
              <td className="px-4 py-3 font-mono text-white/80">
                {neo.absolute_magnitude_h !== null ? neo.absolute_magnitude_h.toFixed(2) : '—'}
              </td>
              <td className="px-4 py-3 font-mono text-white/80">
                {fmtKm(neo.diameter_km, 3)}
              </td>
              <td className="px-4 py-3">
                <OrbitClassBadge orbitClass={neo.orbit_class} />
              </td>
              <td className="px-4 py-3">
                <HazardBadge value={neo.is_potentially_hazardous} />
              </td>
              <td className="px-4 py-3">
                <Link
                  to={`/neos/${neo.id}`}
                  className="inline-flex items-center gap-1 text-accent hover:text-accent-hover transition-colors text-xs font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded"
                  aria-label={`View details for ${neo.full_name}`}
                >
                  View
                  <ExternalLink className="w-3 h-3" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Pagination ───────────────────────────────────────────────────────────────

interface PaginationProps {
  page: number;
  perPage: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, perPage, total, onPageChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const from = Math.min((page - 1) * perPage + 1, total);
  const to = Math.min(page * perPage, total);

  return (
    <div className="flex items-center justify-between text-sm text-muted">
      <span>
        {total > 0 ? `${fmt(from)}–${fmt(to)} of ${fmt(total)} objects` : 'No results'}
      </span>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1.5 rounded-lg border border-border text-white/70 hover:text-white hover:border-border-strong disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs font-medium focus-visible:ring-2 focus-visible:ring-accent"
          aria-label="Previous page"
        >
          ← Prev
        </button>
        <span className="px-2 text-xs">
          Page {page} of {totalPages}
        </span>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1.5 rounded-lg border border-border text-white/70 hover:text-white hover:border-border-strong disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs font-medium focus-visible:ring-2 focus-visible:ring-accent"
          aria-label="Next page"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
