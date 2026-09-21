# API Contract

> **CONTRACT — NOT IMPLEMENTED YET**
>
> These endpoint definitions are contracts for the future backend implementation.
> The implementation agent should follow these contracts or explicitly document any changes.

---

## `GET /api/health`

Health check endpoint.

**Response** `200 OK`
```json
{
  "status": "healthy",
  "version": "TBD",
  "timestamp": "ISO-8601"
}
```

---

## `GET /api/neos`

List NEO objects with optional filtering and pagination.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| page | int | No | Page number (default 1) |
| per_page | int | No | Items per page (default 20) |
| is_hazardous | bool | No | Filter by hazardous status |
| search | string | No | Search by name or designation |

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "string",
      "name": "string",
      "designation": "string",
      "is_potentially_hazardous": "boolean",
      "absolute_magnitude_h": "number | null",
      "estimated_diameter_km_min": "number | null",
      "estimated_diameter_km_max": "number | null"
    }
  ],
  "total": "integer",
  "page": "integer",
  "per_page": "integer"
}
```

> Field names are subject to change after real data schema is confirmed.

---

## `GET /api/neos/{id}`

Get detailed information for a single NEO.

**Response** `200 OK`
```json
{
  "id": "string",
  "name": "string",
  "designation": "string",
  "is_potentially_hazardous": "boolean",
  "absolute_magnitude_h": "number | null",
  "estimated_diameter_km_min": "number | null",
  "estimated_diameter_km_max": "number | null",
  "orbital_data": {},
  "close_approaches": []
}
```

**Response** `404 Not Found`
```json
{ "detail": "NEO not found" }
```

---

## `GET /api/neos/{id}/approaches`

List close-approach data for a specific NEO.

**Response** `200 OK`
```json
{
  "neo_id": "string",
  "approaches": [
    {
      "date": "string",
      "relative_velocity_km_s": "number | null",
      "miss_distance_km": "number | null",
      "orbiting_body": "string"
    }
  ]
}
```

---

## `POST /api/predict`

Submit a NEO record for classification prediction.

**Request Body**
```json
{
  "features": {}
}
```

> Feature schema TBD — depends on the trained model's feature set.

**Response** `200 OK`
```json
{
  "prediction": "string",
  "probability": "number",
  "model_version": "string",
  "explanation": {}
}
```

---

## `GET /api/models`

List available trained models.

**Response** `200 OK`
```json
{
  "models": [
    {
      "version": "string",
      "name": "string",
      "created_at": "ISO-8601",
      "metrics": {}
    }
  ]
}
```

---

## `GET /api/models/{version}`

Get metadata for a specific model version.

**Response** `200 OK`
```json
{
  "version": "string",
  "name": "string",
  "created_at": "ISO-8601",
  "features": [],
  "metrics": {},
  "parameters": {}
}
```

---

## `GET /api/analytics`

Aggregated analytics and summary statistics.

**Response** `200 OK`
```json
{
  "total_neos": "integer",
  "hazardous_count": "integer",
  "non_hazardous_count": "integer",
  "total_approaches": "integer",
  "summary": {}
}
```

> Exact response shape depends on data availability and will be refined during implementation.
