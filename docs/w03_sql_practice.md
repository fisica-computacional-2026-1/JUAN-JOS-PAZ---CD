# W03 — SQL Practice: JOINs, CTEs y cardinalidad

## 1. Análisis de `dim_host_bad`

Se calcularon cuatro conteos para verificar cómo cambia la cantidad de filas al hacer distintos JOIN entre `fact_planet_raw` y las dimensiones de host.

```python
n_fact = con.execute("""
SELECT COUNT(*) FROM fact_planet_raw
""").fetchone()[0]

n_join_good = con.execute("""
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_ra h
  ON f.hostname = h.hostname
""").fetchone()[0]

n_join_bad = con.execute("""
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_bad h
  ON f.hostname = h.hostname
""").fetchone()[0]

n_join_fixed = con.execute("""
WITH dim_host_fixed AS (
  SELECT DISTINCT hostname
  FROM dim_host_bad
)
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_fixed h
  ON f.hostname = h.hostname
""").fetchone()[0]

print("n_fact:", n_fact)
print("n_join_good:", n_join_good)
print("n_join_bad:", n_join_bad)
print("n_join_fixed:", n_join_fixed)
```

**Output:**

```text
n_fact: 6107
n_join_good: 6107
n_join_bad: 10779
n_join_fixed: 6107
```

El JOIN correcto mantiene las mismas filas que la tabla de hechos: `6107`. En cambio, el JOIN malo aumenta el resultado a `10779` filas porque `dim_host_bad` tiene varios registros por `hostname`. Al deduplicar la dimensión con `SELECT DISTINCT hostname`, el conteo vuelve a `6107`.

---

## 2. Evidencia del JOIN malo

```python
con.sql("""
WITH c AS (
  SELECT hostname, COUNT(*) AS cnt
  FROM dim_host_bad
  GROUP BY hostname
)
SELECT *
FROM c
WHERE cnt > 1
ORDER BY cnt DESC
LIMIT 10
""").show()
```

**Output:**

```text
┌────────────┬───────┐
│  hostname  │  cnt  │
├────────────┼───────┤
│ KOI-351    │     8 │
│ TRAPPIST-1 │     7 │
│ HD 191939  │     6 │
│ Kepler-11  │     6 │
│ HD 219134  │     6 │
│ HD 110067  │     6 │
│ Kepler-80  │     6 │
│ K2-138     │     6 │
│ TOI-1136   │     6 │
│ HD 10180   │     6 │
└────────────┴───────┘
```

```python
multiplicacion = n_join_bad - n_fact
print("Filas adicionales por JOIN malo:", multiplicacion)
```

**Output:**

```text
Filas adicionales por JOIN malo: 4672
```

Esto demuestra que `dim_host_bad` no tiene una fila única por `hostname`, por lo que no funciona como una dimensión válida y produce duplicación accidental.

---

## 3. Corrección del JOIN malo

```python
con.execute("""
CREATE OR REPLACE TABLE dim_host_fixed AS
SELECT
  hostname,
  MAX(ra) AS ra
FROM dim_host_bad
GROUP BY hostname
""")

con.sql("""
SELECT COUNT(*) AS n_rows,
       COUNT(DISTINCT hostname) AS n_keys
FROM dim_host_fixed
""").show()
```

**Output:**

```text
┌────────┬────────┐
│ n_rows │ n_keys │
├────────┼────────┤
│   4554 │   4554 │
└────────┴────────┘
```

La corrección consiste en agrupar por `hostname` para garantizar una sola fila por sistema. Como `n_rows = n_keys`, la dimensión corregida tiene cardinalidad controlada.

---

# 4. TODO 1 — LEFT JOIN y no-match

```python
query = """
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN h.hostname IS NULL THEN 1 ELSE 0 END) AS no_match
FROM fact_planet_raw f
LEFT JOIN dim_host_ra h
  ON f.hostname = h.hostname
"""
con.sql(query).show()
```

**Output esperado:**

```text
┌───────┬──────────┐
│ total │ no_match │
├───────┼──────────┤
│  6107 │        0 │
└───────┴──────────┘
```

**Interpretación:**  
La consulta verifica cuántas filas de `fact_planet_raw` quedan sin correspondencia en `dim_host_ra`. Como `no_match = 0`, todos los planetas tienen un host asociado en la dimensión.

---

# 5. TODO 2 — CTE + ranking: método principal por año

```python
query = """
WITH counts AS (
  SELECT
    disc_year,
    discoverymethod,
    COUNT(*) AS n
  FROM fact_planet_raw
  WHERE disc_year IS NOT NULL
    AND discoverymethod IS NOT NULL
  GROUP BY disc_year, discoverymethod
),
ranked AS (
  SELECT
    disc_year,
    discoverymethod,
    n,
    ROW_NUMBER() OVER (
      PARTITION BY disc_year
      ORDER BY n DESC
    ) AS rn
  FROM counts
)
SELECT
  disc_year,
  discoverymethod,
  n
FROM ranked
WHERE rn = 1
ORDER BY disc_year
"""
con.execute(query).fetchall()
```

**Interpretación:**  
Esta consulta identifica el método de descubrimiento dominante en cada año. Primero cuenta planetas por año y método, y luego usa `ROW_NUMBER()` para quedarse con el método número uno de cada año.

---

# 6. TODO 3 — Validación de cardinalidad en `dim_discovery`

```python
query = """
SELECT
  discoverymethod,
  disc_year,
  COUNT(*) AS cnt
FROM dim_discovery
GROUP BY discoverymethod, disc_year
HAVING COUNT(*) > 1
ORDER BY cnt DESC
"""
con.execute(query).fetchall()
```

**Output esperado:**

```text
[]
```

**Interpretación:**  
La consulta busca duplicados en la clave compuesta `(discoverymethod, disc_year)`. Si el resultado es vacío, entonces `dim_discovery` no tiene duplicados para esa combinación.

---

# 7. TODO 4 — JOIN + agregación: promedio de RA por método

```python
query = """
SELECT
  f.discoverymethod,
  COUNT(*) AS n_planets,
  ROUND(AVG(h.ra), 2) AS avg_ra
FROM fact_planet_raw f
JOIN dim_host_ra h
  ON f.hostname = h.hostname
WHERE f.discoverymethod IS NOT NULL
  AND h.ra IS NOT NULL
GROUP BY f.discoverymethod
ORDER BY n_planets DESC
"""
con.sql(query).show()
```

**Interpretación:**  
Esta consulta combina la tabla de hechos con la dimensión de hosts para calcular el promedio de RA por método de descubrimiento. Es un JOIN válido porque `dim_host_ra` tiene una sola fila por `hostname`.

---

# 8. Consulta extra con JOIN

## Top 10 planetas más masivos con RA de su host

```python
query = """
SELECT
  f.pl_name,
  f.pl_bmasse,
  h.ra
FROM fact_planet_raw f
JOIN dim_host_ra h
  ON f.hostname = h.hostname
WHERE f.pl_bmasse IS NOT NULL
ORDER BY f.pl_bmasse DESC
LIMIT 10
"""
con.sql(query).show()
```

**Output:**

```text
┌────────────────────────────┬───────────────┬─────────────┐
│          pl_name           │   pl_bmasse   │     ra      │
├────────────────────────────┼───────────────┼─────────────┤
│ 2MASS J22501512+2325342 b  │    9534.85221 │ 342.5634097 │
│ CD-35 2722 b               │  9375.9380065 │  92.3300147 │
│ Luhman 16 b                │  9344.1551658 │ 162.3282594 │
│ HD 188641 b                │ 9333.03117155 │ 299.4048303 │
│ KMT-2018-BLG-0885L b       │   9217.023803 │ 268.9663333 │
│ DENIS-P J082303.1-491201 b │       9057.77 │ 125.7620668 │
│ HD 26161 b                 │ 9045.39646322 │  62.4122255 │
│ HD 6860 b                  │ 8981.83078182 │   17.432979 │
│ 2MASS J11011926-7732383 b  │   8899.195396 │ 165.3295388 │
│ HD 206893 b                │   8899.195396 │ 326.3416874 │
└────────────────────────────┴───────────────┴─────────────┘
```

**Interpretación:**  
Esta consulta usa un JOIN para traer información del planeta y del host en una misma tabla. Permite observar los planetas más masivos junto con la coordenada RA de su sistema.

---

# 9. Consulta extra con CTE

## Años donde Transit superó a Radial Velocity

```python
query = """
WITH metodos AS (
  SELECT
    disc_year,
    discoverymethod,
    COUNT(*) AS n
  FROM fact_planet_raw
  WHERE disc_year IS NOT NULL
    AND discoverymethod IN ('Transit', 'Radial Velocity')
  GROUP BY disc_year, discoverymethod
),
comparacion AS (
  SELECT
    disc_year,
    MAX(CASE WHEN discoverymethod = 'Transit' THEN n END) AS transit,
    MAX(CASE WHEN discoverymethod = 'Radial Velocity' THEN n END) AS radial_velocity
  FROM metodos
  GROUP BY disc_year
)
SELECT *
FROM comparacion
WHERE transit > radial_velocity
ORDER BY disc_year
"""
con.sql(query).show()
```

**Output:**

```text
┌───────────┬─────────┬─────────────────┐
│ disc_year │ transit │ radial_velocity │
├───────────┼─────────┼─────────────────┤
│      2010 │      47 │              41 │
│      2011 │      79 │              43 │
│      2012 │      93 │              35 │
│      2013 │      80 │              33 │
│      2014 │     798 │              48 │
│      2015 │      99 │              46 │
│      2016 │    1432 │              50 │
│      2017 │      87 │              49 │
│      2018 │     242 │              46 │
│      2019 │     107 │              65 │
│      2020 │     165 │              46 │
│      2021 │     457 │              76 │
│      2022 │     191 │             118 │
│      2023 │     224 │              57 │
│      2024 │     187 │              28 │
│      2025 │     144 │              61 │
│      2026 │      26 │              24 │
└───────────┴─────────┴─────────────────┘
```

**Interpretación:**  
Esta consulta muestra los años en que el método `Transit` superó a `Radial Velocity` en número de descubrimientos. El resultado evidencia el crecimiento del método de tránsito en los descubrimientos modernos de exoplanetas.