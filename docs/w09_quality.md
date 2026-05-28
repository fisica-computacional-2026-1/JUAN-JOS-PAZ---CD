# W09 — Quality Gates

## 1. Objetivo

Se creó una tabla `quality_events` para registrar eventos de calidad del dataset `silver_planet_v3`. Cada fila representa un check con su estado, valor métrico y descripción.

---

## 2. Estructura de `quality_events`

```sql
CREATE TABLE quality_events (
  ts_utc VARCHAR,
  check_name VARCHAR,
  status VARCHAR,
  metric_value BIGINT,
  details VARCHAR
);
```

La tabla incluye:

- `ts_utc`: timestamp de ejecución.
- `check_name`: nombre del check.
- `status`: resultado del check (`PASS`, `WARN` o `FAIL`).
- `metric_value`: valor numérico asociado.
- `details`: explicación del check.

---

## 3. Checks implementados

Se implementaron cuatro checks:

1. `null_pl_name`: valida nulos en `pl_name`.
2. `null_hostname_canon`: valida nulos en `hostname_canon`.
3. `bad_disc_year`: valida años de descubrimiento problemáticos.
4. `invalid_physical_values`: valida valores físicos inválidos en período orbital, radio y masa.

---

## 4. Output de `quality_events`

```sql
SELECT check_name, status, metric_value
FROM quality_events
ORDER BY check_name;
```

**Output:**

```text
┌─────────────────────────┬─────────┬──────────────┐
│       check_name        │ status  │ metric_value │
│         varchar         │ varchar │    int64     │
├─────────────────────────┼─────────┼──────────────┤
│ bad_disc_year           │ WARN    │            1 │
│ invalid_physical_values │ PASS    │            0 │
│ null_hostname_canon     │ PASS    │            0 │
│ null_pl_name            │ PASS    │            0 │
└─────────────────────────┴─────────┴──────────────┘
```

---

## 5. Interpretación

Los checks de completitud (`null_pl_name` y `null_hostname_canon`) son críticos porque estas columnas permiten identificar planetas y sistemas. Si alguno falla, podrían romperse joins, agregaciones o trazabilidad.

El check `bad_disc_year` se clasifica como `WARN` cuando existen años problemáticos, porque puede indicar datos faltantes o valores fuera de rango sin necesariamente invalidar toda la fila. El check `invalid_physical_values` sí se considera más estricto, porque valores negativos o cero en magnitudes físicas pueden afectar análisis científicos.