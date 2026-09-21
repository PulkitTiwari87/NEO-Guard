# Frontend Contract

> **Status: PLANNED — NOT IMPLEMENTED**
>
> The frontend will be implemented in Phase 3 (Antigravity) using Stitch and Apple-inspired design principles.

---

## Planned Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Overview with key metrics and recent data |
| `/neos` | NEO Explorer | Searchable, filterable list of NEO objects |
| `/neos/:id` | NEO Detail | Detailed view of a single NEO with approaches |
| `/analytics` | Analytics | Data visualisations and summary statistics |
| `/models` | Model Performance | Model metrics, comparison, version history |
| `/predict` | Prediction | Submit features and view prediction + explanation |
| `/about` | About / Methodology | Scientific methodology and limitations |

## Planned UI Components

- Dashboard with key metrics cards
- NEO explorer with search, filter, pagination
- Object detail page with orbital data and close-approach history
- Analytics charts (distribution, timeline, scatter)
- Model performance dashboard (metrics, confusion matrix, ROC)
- Prediction interface with SHAP explanation visualisation
- Methodology / about page

## Technology Stack

| Technology | Purpose |
|------------|---------|
| React | UI framework |
| Vite | Build tool |
| Tailwind CSS | Styling |
| Stitch | Design system generation |
| Charting library (TBD) | Data visualisation |

## Design Principles

See [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) for the design direction.

## Data Contract

The frontend consumes the API defined in [API_CONTRACT.md](API_CONTRACT.md). It must not bypass the API to access the database directly.
