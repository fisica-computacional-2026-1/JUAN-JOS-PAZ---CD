# W08 — Assignment Report

## 1. Objetivo

El objetivo de este assignment fue aplicar limpieza SQL sobre el dataset de exoplanetas y construir un ejemplo de relación muchos-a-muchos usando una tabla puente con PK/FK.

---

# Parte A — Limpieza Raw → Silver v2

## 2. Tabla `method_map`

Se creó una tabla `method_map` para mapear métodos de descubrimiento originales a nombres canónicos. Esto permite estandarizar categorías antes de construir una capa Silver.

```sql
CREATE TABLE method_map (
  raw_method VARCHAR PRIMARY KEY,
  canonical_method VARCHAR NOT NULL
);

INSERT INTO method_map VALUES
  ('Transit', 'transit'),
  ('Radial Velocity', 'radial_velocity'),
  ('Microlensing', 'microlensing'),
  ('Imaging', 'imaging'),
  ('Transit Timing Variations', 'transit_timing_variations'),
  ('Eclipse Timing Variations', 'eclipse_timing_variations'),
  ('Orbital Brightness Modulation', 'orbital_brightness_modulation'),
  ('Pulsar Timing', 'pulsar_timing');
```

**Output:**

```text
┌───────────────────────────────┬───────────────────────────────┐
│          raw_method           │       canonical_method        │
│            varchar            │            varchar            │
├───────────────────────────────┼───────────────────────────────┤
│ Eclipse Timing Variations     │ eclipse_timing_variations     │
│ Imaging                       │ imaging                       │
│ Microlensing                  │ microlensing                  │
│ Orbital Brightness Modulation │ orbital_brightness_modulation │
│ Pulsar Timing                 │ pulsar_timing                 │
│ Radial Velocity               │ radial_velocity               │
│ Transit                       │ transit                       │
│ Transit Timing Variations     │ transit_timing_variations     │
└───────────────────────────────┴───────────────────────────────┘

```

---

## 3. Tabla `silver_planet_v2`

Se creó `silver_planet_v2` aplicando limpieza sobre nombres de host, métodos de descubrimiento y años de descubrimiento.

Reglas aplicadas:

- `hostname_clean = LOWER(TRIM(hostname))`
- `discoverymethod_clean = COALESCE(method_map.canonical_method, LOWER(TRIM(discoverymethod)))`
- `disc_era` clasifica el año de descubrimiento por época
- Se filtran registros sin `pl_name` o sin `hostname`
- Se mantienen rangos razonables para `disc_year`, `pl_rade` y `pl_bmasse`

```sql
CREATE TABLE silver_planet_v2 AS
WITH cleaned AS (
  SELECT
    pl_name,
    hostname,
    LOWER(TRIM(hostname)) AS hostname_clean,
    discoverymethod,
    TRIM(discoverymethod) AS discoverymethod_norm,
    disc_year,
    pl_orbper,
    pl_rade,
    pl_bmasse,
    pl_eqt,
    sy_dist,
    ra,
    dec
  FROM raw_ps
  WHERE pl_name IS NOT NULL
    AND hostname IS NOT NULL
)
SELECT
  c.pl_name,
  c.hostname,
  c.hostname_clean,
  c.discoverymethod,
  COALESCE(m.canonical_method, LOWER(TRIM(c.discoverymethod_norm))) AS discoverymethod_clean,
  c.disc_year,
  CASE
    WHEN c.disc_year IS NULL THEN 'unknown'
    WHEN c.disc_year < 2000 THEN 'pre_2000'
    WHEN c.disc_year BETWEEN 2000 AND 2009 THEN '2000s'
    WHEN c.disc_year BETWEEN 2010 AND 2019 THEN '2010s'
    WHEN c.disc_year >= 2020 THEN '2020s'
    ELSE 'unknown'
  END AS disc_era,
  c.pl_orbper,
  c.pl_rade,
  c.pl_bmasse,
  c.pl_eqt,
  c.sy_dist,
  c.ra,
  c.dec
FROM cleaned c
LEFT JOIN method_map m
  ON c.discoverymethod_norm = m.raw_method
WHERE (c.disc_year IS NULL OR c.disc_year BETWEEN 1980 AND 2026)
  AND (c.pl_rade IS NULL OR c.pl_rade > 0)
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

**Hosts nulos:**

```text
┌──────────────┐
│ n_null_hosts │
│    int64     │
├──────────────┤
│            0 │
└──────────────┘
```

**Métodos limpios más frecuentes:**

```text
┌───────────────────────────────┬───────┐
│     discoverymethod_clean     │   n   │
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

# Parte B — Many-to-Many

## 4. Modelo M:N con tabla puente

Se construyó un ejemplo de relación muchos-a-muchos entre planetas y métodos de detección. Un planeta puede tener más de un método asociado y un método puede estar asociado a varios planetas.

## 5. DDL con PK/FK

```sql
CREATE TABLE planet_demo (
  planet_id INTEGER PRIMARY KEY,
  name VARCHAR NOT NULL
);

CREATE TABLE method_demo (
  method_id INTEGER PRIMARY KEY,
  method_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE planet_method_demo (
  planet_id INTEGER NOT NULL,
  method_id INTEGER NOT NULL,
  PRIMARY KEY (planet_id, method_id),
  FOREIGN KEY (planet_id) REFERENCES planet_demo(planet_id),
  FOREIGN KEY (method_id) REFERENCES method_demo(method_id)
);
```

Este DDL evidencia que la tabla puente `planet_method_demo` usa una PK compuesta `(planet_id, method_id)` y dos FK hacia las tablas padre.

---

## 6. Pregunta 1 — ¿Cuántos planetas hay por método?

```sql
SELECT
  m.method_name,
  COUNT(DISTINCT pm.planet_id) AS n_planets
FROM method_demo m
JOIN planet_method_demo pm
  ON m.method_id = pm.method_id
GROUP BY m.method_name
ORDER BY n_planets DESC, m.method_name;
```

**Output:**

```text
PEGA AQUÍ EL OUTPUT DE q1
```

---

## 7. Pregunta 2 — ¿Cuántos métodos tiene cada planeta?

```sql
SELECT
  p.name AS planet_name,
  COUNT(DISTINCT pm.method_id) AS n_methods
FROM planet_demo p
JOIN planet_method_demo pm
  ON p.planet_id = pm.planet_id
GROUP BY p.name
ORDER BY n_methods DESC, planet_name;
```

**Output:**

```text
┌─────────────────┬───────────┐
│   method_name   │ n_planets │
│     varchar     │   int64   │
├─────────────────┼───────────┤
│ radial_velocity │         3 │
│ transit         │         2 │
│ imaging         │         1 │
└─────────────────┴───────────┘
```

---

## 8. Check requerido: duplicados en la link table

```sql
SELECT planet_id, method_id, COUNT(*) AS c
FROM planet_method_demo
GROUP BY planet_id, method_id
HAVING COUNT(*) > 1;
```

**Output:**

```text
┌──────────────┬───────────┐
│ planet_name  │ n_methods │
│   varchar    │   int64   │
├──────────────┼───────────┤
│ HR 8799 b    │         2 │
│ Kepler-22 b  │         2 │
│ 51 Pegasi b  │         1 │
│ TRAPPIST-1 e │         1 │
└──────────────┴───────────┘
```

## 9. Interpretación

El check de duplicados retorna vacío, lo que indica que no hay pares repetidos `(planet_id, method_id)` en la tabla puente. Además, la PK compuesta impide insertar relaciones duplicadas. Las FK aseguran que cada relación apunte a un planeta y a un método existentes.

---

## 10. Conclusión

La limpieza Raw → Silver v2 permitió estandarizar nombres de host, métodos de descubrimiento y épocas de descubrimiento. El modelo M:N mostró cómo representar correctamente relaciones muchos-a-muchos mediante una tabla puente con PK compuesta y FK hacia las tablas principales.