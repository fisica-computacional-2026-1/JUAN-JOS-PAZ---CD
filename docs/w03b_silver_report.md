
## 1. Construcción de `silver_planet`

Se creó la tabla `silver_planet` a partir de `raw_ps`, aplicando reglas mínimas de calidad para pasar de una capa Bronze a una capa Silver.

Las reglas aplicadas fueron:

- `pl_name IS NOT NULL`
- `hostname IS NOT NULL`
- `disc_year` entre 1980 y 2026 si no es nulo
- `pl_rade` mayor que 0 y menor o igual a 30 si no es nulo
- `pl_bmasse` mayor que 0 si no es nulo
- `pl_orbper` mayor que 0 si no es nulo

```python
con.execute("DROP TABLE IF EXISTS silver_planet")

con.execute("""
CREATE TABLE silver_planet AS
SELECT
  pl_name,
  hostname,
  discoverymethod,
  disc_year,
  sy_snum,
  sy_pnum,
  sy_dist,
  ra,
  dec,
  pl_orbper,
  pl_rade,
  pl_bmasse,
  pl_eqt,
  st_teff,
  st_rad,
  st_mass
FROM raw_ps
WHERE pl_name IS NOT NULL
  AND hostname IS NOT NULL
  AND (disc_year IS NULL OR disc_year BETWEEN 1980 AND 2026)
  AND (pl_rade IS NULL OR (pl_rade > 0 AND pl_rade <= 30))
  AND (pl_bmasse IS NULL OR pl_bmasse > 0)
  AND (pl_orbper IS NULL OR pl_orbper > 0)
""")
```

---

## 2. `DESCRIBE silver_planet`

```python
con.sql("DESCRIBE silver_planet").show()
```

**Output:**

```text
┌─────────────────┬─────────────┬─────────┬─────────┬─────────┬─────────┐
│   column_name   │ column_type │  null   │   key   │ default │  extra  │
│     varchar     │   varchar   │ varchar │ varchar │ varchar │ varchar │
├─────────────────┼─────────────┼─────────┼─────────┼─────────┼─────────┤
│ pl_name         │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ hostname        │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ discoverymethod │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ disc_year       │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ sy_snum         │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ sy_pnum         │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ sy_dist         │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ ra              │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ dec             │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ pl_orbper       │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ pl_rade         │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ pl_bmasse       │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ pl_eqt          │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ st_teff         │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ st_rad          │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ st_mass         │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
├─────────────────┴─────────────┴─────────┴─────────┴─────────┴─────────┤
│ 16 rows                                                     6 columns │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Conteos de `silver_planet`

```python
con.sql("""
SELECT
  COUNT(*) AS n_rows,
  COUNT(DISTINCT pl_name) AS distinct_pl_name,
  COUNT(DISTINCT hostname) AS distinct_hostname
FROM silver_planet
""").show()
```

**Output:**

```text
┌────────┬──────────────────┬───────────────────┐
│ n_rows │ distinct_pl_name │ distinct_hostname │
│ int64  │      int64       │       int64       │
├────────┼──────────────────┼───────────────────┤
│   6286 │             6286 │              4705 │
└────────┴──────────────────┴───────────────────┘
```

**Interpretación:**  
Estos conteos permiten verificar cuántas filas quedaron después de aplicar las reglas Silver y cuántos planetas y hosts únicos permanecen en el dataset. La comparación entre `n_rows` y `distinct_pl_name` ayuda a revisar si la granularidad sigue siendo aproximadamente una fila por planeta.

---

## 4. Construcción de `dim_host_full`

Se creó la dimensión `dim_host_full` con una fila por `hostname`. Para consolidar los valores por host se usó `GROUP BY hostname` y agregaciones `MAX()` sobre tres columnas: `sy_dist`, `ra` y `dec`.

```python
con.execute("DROP TABLE IF EXISTS dim_host_full")

con.execute("""
CREATE TABLE dim_host_full AS
SELECT
  hostname,
  MAX(sy_dist) AS sy_dist,
  MAX(ra) AS ra,
  MAX(dec) AS dec
FROM silver_planet
GROUP BY hostname
""")
```

---

## 5. Validación de cardinalidad de `dim_host_full`

```python
con.sql("""
SELECT
  COUNT(*) AS n_rows,
  COUNT(DISTINCT hostname) AS n_keys
FROM dim_host_full
""").show()
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

**Interpretación:**  
Si `n_rows = n_keys`, entonces `dim_host_full` tiene una sola fila por `hostname`. Esto significa que la dimensión puede usarse en JOINs sin multiplicar accidentalmente las filas de la tabla de hechos.

---

## 6. Construcción de `fact_planet`

Se creó la tabla `fact_planet` desde `silver_planet`, conservando el grano de una fila por planeta.

```python
con.execute("DROP TABLE IF EXISTS fact_planet")

con.execute("""
CREATE TABLE fact_planet AS
SELECT DISTINCT
  pl_name,
  hostname,
  discoverymethod,
  disc_year,
  pl_orbper,
  pl_rade,
  pl_bmasse,
  pl_eqt
FROM silver_planet
""")
```

---

## 7. Validación de JOIN sano

```python
n_fact = con.execute("""
SELECT COUNT(*) FROM fact_planet
""").fetchone()[0]

n_join = con.execute("""
SELECT COUNT(*)
FROM fact_planet f
JOIN dim_host_full h
  ON f.hostname = h.hostname
""").fetchone()[0]

print("n_fact:", n_fact)
print("n_join:", n_join)
```

**Output:**

```text
n_fact: 6286
n_join: 6286
```

**Interpretación:**  
Un JOIN sano no debe inflar filas. Si `n_fact` y `n_join` son iguales, entonces la unión entre `fact_planet` y `dim_host_full` mantiene la cardinalidad esperada.