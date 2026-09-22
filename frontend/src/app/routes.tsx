import { Routes, Route } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { Dashboard } from '../pages/Dashboard';
import { NeoExplorer } from '../pages/NeoExplorer';
import { NeoDetail } from '../pages/NeoDetail';
import { Analytics } from '../pages/Analytics';
import { Models } from '../pages/Models';
import { Prediction } from '../pages/Prediction';
import { About } from '../pages/About';
import { EmptyState } from '../components/common/EmptyState';
import { AlertTriangle } from 'lucide-react';

function NotFound() {
  return (
    <EmptyState
      title="Page not found"
      description="The page you are looking for does not exist."
      icon={<AlertTriangle className="w-6 h-6" />}
    />
  );
}

export function AppRoutes() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/neos" element={<NeoExplorer />} />
        <Route path="/neos/:id" element={<NeoDetail />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/models" element={<Models />} />
        <Route path="/predict" element={<Prediction />} />
        <Route path="/about" element={<About />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppShell>
  );
}
