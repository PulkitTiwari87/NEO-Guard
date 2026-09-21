# Feature Policy

## Admission Criteria

A feature can only be used in the ML pipeline if **all** of the following are true:

1. It exists in the authoritative dataset (or is a documented derivation of fields that exist).
2. Its meaning is documented in the Data Dictionary.
3. It is available at prediction time (not post-outcome).
4. It does not directly encode the target variable.
5. Its preprocessing is reproducible and documented.

**No invented scientific features.** Every feature must trace back to a real field in the source data.

---

## Derived Feature Documentation Template

Any feature that is derived (computed from one or more source features) must document:

```
Name:
Source features:
Formula:
Units:
Transformation:
Scientific rationale:
Leakage assessment:
```

---

## Feature Registry

The implementation agent must maintain a feature registry (a table or structured file) listing every feature used in training, along with its audit status per the Data Leakage policy.

| Feature | Source | Type | Leakage Audit | Allowed |
|---------|--------|------|---------------|---------|
| TBD | TBD | TBD | TBD | TBD |

> This table will be populated during Phase 2 (Claude Code).
