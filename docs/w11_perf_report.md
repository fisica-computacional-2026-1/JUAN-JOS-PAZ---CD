# W11 — Performance Report

## 1. Objetivo

El objetivo de W11 fue seleccionar dos queries críticas del proyecto, definir un performance budget, medir tiempos base, guardar `EXPLAIN ANALYZE`, identificar anti-patrones, proponer reescrituras y construir un Gold mart optimizado.

---

## 2. Query crítica 1: métricas por método desde 2010

### Query baseline

```sql
WITH wide AS (
  SELECT *
  FROM silver_planet_v3
  WHERE disc_year_int >= 2010
)
SELECT
  discoverymethod_canon,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 2) AS avg_radius,
  ROUND(AVG(pl_bmasse), 2) AS avg_mass
FROM wide
WHERE pl_rade IS NOT NULL
GROUP BY discoverymethod_canon
ORDER BY n_planets DESC;
```

### Performance budget

- Budget definido: `q1 <= 1.0 s`
- Razón: Es una consulta agregada simple sobre una tabla Silver local.

### Baseline con tiempos

```text
Setup OK
┌────────┬───────────┬─────────┐
│ n_rows │ n_planets │ n_hosts │
│ int64  │   int64   │  int64  │
├────────┼───────────┼─────────┤
│   6291 │      6291 │    4709 │
└────────┴───────────┴─────────┘

{'min_s': 0.004908599999907892,
 'avg_s': 0.006519199998971696,
 'max_s': 0.008315299994137604,
 'rows': 11,
 'result': [('transit', 4588, 4.23, 112.95),
  ('radial velocity', 841, 8.88, 967.02),
  ('microlensing', 268, 10.04, 835.53),
  ('imaging', 76, 15.32, 4492.27),
  ('transit timing variations', 40, 6.46, 483.47),
  ('eclipse timing variations', 14, 12.91, 2092.93),
  ('orbital brightness modulation', 6, 9.65, 350.32),
  ('astrometry', 6, 12.45, 4673.61),
  ('pulsar timing', 2, 7.56, 127.31),
  ('pulsation timing variations', 1, 12.4, 3750.39),
  ('disk kinematics', 1, 13.3, 794.58)]}
```

### EXPLAIN ANALYZE

El plan fue guardado en:

```text
artifacts/w11_explain_critical_q1.txt
```

### Anti-patrón identificado

El principal anti-patrón es usar `SELECT *` dentro de la CTE `wide`. Aunque la consulta final solo necesita `discoverymethod_canon`, `pl_rade`, `pl_bmasse` y `disc_year_int`, el `SELECT *` expresa una lectura innecesariamente amplia.

### Reescritura

```sql
SELECT
  discoverymethod_canon,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 2) AS avg_radius,
  ROUND(AVG(pl_bmasse), 2) AS avg_mass
FROM silver_planet_v3
WHERE disc_year_int >= 2010
  AND pl_rade IS NOT NULL
GROUP BY discoverymethod_canon
ORDER BY n_planets DESC;
```

### Resultado después de reescritura

```text
{'min_s': 0.004960199999914039,
 'avg_s': 0.005861033333834105,
 'max_s': 0.007507000002078712,
 'rows': 11,
 'result': [('transit', 4588, 4.23, 112.95),
  ('radial velocity', 841, 8.88, 967.02),
  ('microlensing', 268, 10.04, 835.53),
  ('imaging', 76, 15.32, 4492.27),
  ('transit timing variations', 40, 6.46, 483.47),
  ('eclipse timing variations', 14, 12.91, 2092.93),
  ('astrometry', 6, 12.45, 4673.61),
  ('orbital brightness modulation', 6, 9.65, 350.32),
  ('pulsar timing', 2, 7.56, 127.31),
  ('disk kinematics', 1, 13.3, 794.58),
  ('pulsation timing variations', 1, 12.4, 3750.39)]}
```

### Justificación

La reescritura elimina la CTE innecesaria y proyecta únicamente las columnas utilizadas. También empuja los filtros directamente sobre la tabla base, facilitando que el motor reduzca filas antes del `GROUP BY`.

---

## 3. Query crítica 2: métricas por host con JOIN

### Query baseline

```sql
WITH joined AS (
  SELECT *
  FROM silver_planet_v3 p
  JOIN dim_host_w11 h
    ON p.hostname_canon = h.hostname_canon
)
SELECT
  hostname_canon,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 2) AS avg_radius,
  ROUND(AVG(st_teff), 2) AS avg_st_teff
FROM joined
WHERE pl_rade IS NOT NULL
GROUP BY hostname_canon
ORDER BY n_planets DESC
LIMIT 15;
```

### Performance budget

- Budget definido: `q2 <= 1.5 s`
- Razón: Incluye un JOIN y agregación, por lo que se permite un presupuesto ligeramente mayor.

### Baseline con tiempos

```text
{'min_s': 0.009554299998853821,
 'avg_s': 0.011644833333169421,
 'max_s': 0.012771299996529706,
 'rows': 15,
 'result': [('koi-351', 8, 3.9, 6059.66),
  ('trappist-1', 7, 0.98, 2566.0),
  ('kepler-80', 6, 1.81, 4540.0),
  ('hd 191939', 6, 6.59, 5348.0),
  ('kepler-20', 6, 2.29, 5495.0),
  ('k2-138', 6, 2.58, 5356.3),
  ('hd 110067', 6, 2.43, 5266.0),
  ('hd 34445', 6, 8.86, 5843.17),
  ('toi-1136', 6, 3.05, 5770.0),
  ('kepler-11', 6, 2.97, 5663.0),
  ('hip 41378', 6, 4.18, 6329.83),
  ('hd 219134', 6, 3.67, 4770.33),
  ('toi-178', 6, 2.22, 4316.0),
  ('kepler-82', 5, 3.7, 5411.8),
  ('k2-268', 5, 1.85, 5106.0)]}
```

### EXPLAIN ANALYZE

El plan fue guardado en:

```text
artifacts/w11_explain_critical_q2.txt
```

### Anti-patrones identificados

Se identificaron dos anti-patrones:

1. `SELECT *` en una CTE con JOIN, lo que aumenta el ancho intermedio de la consulta.
2. Filtrar `pl_rade IS NOT NULL` después del JOIN, cuando podría filtrarse antes para reducir las filas que entran al JOIN.

### Reescritura

```sql
SELECT
  p.hostname_canon,
  COUNT(*) AS n_planets,
  ROUND(AVG(p.pl_rade), 2) AS avg_radius,
  ROUND(AVG(h.st_teff), 2) AS avg_st_teff
FROM (
  SELECT hostname_canon, pl_rade
  FROM silver_planet_v3
  WHERE pl_rade IS NOT NULL
) p
JOIN (
  SELECT hostname_canon, st_teff
  FROM dim_host_w11
  WHERE st_teff IS NOT NULL
) h
  ON p.hostname_canon = h.hostname_canon
GROUP BY p.hostname_canon
ORDER BY n_planets DESC
LIMIT 15;
```

### Resultado después de reescritura

```text
{'min_s': 0.007786699999996927,
 'avg_s': 0.009180666667816695,
 'max_s': 0.011273000003711786,
 'rows': 15,
 'result': [('koi-351', 8, 3.9, 6080.0),
  ('trappist-1', 7, 0.98, 2566.0),
  ('hd 219134', 6, 3.67, 4913.0),
  ('toi-178', 6, 2.22, 4316.0),
  ('hip 41378', 6, 4.18, 6371.0),
  ('kepler-11', 6, 2.97, 5663.0),
  ('kepler-20', 6, 2.29, 5495.0),
  ('hd 34445', 6, 8.86, 5879.0),
  ('k2-138', 6, 2.58, 5356.3),
  ('kepler-80', 6, 1.81, 4540.0),
  ('toi-1136', 6, 3.05, 5770.0),
  ('hd 191939', 6, 6.59, 5348.0),
  ('hd 110067', 6, 2.43, 5266.0),
  ('kepler-444', 5, 0.54, 5046.0),
  ('kepler-238', 5, 2.96, 5800.0)]}
```

### Justificación

La reescritura reduce el número de columnas antes del JOIN y aplica filtros antes de unir las tablas. Esto disminuye el ancho de datos intermedio y evita que el JOIN procese columnas que no son necesarias para la métrica final.

---

## 4. Comparación antes/después

```text
{'q1_baseline': {'min_s': 0.004908599999907892,
  'avg_s': 0.006519199998971696,
  'max_s': 0.008315299994137604,
  'rows': 11,
  'result': [('transit', 4588, 4.23, 112.95),
   ('radial velocity', 841, 8.88, 967.02),
   ('microlensing', 268, 10.04, 835.53),
   ('imaging', 76, 15.32, 4492.27),
   ('transit timing variations', 40, 6.46, 483.47),
   ('eclipse timing variations', 14, 12.91, 2092.93),
   ('orbital brightness modulation', 6, 9.65, 350.32),
   ('astrometry', 6, 12.45, 4673.61),
   ('pulsar timing', 2, 7.56, 127.31),
   ('pulsation timing variations', 1, 12.4, 3750.39),
   ('disk kinematics', 1, 13.3, 794.58)]},
 'q1_rewrite': {'min_s': 0.004960199999914039,
  'avg_s': 0.005861033333834105,
  'max_s': 0.007507000002078712,
  'rows': 11,
  'result': [('transit', 4588, 4.23, 112.95),
   ('radial velocity', 841, 8.88, 967.02),
   ('microlensing', 268, 10.04, 835.53),
   ('imaging', 76, 15.32, 4492.27),
   ('transit timing variations', 40, 6.46, 483.47),
   ('eclipse timing variations', 14, 12.91, 2092.93),
...
   ('toi-1136', 6, 3.05, 5770.0),
   ('hd 191939', 6, 6.59, 5348.0),
   ('hd 110067', 6, 2.43, 5266.0),
   ('kepler-444', 5, 0.54, 5046.0),
   ('kepler-238', 5, 2.96, 5800.0)]}}
Output is truncated. View as a scrollable element or open in a text editor. Adjust cell output settings...
```

En ambas consultas se busca reducir el trabajo del motor mediante dos ideas: leer menos columnas y filtrar antes. Aunque en un dataset pequeño las diferencias pueden ser mínimas, el patrón es importante para escalabilidad.

---

## 5. Gold mart propuesto: `gold_perf_method_era`

### SQL

```sql
CREATE VIEW gold_perf_method_era AS
SELECT
  discoverymethod_canon,
  CASE
    WHEN disc_year_int IS NULL THEN 'unknown'
    WHEN disc_year_int < 2000 THEN 'pre_2000'
    WHEN disc_year_int BETWEEN 2000 AND 2009 THEN '2000s'
    WHEN disc_year_int BETWEEN 2010 AND 2019 THEN '2010s'
    WHEN disc_year_int >= 2020 THEN '2020s'
    ELSE 'unknown'
  END AS disc_era,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 2) AS avg_radius,
  ROUND(AVG(pl_bmasse), 2) AS avg_mass
FROM silver_planet_v3
WHERE discoverymethod_canon IS NOT NULL
GROUP BY discoverymethod_canon, disc_era;
```

### Output

```text
┌───────────────────────────┬──────────┬───────────┬────────────┬──────────┐
│   discoverymethod_canon   │ disc_era │ n_planets │ avg_radius │ avg_mass │
│          varchar          │ varchar  │   int64   │   double   │  double  │
├───────────────────────────┼──────────┼───────────┼────────────┼──────────┤
│ transit                   │ 2010s    │      3065 │       3.92 │     89.5 │
│ transit                   │ 2020s    │      1524 │       4.84 │   159.88 │
│ radial velocity           │ 2010s    │       454 │       9.72 │   941.24 │
│ radial velocity           │ 2020s    │       411 │       7.99 │  1056.45 │
│ radial velocity           │ 2000s    │       289 │      12.09 │  1113.39 │
│ microlensing              │ 2020s    │       188 │       9.78 │   837.63 │
│ microlensing              │ 2010s    │        80 │      10.63 │   830.58 │
│ transit                   │ 2000s    │        61 │      13.53 │   710.64 │
│ imaging                   │ 2020s    │        43 │      14.97 │  4364.47 │
│ imaging                   │ 2010s    │        37 │      15.75 │  4616.27 │
│ radial velocity           │ pre_2000 │        27 │      13.38 │  1194.89 │
│ transit timing variations │ 2010s    │        21 │       5.55 │   517.46 │
│ transit timing variations │ 2020s    │        20 │       7.47 │   425.73 │
│ imaging                   │ 2000s    │        17 │      16.48 │  4180.42 │
│ eclipse timing variations │ 2010s    │        13 │       12.8 │  2391.75 │
├───────────────────────────┴──────────┴───────────┴────────────┴──────────┤
│ 15 rows                                                        5 columns │
└──────────────────────────────────────────────────────────────────────────┘

```

### Interpretación

Este Gold mart resume los descubrimientos por método y era. Es útil porque evita recalcular agrupaciones frecuentes desde Silver y entrega una tabla lista para análisis.

---

## 6. Validación de resultados

```sql
SELECT SUM(n_planets) AS n_gold_rows
FROM gold_perf_method_era;

SELECT COUNT(*) AS n_source_rows
FROM silver_planet_v3
WHERE discoverymethod_canon IS NOT NULL;
```

**Output:**

```text
┌─────────────┐
│ n_gold_rows │
│   int128    │
├─────────────┤
│        6291 │
└─────────────┘

┌───────────────┐
│ n_source_rows │
│     int64     │
├───────────────┤
│          6291 │
└───────────────┘
```

La validación esperada es que `SUM(n_planets)` coincida con el número de filas fuente con `discoverymethod_canon IS NOT NULL`.

---

## 7. Decisión técnica final

Se decidió crear el Gold mart `gold_perf_method_era` porque materializa una consulta frecuente del proyecto: comparar métodos de descubrimiento a través del tiempo. Esta decisión reduce lógica repetida y facilita análisis posteriores.

---

## 8. Reflexión

Los anti-patrones más claros fueron `SELECT *` y filtrar tarde después de un JOIN. Aunque el dataset local es pequeño, corregir estos patrones es importante porque en datos más grandes pueden aumentar mucho el costo de lectura, memoria y tiempo de ejecución.