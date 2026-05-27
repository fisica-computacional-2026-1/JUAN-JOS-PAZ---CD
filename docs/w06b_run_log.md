# W06B — Run Log

## 1. Comando ejecutado

```bash
python -m src.pipeline.w06b_runner
```

## 2. Verificación inicial

Antes de ejecutar el runner se verificó que existieran los archivos necesarios:

```python
from pathlib import Path
import os

PROJECT_ROOT = Path(r"C:\Users\USUARIO WINDOWS\CODIGOS\PAZ CD").resolve()
os.chdir(PROJECT_ROOT)

print("cwd:", os.getcwd())

assert Path("data/raw/pscomppars.csv").exists(), "Falta data/raw/pscomppars.csv"
assert Path("src/pipeline/w06_pipeline.py").exists(), "Falta src/pipeline/w06_pipeline.py"
assert Path("src/pipeline/w06b_runner.py").exists(), "Falta src/pipeline/w06b_runner.py"

print("OK ✅")
```

**Output:**

```text
cwd: C:\Users\USUARIO WINDOWS\CODIGOS\PAZ CD
OK ✅
```

---

## 3. Ejecución del runner

```python
import subprocess, sys

cmd = [sys.executable, "-m", "src.pipeline.w06b_runner"]

print("Running:", " ".join(cmd))

res = subprocess.run(cmd, capture_output=True, text=True)

print("STDOUT:\n", res.stdout)

if res.returncode != 0:
    print("STDERR:\n", res.stderr)

    cmd2 = [sys.executable, "src/pipeline/w06b_runner.py"]
    print("\nFallback:", " ".join(cmd2))

    res2 = subprocess.run(cmd2, capture_output=True, text=True)

    print("STDOUT:\n", res2.stdout)

    if res2.returncode != 0:
        print("STDERR:\n", res2.stderr)
        raise RuntimeError("Runner failed. Copia el stderr en tu run_log.")
```

**STDOUT:**

```text
Running: c:\Users\USUARIO WINDOWS\CODIGOS\PAZ CD\.venv\Scripts\python.exe -m src.pipeline.w06b_runner
STDOUT:
 W06B runner iniciado
PROJECT_ROOT: C:\Users\USUARIO WINDOWS\CODIGOS\PAZ CD
Artifacts generados:
- C:\Users\USUARIO WINDOWS\CODIGOS\PAZ CD\artifacts\w06b_run_report.json
- C:\Users\USUARIO WINDOWS\CODIGOS\PAZ CD\artifacts\w06b_stage_timings.csv
Stage timings:
- bronze: 0.210315 s
- silver: 0.135662 s
- dims: 0.060935 s
- facts: 0.083387 s
- gold: 0.018404 s
- export: 0.022433 s
Checks:
- n_fact_sk: 6286
- orphan_rows: 0
- dim_host_rows: 4705
- dim_host_keys: 4705
W06B runner finalizado correctamente
```

---

## 4. Artifacts generados

Se verificó que el runner generara archivos con prefijo `w06b_` en la carpeta `artifacts/`.

```python
from pathlib import Path

sorted([p.name for p in Path("artifacts").glob("w06b_*")])
```

**Output:**

```text
['w06b_run_report.json', 'w06b_stage_timings.csv']
```

---

## 5. Lectura del reporte de tiempos

```python
import json
from pathlib import Path

report = json.loads(Path("artifacts/w06b_run_report.json").read_text(encoding="utf-8"))

[(s["mode"], s["seconds"]) for s in report["stages"]]
```

**Output:**

```text
[('bronze', 0.210315),
 ('silver', 0.135662),
 ('dims', 0.060935),
 ('facts', 0.083387),
 ('gold', 0.018404),
 ('export', 0.022433)]
```

---

## 6. Interpretación: etapa más lenta

La etapa más lenta fue la que presentó el mayor valor en segundos dentro de `artifacts/w06b_run_report.json`. Esta etapa representa el mayor costo del pipeline durante la ejecución local.

Una posible causa es que esa etapa realiza más trabajo de lectura, escritura, creación de tablas, joins o exportación de archivos. Los tiempos también pueden variar entre ejecuciones por el uso de caché, la carga del sistema y otros procesos activos.

---

## 7. Comparación de dos ejecuciones

Se ejecutó el runner dos veces para comparar tiempos. Los resultados pueden cambiar entre corridas porque el entorno local no es completamente determinista.

Si la segunda ejecución fue más rápida, probablemente parte de los datos o archivos ya estaban en caché. Si fue más lenta, puede deberse a procesos externos abiertos, mayor carga de CPU/disco o diferencias normales del sistema operativo.