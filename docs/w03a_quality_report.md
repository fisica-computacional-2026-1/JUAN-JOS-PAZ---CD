# W03A — Quality Report

## 1. TU TURNO 1 — Nulos en 12 columnas clave

Se construyó un reporte de nulos para 12 columnas seleccionadas del dataset `raw_ps`. Las columnas elegidas combinan identificadores, información de descubrimiento, propiedades físicas del planeta, distancia, coordenadas y temperatura estelar.

```python
picked = [
  "pl_name", "hostname", "discoverymethod", "disc_year",
  "pl_orbper", "pl_rade", "pl_bmasse", "pl_eqt",
  "sy_dist", "ra", "dec", "st_teff"
]

parts = [
  f"SELECT '{c}' AS col, COUNT(*) - COUNT({c}) AS nulls FROM raw_ps"
  for c in picked
]

query = " UNION ALL ".join(parts) + " ORDER BY nulls DESC, col ASC"

quality_df = con.sql(query).df()

quality_df
```

**Output:**


```text
c
col	nulls
0	pl_eqt	1601
1	pl_orbper	340
2	st_teff	294
3	pl_rade	50
4	pl_bmasse	31
5	sy_dist	27
6	disc_year	1
7	dec	0
8	discoverymethod	0
9	hostname	0
10	pl_name	0
11	ra	0

```

## 2. Materialización del reporte

El reporte de calidad se guardó como tabla DuckDB llamada `quality_w03a` y también se exportó como archivo CSV en la carpeta `artifacts`.

```python
con.register("quality_df_view", quality_df)

con.execute("""
CREATE OR REPLACE TABLE quality_w03a AS
SELECT * FROM quality_df_view
""")

print("Tabla quality_w03a creada en DuckDB")
```

```python
csv_path = ART_DIR / "quality_w03a.csv"

quality_df.to_csv(csv_path, index=False, encoding="utf-8")

print(f"CSV guardado en: {csv_path}")
```

## 3. TU TURNO 2 — Check de rango para `pl_orbper`

Se realizó un check de rango sobre `pl_orbper`, que representa el período orbital del planeta. Como regla mínima, se considera inválido un período orbital menor o igual a cero.

```python
query = """
SELECT
  COUNT(*) AS n_bad_pl_orbper
FROM raw_ps
WHERE pl_orbper IS NOT NULL
  AND pl_orbper <= 0
"""

range_df = con.sql(query).df()

range_df
```

**Output:**


```text

n_bad_pl_orbper
0	0

```

## 4. Interpretación

El reporte de nulos permite identificar qué columnas están más completas y cuáles requieren mayor cuidado antes de construir una capa Silver. Las columnas identificadoras como `pl_name` y `hostname` deberían mantenerse completas porque son claves para trazabilidad y joins.

El check de rango sobre `pl_orbper` valida que los períodos orbitales reportados sean positivos. Si el resultado es `0`, no se detectan períodos orbitales inválidos bajo esta regla; si aparece un valor mayor que cero, esos registros deben revisarse antes de usarse en análisis físico.



---

# TU TURNO 3 — Materialización de reporte de calidad

## 1. Objetivo

Se materializó un reporte de calidad llamado `quality_w03a` con tres checks mínimos:

1. Nulos en `pl_name`.
2. Nulos en `hostname`.
3. Valores inválidos en `pl_orbper`.

Los dos primeros checks son de completitud porque `pl_name` y `hostname` son columnas necesarias para identificar planetas y sistemas. El tercer check es de validez porque el período orbital (`pl_orbper`) debe ser positivo cuando está presente.

---

## 2. Query usado

```python
from datetime import datetime, timezone

run_ts = datetime.now(timezone.utc).isoformat()

con.execute("DROP TABLE IF EXISTS quality_w03a")

sql = f"""
CREATE TABLE quality_w03a AS

SELECT
  {sql_quote(run_ts)} AS run_ts,
  'nulls_pl_name' AS check_name,
  'completeness' AS check_type,
  (COUNT(*) - COUNT(pl_name))::BIGINT AS metric_value
FROM raw_ps

UNION ALL

SELECT
  {sql_quote(run_ts)} AS run_ts,
  'nulls_hostname' AS check_name,
  'completeness' AS check_type,
  (COUNT(*) - COUNT(hostname))::BIGINT AS metric_value
FROM raw_ps

UNION ALL

SELECT
  {sql_quote(run_ts)} AS run_ts,
  'bad_pl_orbper' AS check_name,
  'validity_range' AS check_type,
  SUM(CASE WHEN pl_orbper IS NOT NULL AND pl_orbper <= 0 THEN 1 ELSE 0 END)::BIGINT AS metric_value
FROM raw_ps
"""

con.execute(sql)

con.sql("SELECT * FROM quality_w03a").show()
```

---

## 3. Explicación detallada del query

La tabla `quality_w03a` se construyó con `CREATE TABLE ... AS`, usando tres consultas unidas mediante `UNION ALL`. Cada consulta devuelve las mismas cuatro columnas: `run_ts`, `check_name`, `check_type` y `metric_value`.

La columna `run_ts` registra la fecha y hora de ejecución del reporte. La columna `check_name` identifica el nombre del check aplicado. La columna `check_type` clasifica el tipo de validación, por ejemplo `completeness` o `validity_range`. Finalmente, `metric_value` guarda el resultado numérico del check.

Para los checks de nulos se usó la expresión `COUNT(*) - COUNT(columna)`, ya que `COUNT(*)` cuenta todas las filas y `COUNT(columna)` ignora los valores nulos. Para el check de rango se usó `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`, contando los casos donde `pl_orbper` no es nulo y además es menor o igual a cero.

---

## 4. Output de `quality_w03a`


```text
┌──────────────────────────────────┬────────────────┬────────────────┬──────────────┐
│              run_ts              │   check_name   │   check_type   │ metric_value │
│             varchar              │    varchar     │    varchar     │    int64     │
├──────────────────────────────────┼────────────────┼────────────────┼──────────────┤
│ 2026-05-27T17:49:17.876411+00:00 │ nulls_pl_name  │ completeness   │            0 │
│ 2026-05-27T17:49:17.876411+00:00 │ nulls_hostname │ completeness   │            0 │
│ 2026-05-27T17:49:17.876411+00:00 │ bad_pl_orbper  │ validity_range │            0 │
└──────────────────────────────────┴────────────────┴────────────────┴──────────────┘
```

---

## 5. Exportación a CSV

```python
ART_DIR.mkdir(parents=True, exist_ok=True)

out_csv = ART_DIR / f"w03a_quality_{run_ts.replace(':','-')}.csv"

con.execute(
    f"""
    COPY (SELECT * FROM quality_w03a)
    TO {sql_quote(str(out_csv))}
    WITH (HEADER, DELIMITER ',')
    """
)

print("Exporté:", out_csv)
```

El archivo fue exportado a la carpeta `artifacts/` como evidencia reproducible del reporte de calidad.