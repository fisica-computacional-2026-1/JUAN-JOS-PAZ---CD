# W04A — Performance Report

## 1. Consulta métrica: descubrimientos por década y período orbital promedio

### SQL

```sql
SELECT
  FLOOR(disc_year / 10) * 10 AS decade,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_orbper), 2) AS avg_orbital_period
FROM fact_planet
WHERE disc_year IS NOT NULL
  AND disc_year >= 2000
  AND pl_orbper IS NOT NULL
GROUP BY decade
ORDER BY decade ASC;
```

### Plan EXPLAIN

```text
┌───────────────────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│  (floor((exoplanets_w04a  │
│     .main.fact_planet     │
│.disc_year / 10)) * 10) ASC│
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             0             │
│         n_planets         │
│     avg_orbital_period    │
│                           │
│         ~628 rows         │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│         Groups: #0        │
│                           │
│        Aggregates:        │
│        count_star()       │
│          avg(#1)          │
...
│                           ││                           │
│        ~1,257 rows        ││         ~941 rows         │
└───────────────────────────┘└───────────────────────────┘
```

### Conclusión 1: ¿dónde está el costo?

El costo principal está en el `SEQ_SCAN` sobre `fact_planet`, donde se leen las columnas necesarias y se aplican los filtros sobre `disc_year` y `pl_orbper`. Después aparece el `HASH_GROUP_BY`, que agrupa por década y calcula el conteo de planetas y el promedio del período orbital.

### Conclusión 2: ¿qué mejoraría?

La consulta ya evita `SELECT *`, por lo que lee menos columnas. Como mejora, mantendría el filtro antes del `GROUP BY` y evitaría agregar columnas que no sean necesarias para responder la pregunta.

---

## 2. Consulta con JOIN: radio promedio según grupo de temperatura estelar

### SQL

```sql
SELECT
  CASE
    WHEN h.st_teff < 5000 THEN 'cool_star'
    WHEN h.st_teff BETWEEN 5000 AND 6500 THEN 'solar_like_star'
    ELSE 'hot_star'
  END AS stellar_group,
  COUNT(*) AS n_planets,
  ROUND(AVG(f.pl_rade), 2) AS avg_radius
FROM fact_planet f
JOIN dim_host_full h
  ON f.hostname = h.hostname
WHERE h.st_teff IS NOT NULL
  AND f.pl_rade IS NOT NULL
GROUP BY stellar_group
ORDER BY n_planets DESC;
```

### Plan EXPLAIN

```text
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
EXPLAIN ANALYZE  SELECT   FLOOR(disc_year / 10) * 10 AS decade,   COUNT(*) AS n_planets,   ROUND(AVG(pl_orbper), 2) AS avg_orbital_period FROM fact_planet WHERE disc_year IS NOT NULL   AND disc_year >= 2000   AND pl_orbper IS NOT NULL GROUP BY decade ORDER BY decade ASC 
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0125s             ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│           0 rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│  (floor((exoplanets_w04a  │
│     .main.fact_planet     │
...
│         5,919 rows        │
│          (0.00s)          │
└───────────────────────────┘
```

### Conclusión 1: ¿dónde está el costo?

El costo se reparte entre el `SEQ_SCAN` de `fact_planet`, el `SEQ_SCAN` de `dim_host_full` y el `HASH_JOIN` por `hostname`. Luego el resultado se agrupa con `HASH_GROUP_BY` para obtener el conteo de planetas y el radio promedio por grupo estelar.

### Conclusión 2: ¿qué mejoraría?

La consulta ya filtra valores nulos antes de agrupar. Para mejorarla, mantendría solo las columnas necesarias en cada lado del JOIN: `hostname`, `pl_rade` y `st_teff`. También validaría que `dim_host_full` tenga una sola fila por `hostname` para evitar inflación de filas.

---

## 3. Evidencia exportada

Los planes fueron guardados como evidencia en:

```text
artifacts/w04a_explain_q1.txt
```
