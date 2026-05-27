## Decisión W01B — Trazabilidad del archivo Raw

- Fecha: 2026-05-26
- Decisión: Guardar evidencia del archivo Raw `pscomppars.csv` mediante SHA-256, número de filas y número de columnas.
- Razón: El hash permite detectar cambios invisibles en el archivo, aunque conserve el mismo nombre. Esto mejora la confiabilidad y trazabilidad del proceso de ingesta.
- Alternativas: Confiar solo en el nombre del archivo, o registrar únicamente la fecha de descarga. Ambas alternativas fueron rechazadas porque no garantizan que el contenido sea el mismo.
- Evidencia:
  - Archivo: `data/raw/pscomppars.csv`
  - Filas: `6153`
  - Columnas: `16`
  - JSON generado en `artifacts/w01b_raw_evidence_*.json`
  - Check adicional: validación de valores físicos negativos en `pl_orbper`, `pl_rade` y `pl_bmasse`.

## Decisión W02A — Separar consultas de calidad y consultas científicas

- Fecha: 2026-05-26
- Decisión: Documentar por separado las consultas de calidad de datos y las consultas científicas en `docs/w02a_sql_practice.md`.
- Razón: Las consultas de calidad sirven para revisar la confiabilidad del dataset, mientras que las consultas científicas permiten interpretar patrones físicos o astronómicos.
- Alternativas: Mezclar todas las consultas sin clasificación. Se rechaza porque dificulta distinguir validación de datos e interpretación científica.
- Evidencia:
  - Consulta de calidad 1: años de descubrimiento fuera de rango.
  - Consulta de calidad 2: outliers simples en radio planetario.
  - Consulta científica 1: radio promedio por método de descubrimiento.
  - Consulta científica 2: descubrimientos de exoplanetas por década.



## Decisión W03 — Validación de cardinalidad antes de hacer JOIN

- Fecha: 2026-05-26
- Decisión: Validar la cardinalidad de las dimensiones antes de hacer JOIN con la tabla de hechos.
- Razón: Un JOIN con una dimensión que no tiene llave única puede multiplicar filas y producir resultados incorrectos.
- Evidencia:
  - `n_fact = 6107`
  - `n_join_good = 6107`
  - `n_join_bad = 10779`
  - `n_join_fixed = 6107`
  - Filas adicionales por JOIN malo: `4672`

Query de evidencia:

```sql
WITH c AS (
  SELECT hostname, COUNT(*) AS cnt
  FROM dim_host_bad
  GROUP BY hostname
)
SELECT *
FROM c
WHERE cnt > 1
ORDER BY cnt DESC
LIMIT 10;
```

Conclusión: `dim_host_bad` tenía múltiples filas por `hostname`, lo que generó duplicación accidental. La solución fue construir una dimensión corregida con una sola fila por `hostname`.

## Decisión W03A — Selección de 12 columnas para reporte de calidad

- Fecha: 2026-05-26
- Decisión: Seleccionar 12 columnas para evaluar calidad inicial del dataset `raw_ps`: `pl_name`, `hostname`, `discoverymethod`, `disc_year`, `pl_orbper`, `pl_rade`, `pl_bmasse`, `pl_eqt`, `sy_dist`, `ra`, `dec` y `st_teff`.
- Razón: Estas columnas cubren identificación del planeta, identificación del sistema, método y año de descubrimiento, parámetros físicos del planeta, distancia, coordenadas y temperatura efectiva de la estrella.
- Evidencia: Se creó un reporte de nulos usando `quality_df`, luego se materializó como tabla `quality_w03a` en DuckDB y se exportó como `artifacts/quality_w03a.csv`.
- Check adicional: Se aplicó un check de rango sobre `pl_orbper`, considerando inválidos los valores menores o iguales a cero.

Query de evidencia:

```sql
SELECT 'pl_name' AS col, COUNT(*) - COUNT(pl_name) AS nulls FROM raw_ps
UNION ALL
SELECT 'hostname' AS col, COUNT(*) - COUNT(hostname) AS nulls FROM raw_ps
UNION ALL
SELECT 'discoverymethod' AS col, COUNT(*) - COUNT(discoverymethod) AS nulls FROM raw_ps
UNION ALL
SELECT 'disc_year' AS col, COUNT(*) - COUNT(disc_year) AS nulls FROM raw_ps
UNION ALL
SELECT 'pl_orbper' AS col, COUNT(*) - COUNT(pl_orbper) AS nulls FROM raw_ps
UNION ALL
SELECT 'pl_rade' AS col, COUNT(*) - COUNT(pl_rade) AS nulls FROM raw_ps
UNION ALL
SELECT 'pl_bmasse' AS col, COUNT(*) - COUNT(pl_bmasse) AS nulls FROM raw_ps
UNION ALL
SELECT 'pl_eqt' AS col, COUNT(*) - COUNT(pl_eqt) AS nulls FROM raw_ps
UNION ALL
SELECT 'sy_dist' AS col, COUNT(*) - COUNT(sy_dist) AS nulls FROM raw_ps
UNION ALL
SELECT 'ra' AS col, COUNT(*) - COUNT(ra) AS nulls FROM raw_ps
UNION ALL
SELECT 'dec' AS col, COUNT(*) - COUNT(dec) AS nulls FROM raw_ps
UNION ALL
SELECT 'st_teff' AS col, COUNT(*) - COUNT(st_teff) AS nulls FROM raw_ps;
```

## Decisión W03B — Reglas Silver aplicadas

- Fecha: 2026-05-26
- Decisión: Construir `silver_planet` aplicando reglas mínimas de calidad sobre identificadores, año de descubrimiento y variables físicas básicas.
- Reglas aplicadas:
  - `pl_name IS NOT NULL`
  - `hostname IS NOT NULL`
  - `disc_year BETWEEN 1980 AND 2026` si no es nulo
  - `pl_rade > 0 AND pl_rade <= 30` si no es nulo
  - `pl_bmasse > 0` si no es nulo
  - `pl_orbper > 0` si no es nulo
- Razón: Estas reglas permiten construir una capa Silver más estable, evitando registros sin identificadores y valores físicos claramente inválidos.
- Evidencia: Se validó `silver_planet` con conteos de filas, planetas distintos y hosts distintos. También se validó `dim_host_full` con `n_rows = n_keys` y se comprobó un JOIN sano comparando `n_fact` vs `n_join`.

Query de evidencia:

```sql
SELECT
  COUNT(*) AS n_rows,
  COUNT(DISTINCT pl_name) AS distinct_pl_name,
  COUNT(DISTINCT hostname) AS distinct_hostname
FROM silver_planet;
```

Query de JOIN sano:

```sql
SELECT COUNT(*)
FROM fact_planet f
JOIN dim_host_full h
  ON f.hostname = h.hostname;
```

## Decisión W04 — Reglas Silver y reporte mínimo de calidad

- Fecha: 2026-05-26
- Decisión: Construir una capa Silver aplicando reglas mínimas de calidad y materializar un reporte `quality_w03a` con checks básicos.
- Razón: Antes de crear tablas Silver, dimensiones, hechos o vistas Gold, es necesario validar que las columnas clave no rompan la trazabilidad ni los JOINs posteriores.
- Columnas clave revisadas:
  - `pl_name`
  - `hostname`
  - `pl_orbper`
- Reglas aplicadas:
  - `pl_name` no debe ser nulo.
  - `hostname` no debe ser nulo.
  - `pl_orbper` debe ser positivo cuando no sea nulo.
- Evidencia:
  - Se creó la tabla `quality_w03a`.
  - Se exportó el reporte a `artifacts/w03a_quality_*.csv`.
  - El reporte incluye checks de completitud y validez.

Query de evidencia:

```sql
CREATE TABLE quality_w03a AS

SELECT
  run_ts,
  'nulls_pl_name' AS check_name,
  'completeness' AS check_type,
  (COUNT(*) - COUNT(pl_name))::BIGINT AS metric_value
FROM raw_ps

UNION ALL

SELECT
  run_ts,
  'nulls_hostname' AS check_name,
  'completeness' AS check_type,
  (COUNT(*) - COUNT(hostname))::BIGINT AS metric_value
FROM raw_ps

UNION ALL

SELECT
  run_ts,
  'bad_pl_orbper' AS check_name,
  'validity_range' AS check_type,
  SUM(CASE WHEN pl_orbper IS NOT NULL AND pl_orbper <= 0 THEN 1 ELSE 0 END)::BIGINT AS metric_value
FROM raw_ps;