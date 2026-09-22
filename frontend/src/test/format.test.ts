import { describe, it, expect } from 'vitest';
import {
  fmt,
  fmtKm,
  fmtAu,
  fmtKmS,
  fmtDeg,
  fmtDays,
  fmtPct,
  fmtApproachDate,
  orbitClassName,
  hazardLabel,
  neoDisplayName,
  humanFeatureName,
} from '../utils/format';

describe('fmt', () => {
  it('formats numbers', () => {
    expect(fmt(42477)).toBe('42,477');
    expect(fmt(null)).toBe('—');
    expect(fmt(undefined)).toBe('—');
  });
});

describe('fmtKm', () => {
  it('formats km with units', () => {
    expect(fmtKm(4.9, 1)).toBe('4.9 km');
    expect(fmtKm(null)).toBe('—');
  });
});

describe('fmtAu', () => {
  it('formats au values', () => {
    expect(fmtAu(0.9223592206975018)).toMatch(/au$/);
    expect(fmtAu(null)).toBe('—');
  });
});

describe('fmtKmS', () => {
  it('formats velocity', () => {
    expect(fmtKmS(7.42)).toBe('7.420 km/s');
    expect(fmtKmS(null)).toBe('—');
  });
});

describe('fmtDeg', () => {
  it('formats degrees', () => {
    expect(fmtDeg(3.34)).toMatch(/°$/);
    expect(fmtDeg(null)).toBe('—');
  });
});

describe('fmtDays', () => {
  it('formats day counts', () => {
    expect(fmtDays(323.5)).toBe('323.5 d');
    expect(fmtDays(null)).toBe('—');
  });
});

describe('fmtPct', () => {
  it('formats fractions as percentages', () => {
    expect(fmtPct(0.118)).toBe('11.8%');
    expect(fmtPct(null)).toBe('—');
  });
});

describe('fmtApproachDate', () => {
  it('appends TDB to approach dates', () => {
    const result = fmtApproachDate('2029-04-13T21:46:00');
    expect(result).toContain('TDB');
    expect(result).toContain('2029-04-13');
  });
});

describe('orbitClassName', () => {
  it('returns full names for known codes', () => {
    expect(orbitClassName('APO')).toBe('Apollo');
    expect(orbitClassName('AMO')).toBe('Amor');
    expect(orbitClassName('ATE')).toBe('Aten');
    expect(orbitClassName('IEO')).toContain('Atira');
  });
  it('returns the code for unknown classes', () => {
    expect(orbitClassName('XYZ')).toBe('XYZ');
  });
});

describe('hazardLabel', () => {
  it('returns correct labels', () => {
    expect(hazardLabel(true)).toBe('Potentially Hazardous');
    expect(hazardLabel(false)).toBe('Non-Hazardous');
    expect(hazardLabel(null)).toBe('Unknown');
  });
});

describe('neoDisplayName', () => {
  it('prefers full_name', () => {
    expect(neoDisplayName({ name: 'Apophis', full_name: '99942 Apophis', designation: '99942' })).toBe('99942 Apophis');
  });
  it('falls back to designation', () => {
    expect(neoDisplayName({ name: null, full_name: '', designation: '12345' })).toBe('12345');
  });
});

describe('humanFeatureName', () => {
  it('maps known feature names', () => {
    expect(humanFeatureName('eccentricity')).toBe('Eccentricity (e)');
    expect(humanFeatureName('semi_major_axis_au')).toBe('Semi-major axis (a)');
  });
  it('returns the raw name for unknown features', () => {
    expect(humanFeatureName('unknown_feature')).toBe('unknown_feature');
  });
});
