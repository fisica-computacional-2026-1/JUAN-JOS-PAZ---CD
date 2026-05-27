# W03 — Caso real de JOIN malo

## 1. Contexto

Se construyó una tabla llamada `dim_host_bad` a partir de `raw_ps`. Esta tabla conserva múltiples filas por `hostname`, por lo que no cumple la regla de una dimensión válida: tener una sola fila por clave.

El problema aparece cuando se hace un JOIN entre `fact_planet_raw` y `dim_host_bad` usando `hostname`.

---

## 2. Evidencia con conteos antes y después

```python
n_fact = con.execute("""
SELECT COUNT(*) FROM fact_planet_raw
""").fetchone()[0]

n_join_bad = con.execute("""
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_bad h
  ON f.hostname = h.hostname
""").fetchone()[0]

print("n_fact:", n_fact)
print("n_join_bad:", n_join_bad)
print("filas_extra:", n_join_bad - n_fact)
```

**Output:**

```text
n_fact: 6107
n_join_bad: 10779
filas_extra: 4672
```

El JOIN malo genera `4672` filas adicionales. Esto indica que el JOIN está multiplicando registros.

---

## 3. Diagnóstico: clave que falló

La clave que falló fue `hostname`, porque `dim_host_bad` contiene varias filas para un mismo sistema planetario.

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

Estos resultados muestran que algunos sistemas aparecen varias veces en `dim_host_bad`. Por eso, al hacer JOIN, cada planeta puede emparejarse con más de una fila del host.

---

## 4. Fix simple: deduplicar con `GROUP BY`

La solución fue crear una dimensión corregida con una sola fila por `hostname`.

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

Como `n_rows = n_keys`, la tabla `dim_host_fixed` sí tiene una fila única por `hostname`.

---

## 5. Validación del JOIN corregido

```python
n_join_fixed = con.execute("""
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_fixed h
  ON f.hostname = h.hostname
""").fetchone()[0]

print("n_fact:", n_fact)
print("n_join_fixed:", n_join_fixed)
```

**Output:**

```text
n_fact: 6107
n_join_fixed: 6107
```

Después de corregir la dimensión, el JOIN ya no multiplica filas. El conteo final coincide con el número de filas de la tabla de hechos.

---

## 6. Conclusión

El JOIN malo ocurrió porque `dim_host_bad` no tenía cardinalidad uno-a-uno respecto a `hostname`. La clave `hostname` no era única en la dimensión, lo que generó duplicación accidental. La solución fue deduplicar la tabla usando `GROUP BY hostname` y seleccionar un único valor de `ra` con `MAX(ra)`.