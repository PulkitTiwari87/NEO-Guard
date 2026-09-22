import { Link } from 'react-router-dom';
import { ExternalLink } from 'lucide-react';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-subheading text-white">{title}</h2>
      <div className="text-body text-muted space-y-2 leading-relaxed">{children}</div>
    </section>
  );
}

export function About() {
  return (
    <div className="space-y-8 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-heading text-white">About NEO-Guard</h1>
        <p className="text-body text-muted mt-1">
          Methodology, data source, scientific limitations, and technology.
        </p>
      </div>

      {/* What is NEO-Guard */}
      <Section title="What is NEO-Guard?">
        <p>
          NEO-Guard is a scientific data exploration and machine learning demonstration platform
          for Near-Earth Objects (NEOs). It displays real asteroid data from NASA/JPL and applies
          experimental ML classifiers to predict whether an object would be classified as a
          Potentially Hazardous Asteroid (PHA) based on orbital elements alone.
        </p>
        <p>
          <strong className="text-white/80">NEO-Guard is not an impact prediction or risk assessment system.</strong>{' '}
          It does not predict asteroid impacts, assign impact probabilities, or replace JPL's official
          PHA designation process. All model outputs are statistical estimates from a small set of
          orbital features.
        </p>
      </Section>

      {/* Data source */}
      <Section title="Data Source">
        <p>
          All asteroid and approach data is sourced from:
        </p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>
            <strong className="text-white/70">NASA/JPL Small-Body Database (SBDB) Query API v1.0</strong> —
            orbital elements, physical properties, and PHA flags for all known near-Earth asteroids.
          </li>
          <li>
            <strong className="text-white/70">NASA/JPL Close-Approach Data (CAD) API v1.5</strong> —
            predicted Earth close approaches (≤ 0.05 au) during 2000–2100.
          </li>
        </ul>
        <p>
          The dataset is a single snapshot (2026-09-21) containing 42,477 NEOs and 30,828 close approach
          records. JPL orbit parameters and PHA flags change as new observations are made. NEO-Guard does
          not perform live updates — re-ingestion from JPL APIs is required to refresh the data.
        </p>
        <p className="text-caption text-muted-subtle">
          All approach dates are in Barycentric Dynamical Time (TDB), not UTC. Future approaches are
          predictions with uncertainty bounds published by JPL.
        </p>
      </Section>

      {/* ML methodology */}
      <Section title="Machine Learning Methodology">
        <p>
          NEO-Guard trains binary classifiers to predict JPL's PHA flag from 7 orbital elements:
          semi-major axis (a), eccentricity (e), inclination (i), perihelion distance (q),
          aphelion distance (Q), longitude of ascending node (Ω), and argument of perihelion (ω).
        </p>
        <p>
          <strong className="text-white/80">What the models learn:</strong> JPL's PHA flag is defined
          as Earth MOID ≤ 0.05 au and H ≤ 22.0. Both MOID and H are excluded from inputs to avoid
          data leakage — the models therefore learn which <em>orbital geometries</em> can approach
          Earth closely, not the full PHA rule. This is a weaker, harder task.
        </p>
        <p>
          Six models were trained: Logistic Regression, Random Forest, and XGBoost, each with and
          without class-weight balancing. All use a chronological train/validation/test split.
          Evaluation includes held-out test metrics with bootstrap confidence intervals, and SHAP
          explanations for individual predictions.
        </p>
        <p className="text-caption text-muted">
          All models are experimental. None has received independent expert review or been promoted to
          production status. Refer to the{' '}
          <Link to="/models" className="text-accent underline underline-offset-2">Models page</Link>{' '}
          for full metrics.
        </p>
      </Section>

      {/* SHAP */}
      <Section title="SHAP Explanations">
        <p>
          SHAP (SHapley Additive exPlanations) values quantify each feature's contribution to a
          specific model output. They describe <em>how the model uses its inputs</em>, not physical
          causes. A high SHAP value for perihelion distance means the model relied heavily on that
          feature for this prediction — it does not mean perihelion distance physically causes hazard.
        </p>
      </Section>

      {/* Scientific integrity */}
      <Section title="Scientific Integrity">
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>No data is fabricated or invented. All values come from the API or display "—" when unavailable.</li>
          <li>Model outputs are clearly labeled experimental and shown with model version and threshold.</li>
          <li>The disclaimer required by the backend is displayed on every prediction result.</li>
          <li>JPL's own PHA flag is shown alongside model predictions to aid comparison.</li>
          <li>Charts and statistics are derived from real data; charts show empty states rather than fake data.</li>
          <li>The backend is the single source of truth. No production values are hardcoded in the frontend.</li>
        </ul>
      </Section>

      {/* Known limitations */}
      <Section title="Known Limitations">
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>Weak classifier: best test PR-AUC ≈ 0.15 (no-skill ≈ 0.013). Models miss most PHAs.</li>
          <li>Apophis (a well-known PHA) is predicted non-hazardous by all models.</li>
          <li>Strong distribution shift: PHA rate falls from 7.5% (training) to 1.3% (test).</li>
          <li>Only 64 positive (PHA) examples in the test set — confidence intervals are wide.</li>
          <li>Single JPL snapshot. Orbits and flags change with new observations.</li>
          <li>Diameter measured for only ~2.9% of objects; albedo for ~2.8%.</li>
          <li>No authentication; rate limiting is per-process.</li>
          <li>Model binaries are not in Git — a deployment without the artifact files will have no models.</li>
        </ul>
      </Section>

      {/* Technology */}
      <Section title="Technology">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            ['Frontend', 'React 18, Vite, TypeScript, Tailwind CSS'],
            ['State / Data', 'TanStack Query, React Router'],
            ['Charts', 'Recharts'],
            ['Backend', 'Python 3.12, FastAPI, SQLAlchemy'],
            ['Database', 'PostgreSQL 16 via Alembic'],
            ['ML', 'scikit-learn, XGBoost, SHAP'],
          ].map(([name, stack]) => (
            <div key={name} className="bg-surface-raised border border-border rounded-lg p-3">
              <p className="text-label uppercase tracking-wider text-muted mb-1">{name}</p>
              <p className="text-sm text-white/70">{stack}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* External links */}
      <Section title="Further Reading">
        <div className="space-y-2">
          {[
            { href: 'https://ssd.jpl.nasa.gov/sbdb.cgi', label: 'JPL Small-Body Database' },
            { href: 'https://ssd-api.jpl.nasa.gov/doc/cad.html', label: 'JPL Close-Approach Data API' },
            { href: 'https://www.astro.umd.edu/~hamilton/NEO/', label: 'NASA NEO Basics' },
            { href: 'https://shap.readthedocs.io/', label: 'SHAP Documentation' },
          ].map(({ href, label }) => (
            <a
              key={href}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-accent hover:text-accent-hover transition-colors text-sm"
            >
              {label}
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          ))}
        </div>
      </Section>
    </div>
  );
}
