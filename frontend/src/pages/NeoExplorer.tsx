import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { useNeos } from '../hooks/useApi';
import { NeoTable, Pagination } from '../components/tables/NeoTable';
import { PageSpinner } from '../components/common/Spinner';
import { EmptyState, ErrorState } from '../components/common/EmptyState';
import { ApiRequestError } from '../services/api/client';
import type { NeoSortField } from '../types/api';

type HazardFilter = 'all' | 'true' | 'false';

export function NeoExplorer() {
  const [searchParams] = useSearchParams();
  const initialSearch = searchParams.get('q') ?? '';
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState(initialSearch);
  const [debouncedSearch, setDebouncedSearch] = useState(initialSearch);
  const [hazardFilter, setHazardFilter] = useState<HazardFilter>('all');
  const [sort, setSort] = useState<NeoSortField>('id');

  // Simple debounce
  const handleSearchChange = useCallback((val: string) => {
    setSearch(val);
    clearTimeout((window as typeof window & { _neoSearchTimer: ReturnType<typeof setTimeout> })._neoSearchTimer);
    (window as typeof window & { _neoSearchTimer: ReturnType<typeof setTimeout> })._neoSearchTimer = setTimeout(() => {
      setDebouncedSearch(val);
      setPage(1);
    }, 350);
  }, []);

  const isHazardous = hazardFilter === 'all' ? undefined : hazardFilter === 'true';

  const { data, isLoading, error, refetch } = useNeos({
    page,
    per_page: 25,
    search: debouncedSearch || undefined,
    is_hazardous: isHazardous,
    sort,
  });

  function handleSort(newSort: NeoSortField) {
    setSort(newSort);
    setPage(1);
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-heading text-white">NEO Explorer</h1>
        <p className="text-body text-muted mt-1">
          Browse, search, and filter {data ? data.total.toLocaleString() : '…'} near-Earth objects from NASA/JPL SBDB.
        </p>
      </div>

      {/* Search and filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input
            type="search"
            placeholder="Search designation, name…"
            value={search}
            onChange={e => handleSearchChange(e.target.value)}
            maxLength={100}
            className="w-full bg-surface border border-border rounded-xl pl-9 pr-9 py-2.5 text-sm text-white placeholder:text-muted focus:outline-none focus:border-accent/60 transition-colors"
            aria-label="Search NEOs"
          />
          {search && (
            <button
              onClick={() => { setSearch(''); setDebouncedSearch(''); setPage(1); }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-white"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Hazard filter */}
        <div className="flex items-center gap-1 bg-surface border border-border rounded-xl p-1" role="group" aria-label="Hazard filter">
          <SlidersHorizontal className="w-4 h-4 text-muted mx-2" />
          {(['all', 'true', 'false'] as HazardFilter[]).map(f => (
            <button
              key={f}
              onClick={() => { setHazardFilter(f); setPage(1); }}
              className={`
                px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                ${hazardFilter === f
                  ? 'bg-accent/10 text-accent border border-accent/30'
                  : 'text-muted hover:text-white'
                }
              `}
              aria-pressed={hazardFilter === f}
            >
              {f === 'all' ? 'All' : f === 'true' ? 'PHA' : 'Non-PHA'}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {error ? (
        <ErrorState
          message={error instanceof ApiRequestError ? error.message : 'Unable to load NEO data.'}
          onRetry={() => refetch()}
        />
      ) : isLoading ? (
        <PageSpinner />
      ) : data?.items.length === 0 ? (
        <EmptyState
          title="No NEOs found"
          description={debouncedSearch ? `No results for "${debouncedSearch}". Try a different search term.` : 'No objects match your current filters.'}
          icon={<Search className="w-6 h-6" />}
        />
      ) : data ? (
        <>
          <NeoTable neos={data.items} sort={sort} onSort={handleSort} />
          <Pagination
            page={data.page}
            perPage={data.per_page}
            total={data.total}
            onPageChange={setPage}
          />
        </>
      ) : null}
    </div>
  );
}
