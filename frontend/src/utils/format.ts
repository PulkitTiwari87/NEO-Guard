/**
 * Formatting utilities for NEO data display.
 * All units are labeled to avoid ambiguity.
 */

/** Format a number to a given number of significant figures, gracefully handling null */
export function fmt(
  value: number | null | undefined,
  options: Intl.NumberFormatOptions = {},
): string {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('en-US', options).format(value);
}

export function fmtAu(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${value.toPrecision(4)} au`;
}

export function fmtKm(value: number | null | undefined, decimals = 0): string {
  if (value === null || value === undefined) return '—';
  return `${fmt(value, { maximumFractionDigits: decimals })} km`;
}

export function fmtKmS(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${value.toFixed(3)} km/s`;
}

export function fmtDeg(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${value.toFixed(4)}°`;
}

export function fmtDays(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${fmt(value, { maximumFractionDigits: 1 })} d`;
}

export function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

export function fmtCount(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return fmt(value, { maximumFractionDigits: 0 });
}

/**
 * Format an approach date that is in TDB (not UTC).
 * We display it with a TDB label per the frontend contract.
 */
export function fmtApproachDate(isoStr: string): string {
  // date is timezone-naive ISO-8601 from the backend (no 'Z')
  const raw = isoStr.replace('T', ' ').replace(/:\d+$/, '');
  return `${raw} TDB`;
}

export function fmtDate(isoStr: string | null | undefined): string {
  if (!isoStr) return '—';
  return isoStr.slice(0, 10);
}

export function fmtDateTime(isoStr: string | null | undefined): string {
  if (!isoStr) return '—';
  return isoStr.replace('T', ' ').slice(0, 16) + ' UTC';
}

/**
 * Rough "time until" a stored approach date (TDB, treated as UTC — see
 * docs/API_CONTRACT.md). Precision is days/hours, so the sub-two-minute
 * TDB/UTC offset is immaterial; not a fabricated countdown, just arithmetic
 * on the real stored timestamp.
 */
export function fmtTimeUntil(isoStr: string): string {
  const targetMs = Date.parse(isoStr.endsWith('Z') ? isoStr : `${isoStr}Z`);
  const diffMs = targetMs - Date.now();
  if (Number.isNaN(diffMs)) return '—';
  const past = diffMs < 0;
  const abs = Math.abs(diffMs);
  const days = Math.floor(abs / 86_400_000);
  const hours = Math.floor((abs % 86_400_000) / 3_600_000);
  const label = days > 0 ? `${days}D ${hours}H` : `${hours}H`;
  return past ? `T+${label}` : `T-${label}`;
}

/** Orbit class full name */
const ORBIT_CLASS_NAMES: Record<string, string> = {
  APO: 'Apollo',
  AMO: 'Amor',
  ATE: 'Aten',
  IEO: 'Atira (IEO)',
};
export function orbitClassName(code: string): string {
  return ORBIT_CLASS_NAMES[code] ?? code;
}

/** Display name: full_name preferred, fall back to designation */
export function neoDisplayName(neo: { name: string | null; full_name: string; designation: string }): string {
  return neo.full_name || neo.designation;
}

/** Hazard status label */
export function hazardLabel(value: boolean | null): string {
  if (value === null) return 'Unknown';
  return value ? 'Potentially Hazardous' : 'Non-Hazardous';
}

export function modelStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    experimental: 'Experimental',
    validated: 'Validated',
    production: 'Production',
    deprecated: 'Deprecated',
  };
  return labels[status] ?? status;
}

/** Humanise a SHAP feature name */
export function humanFeatureName(name: string): string {
  const map: Record<string, string> = {
    semi_major_axis_au: 'Semi-major axis (a)',
    eccentricity: 'Eccentricity (e)',
    inclination_deg: 'Inclination (i)',
    perihelion_distance_au: 'Perihelion distance (q)',
    aphelion_distance_au: 'Aphelion distance (Q)',
    ascending_node_deg: 'Ascending node (Ω)',
    argument_of_perihelion_deg: 'Arg. of perihelion (ω)',
    argument_of_perihelion_sin: 'sin(ω)',
    argument_of_perihelion_cos: 'cos(ω)',
    ascending_node_sin: 'sin(Ω)',
    ascending_node_cos: 'cos(Ω)',
  };
  return map[name] ?? name;
}
