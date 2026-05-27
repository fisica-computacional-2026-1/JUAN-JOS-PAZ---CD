# Data Contract — Exoplanets Pipeline

## 1. Dataset

- Dataset: `nasa_exoplanets_pscomppars`
- Fuente Raw: `data/raw/pscomppars.csv`
- Base local: `data/exoplanets.duckdb`

## 2. Capas

### Bronze

- Tabla/Vista: `raw_ps`
- Descripción: lectura directa del CSV original.
- Grain: una fila aproximada por planeta registrado en el catálogo.

### Silver

- Tabla: `silver_planet`
- Grain: una fila por planeta identificado por `pl_name`.
- Reglas mínimas:
  - `pl_name IS NOT NULL`
  - `hostname IS NOT NULL`
  - `disc_year` entre 1980 y 2026 si no es nulo
  - `pl_rade > 0 AND pl_rade <= 30` si no es nulo
  - `pl_bmasse > 0` si no es nulo

## 3. Modelo dimensional

### `dim_host_sk`

- Grain: una fila por `hostname`.
- Primary Key: `host_id`
- Natural Key: `hostname`
- Restricciones:
  - `host_id PRIMARY KEY`
  - `hostname NOT NULL UNIQUE`

### `fact_planet_sk`

- Grain: una fila por planeta.
- Primary Key: `pl_name`
- Foreign Key: `host_id → dim_host_sk(host_id)`
- Restricciones:
  - `pl_name PRIMARY KEY`
  - `host_id NOT NULL REFERENCES dim_host_sk(host_id)`

## 4. Checks mínimos

### Unicidad de dimensión

```sql
SELECT
  COUNT(*) AS n_rows,
  COUNT(DISTINCT hostname) AS n_keys
FROM dim_host_sk;
```

Criterio esperado:

```text
n_rows = n_keys
```

### Huérfanos en tabla de hechos

```sql
SELECT COUNT(*) AS orphan_rows
FROM fact_planet_sk f
LEFT JOIN dim_host_sk d
  ON f.host_id = d.host_id
WHERE d.host_id IS NULL;
```

Criterio esperado:

```text
orphan_rows = 0
```

## 5. Gold outputs

### `gold_by_discoverymethod`

- Grain: una fila por método de descubrimiento.
- Métricas:
  - `n_planets`
  - `avg_radius`
  - `avg_mass`
  - `first_year`
  - `last_year`

### `gold_by_host`

- Grain: una fila por sistema anfitrión.
- Métricas:
  - `n_planets`
  - `avg_radius`
  - `avg_mass`
  - `first_year`
  - `last_year`