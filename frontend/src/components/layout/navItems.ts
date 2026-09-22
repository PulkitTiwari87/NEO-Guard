import {
  Satellite, Orbit, TriangleAlert, Cpu, Crosshair, Info,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  exact?: boolean;
}

/**
 * Command-console navigation, mapped to the app's real routes.
 * Labels lean into the Stitch "planetary defense command" aesthetic without
 * claiming capabilities the backend doesn't have (Phase 3.5 rule: no fake data/features).
 */
export const navItems: NavItem[] = [
  { to: '/', label: 'Live Observation', icon: Satellite, exact: true },
  { to: '/neos', label: 'Orbital Trajectories', icon: Orbit },
  { to: '/analytics', label: 'Hazard Index', icon: TriangleAlert },
  { to: '/models', label: 'Model Registry', icon: Cpu },
  { to: '/predict', label: 'Prediction', icon: Crosshair },
  { to: '/about', label: 'Data Provenance', icon: Info },
];
