# W09 — Reporte de limpieza avanzada

## 1. Objetivo

El objetivo de W09 fue aplicar limpieza avanzada sobre el dataset de exoplanetas y construir una capa `silver_planet_v3` con columnas normalizadas y banderas de calidad. También se creó una tabla de eventos de calidad para registrar checks mínimos del pipeline.

---

# Parte A — Limpieza avanzada

## 2. Tabla `method_synonyms`

Se creó la tabla `method_synonyms` para mapear métodos de descubrimiento normalizados a una versión canónica en formato `snake_case`.

```sql
CREATE TABLE method_synonyms (
  raw_norm VARCHAR PRIMARY KEY,
  canonical VARCHAR NOT NULL
);

INSERT INTO method_synonyms VALUES
  ('transit', 'transit'),
  ('radial velocity', 'radial_velocity'),
  ('microlensing', 'microlensing'),
  ('imaging', 'imaging'),
  ('transit timing variations', 'transit_timing_variations'),
  ('eclipse timing variations', 'eclipse_timing_variations'),
  ('orbital brightness modulation', 'orbital_brightness_modulation'),
  ('pulsar timing', 'pulsar_timing');
```

**Output:**

```text
┌───────────────────────────────┬───────────────────────────────┐
│           raw_norm            │           canonical           │
│            varchar            │            varchar            │
├───────────────────────────────┼───────────────────────────────┤
│ eclipse timing variations     │ eclipse_timing_variations     │
│ imaging                       │ imaging                       │
│ microlensing                  │ microlensing                  │
│ orbital brightness modulation │ orbital_brightness_modulation │
│ pulsar timing                 │ pulsar_timing                 │
│ radial velocity               │ radial_velocity               │
│ transit                       │ transit                       │
│ transit timing variations     │ transit_timing_variations     │
└───────────────────────────────┴───────────────────────────────┘
```

---

## 3. Construcción de `silver_planet_v3`

La tabla `silver_planet_v3` se construyó a partir de `raw_ps`. En esta versión se agregaron columnas canónicas y una bandera de calidad para el año de descubrimiento.

Columnas nuevas o transformadas:

- `hostname_canon`: versión normalizada de `hostname` usando `LOWER(TRIM(hostname))`.
- `discoverymethod_canon`: método de descubrimiento canónico usando `method_synonyms` y `COALESCE`.
- `disc_year_int`: año de descubrimiento convertido con `TRY_CAST`.
- `disc_year_bad`: bandera booleana para detectar años nulos, inválidos o fuera del rango 1980–2026.

```sql
CREATE TABLE silver_planet_v3 AS
WITH cleaned AS (
  SELECT
    pl_name,
    hostname,
    LOWER(TRIM(hostname)) AS hostname_canon,
    discoverymethod,
    LOWER(TRIM(discoverymethod)) AS discoverymethod_norm,
    TRY_CAST(disc_year AS INTEGER) AS disc_year_int,
    CASE
      WHEN TRY_CAST(disc_year AS INTEGER) IS NULL THEN TRUE
      WHEN TRY_CAST(disc_year AS INTEGER) < 1980 THEN TRUE
      WHEN TRY_CAST(disc_year AS INTEGER) > 2026 THEN TRUE
      ELSE FALSE
    END AS disc_year_bad,
    pl_orbper,
    pl_rade,
    pl_bmasse,
    pl_eqt,
    sy_dist,
    ra,
    dec,
    st_teff,
    st_rad,
    st_mass
  FROM raw_ps
  WHERE pl_name IS NOT NULL
    AND hostname IS NOT NULL
)
SELECT
  c.pl_name,
  c.hostname,
  c.hostname_canon,
  c.discoverymethod,
  COALESCE(s.canonical, c.discoverymethod_norm) AS discoverymethod_canon,
  c.disc_year_int,
  c.disc_year_bad,
  c.pl_orbper,
  c.pl_rade,
  c.pl_bmasse,
  c.pl_eqt,
  c.sy_dist,
  c.ra,
  c.dec,
  c.st_teff,
  c.st_rad,
  c.st_mass
FROM cleaned c
LEFT JOIN method_synonyms s
  ON c.discoverymethod_norm = s.raw_norm
WHERE (c.pl_rade IS NULL OR c.pl_rade > 0)
  AND (c.pl_bmasse IS NULL OR c.pl_bmasse > 0);
```

**Conteo de filas:**

```text
┌────────┐
│ n_rows │
│ int64  │
├────────┤
│   6291 │
└────────┘
```

**Años problemáticos:**

```text
┌───────────────┐
│ disc_year_bad │
│     int64     │
├───────────────┤
│             1 │
└───────────────┘
```

**Métodos canónicos más frecuentes:**

```text
┌───────────────────────────────┬───────┐
│     discoverymethod_canon     │   n   │
│            varchar            │ int64 │
├───────────────────────────────┼───────┤
│ transit                       │  4651 │
│ radial_velocity               │  1181 │
│ microlensing                  │   278 │
│ imaging                       │    97 │
│ transit_timing_variations     │    41 │
│ eclipse_timing_variations     │    17 │
│ orbital_brightness_modulation │     9 │
...
├───────────────────────────────┴───────┤
│ 11 rows                     2 columns │
└───────────────────────────────────────┘
```

---

## 4. Interpretación

La normalización de `hostname` y `discoverymethod` reduce inconsistencias de escritura y facilita los análisis agrupados. La columna `disc_year_bad` permite separar la limpieza de la validación: en lugar de eliminar todos los registros problemáticos, se marcan para revisión.

El uso de `TRY_CAST` hace que el pipeline sea más robusto ante valores no convertibles. Si aparece un año inválido o fuera del rango esperado, la fila puede mantenerse en Silver pero queda señalada por una bandera de calidad.