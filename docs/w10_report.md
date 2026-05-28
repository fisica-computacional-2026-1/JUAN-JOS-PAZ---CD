# W10 — Reporte de particionamiento y pruning

## 1. Objetivo

El objetivo de W10 fue particionar datos en formato Parquet usando la columna `disc_era`, verificar el número de archivos generados, resumir los datos por partición y demostrar partition pruning mediante `EXPLAIN ANALYZE`.

---

## 2. Evidencia de particionamiento

Se exportó una versión particionada de la tabla Silver en formato Parquet. La partición se hizo usando la columna `disc_era`.

```python
COPY (
  SELECT
    *,
    CASE
      WHEN disc_year_int IS NULL THEN 'unknown'
      WHEN disc_year_int < 2000 THEN 'pre_2000'
      WHEN disc_year_int BETWEEN 2000 AND 2009 THEN '2000s'
      WHEN disc_year_int BETWEEN 2010 AND 2019 THEN '2010s'
      WHEN disc_year_int >= 2020 THEN '2020s'
      ELSE 'unknown'
    END AS disc_era
  FROM silver_planet_v3
)
TO 'data/partitioned/silver_v3_partitioned'
(FORMAT PARQUET, PARTITION_BY (disc_era), OVERWRITE_OR_IGNORE TRUE);
```

**Output:**

```text
Particionamiento completado ✅
Ruta: C:/Users/USUARIO WINDOWS/CODIGOS/PAZ CD/data/partitioned/silver_v3_partitioned
```

---

## 3. Número de archivos por partición

Se inspeccionaron los directorios creados por Hive partitioning.

**Output:**

```text
Particiones creadas: 5
--------------------------------------------------
disc_era=2000s                 1 archivo(s) 27.8 KB
disc_era=2010s                 1 archivo(s) 215.5 KB
disc_era=2020s                 1 archivo(s) 142.8 KB
disc_era=pre_2000              1 archivo(s) 4.8 KB
disc_era=unknown               1 archivo(s) 2.0 KB
```

Cada carpeta tiene el formato `disc_era=<valor>`. Esto permite que DuckDB lea solo las particiones necesarias cuando se filtra por `disc_era`.

---

## 4. Resumen por partición

```sql
SELECT
  disc_era,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 2) AS avg_radius,
  ROUND(AVG(pl_bmasse), 2) AS avg_mass,
  MIN(disc_year_int) AS first_year,
  MAX(disc_year_int) AS last_year
FROM read_parquet('data/partitioned/silver_v3_partitioned/**/*.parquet', hive_partitioning=true)
GROUP BY disc_era
ORDER BY disc_era;
```

**Output:**

```text
┌──────────┬───────────┬────────────┬──────────┐
│ disc_era │ n_planets │ avg_radius │ avg_mass │
│ varchar  │   int64   │   double   │  double  │
├──────────┼───────────┼────────────┼──────────┤
│ 2000s    │       378 │      12.33 │  1145.78 │
│ 2010s    │      3681 │       4.89 │   268.55 │
│ 2020s    │      2196 │       6.06 │   476.05 │
│ pre_2000 │        30 │      12.18 │  1075.68 │
│ unknown  │         1 │       2.86 │      5.0 │
└──────────┴───────────┴────────────┴──────────┘
```

---

## 5. Evidencia de pruning

Se usó `EXPLAIN ANALYZE` para verificar que DuckDB aplique pruning al filtrar por una partición específica.

```sql
EXPLAIN ANALYZE
SELECT
  disc_era,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 2) AS avg_radius
FROM read_parquet('data/partitioned/silver_v3_partitioned/**/*.parquet', hive_partitioning=true)
WHERE disc_era = '2020s'
GROUP BY disc_era;
```

**Output resumido del plan:**

```text
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
 EXPLAIN ANALYZE SELECT   disc_era,   COUNT(*) AS n_planets,   ROUND(AVG(pl_rade), 2) AS avg_radius FROM read_parquet('C:/Users/USUARIO WINDOWS/CODIGOS/PAZ CD/data/partitioned/silver_v3_partitioned/**/*.parquet', hive_partitioning=true) WHERE disc_era = '2020s' GROUP BY disc_era 
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0164s             ││
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
│         PROJECTION        │
│    ────────────────────   │
│          disc_era         │
│         n_planets         │
...
│          (0.00s)          │
└───────────────────────────┘

Guardado en: C:\Users\USUARIO WINDOWS\CODIGOS\PAZ CD\artifacts\w10b_explain_analyze_pruning.txt
Output is truncated. View as a scrollable element or open in a text editor. Adjust cell output settings...
```

Archivo generado:

```text
artifacts/w10b_explain_analyze_pruning.txt
```

---

## 6. Explicación del filtro usado

El filtro usado fue:

```sql
WHERE disc_era = '2020s'
```

Este filtro permite demostrar partition pruning porque `disc_era` es la columna usada para particionar los archivos Parquet. Al activar `hive_partitioning=true`, DuckDB puede identificar las carpetas `disc_era=<valor>` y leer solamente la partición correspondiente a `2020s`, evitando escanear las demás.

---

## 7. Decisión de partición

Se decidió particionar por `disc_era` porque es una columna de baja cardinalidad y representa una dimensión temporal útil para consultas analíticas. Muchas preguntas sobre exoplanetas pueden agruparse o filtrarse por época de descubrimiento.

Además, particionar por era evita crear demasiadas carpetas. Esto reduce el riesgo de generar muchos archivos pequeños, algo que podría ocurrir si se particionara por columnas de alta cardinalidad como `hostname` o `pl_name`.

---

## 8. ¿Por qué `disc_era` sí o no?

`disc_era` sí es una buena candidata de partición cuando las consultas filtran por décadas o periodos históricos. En ese caso, el motor puede saltarse particiones completas y reducir lectura de archivos.

Sin embargo, `disc_era` no sería útil si la mayoría de consultas hacen análisis globales sin filtro temporal. En ese escenario, DuckDB tendría que leer todas las particiones y el beneficio del pruning sería bajo.

---

## 9. ¿Qué otra columna evaluaría?

Evaluaría `discoverymethod_canon`, porque también tiene cardinalidad relativamente baja y es común analizar exoplanetas por método de descubrimiento. Podría ser útil si muchas consultas filtran por métodos como `transit` o `radial_velocity`.

Aun así, no la usaría inmediatamente como partición compuesta con `disc_era`, porque la combinación podría crear muchas carpetas pequeñas. Primero revisaría la distribución de filas por método.

---

## 10. Riesgo de small files

El principal riesgo es crear demasiadas particiones con pocos datos. Esto genera muchos archivos pequeños y aumenta el overhead de planificación, apertura de archivos y lectura de metadatos.

En este caso, `disc_era` tiene pocas categorías, por lo que el riesgo es moderado. Pero si se particionara por `hostname`, habría miles de valores posibles y el diseño se volvería ineficiente.

---

## 11. Reflexión breve

El particionamiento ayuda cuando está alineado con los filtros más frecuentes de las consultas. No basta con partir los datos; la columna elegida debe reducir realmente el volumen leído.

En este ejercicio, `disc_era` permite demostrar pruning de forma clara porque DuckDB puede leer solo una era específica cuando aparece un filtro sobre esa columna.

---

## 12. ¿Cuándo particionar ayuda?

Particionar ayuda cuando el dataset es grande, la columna tiene baja o media cardinalidad y las consultas filtran frecuentemente por esa columna. También ayuda cuando las particiones tienen tamaños razonables y evitan leer datos innecesarios.

---

## 13. ¿Cuándo particionar empeora el diseño?

Particionar empeora cuando el dataset es pequeño, cuando la columna tiene demasiados valores distintos o cuando las consultas casi siempre necesitan leer todo el dataset. En esos casos, el costo de administrar muchos archivos puede superar el beneficio del pruning.