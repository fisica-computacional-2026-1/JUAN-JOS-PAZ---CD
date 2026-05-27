# W05A — Evidencia modelo con surrogate key y FK

## 1. Dimensión `dim_host_sk`

Se creó la dimensión `dim_host_sk` usando una llave surrogate `host_id` como clave primaria. La columna `hostname` se mantiene como llave natural única.

```sql
SELECT
  COUNT(*) AS n_rows,
  COUNT(DISTINCT hostname) AS n_keys
FROM dim_host_sk;
```

**Output:**

```text
┌────────┬────────┐
│ n_rows │ n_keys │
│ int64  │ int64  │
├────────┼────────┤
│   4705 │   4705 │
└────────┴────────┘
```

## 2. Tabla de hechos `fact_planet_sk`

Se creó `fact_planet_sk` con `pl_name` como clave primaria y `host_id` como clave foránea hacia `dim_host_sk(host_id)`.

```sql
SELECT COUNT(*) AS n_fact_sk
FROM fact_planet_sk;
```

**Output:**

```text
┌───────────┐
│ n_fact_sk │
│   int64   │
├───────────┤
│      6286 │
└───────────┘
```

## 3. Check de huérfanos

```sql
SELECT COUNT(*) AS orphan_rows
FROM fact_planet_sk f
LEFT JOIN dim_host_sk d
  ON f.host_id = d.host_id
WHERE d.host_id IS NULL;
```

**Output:**

```text
┌─────────────┐
│ orphan_rows │
│    int64    │
├─────────────┤
│           0 │
└─────────────┘
```

## 4. Interpretación

Si `n_rows = n_keys` en `dim_host_sk`, significa que existe una sola fila por `hostname`. Si `orphan_rows = 0`, entonces todas las filas de `fact_planet_sk` tienen un `host_id` válido en la dimensión. Esto confirma que el modelo con PK/FK conserva integridad referencial.