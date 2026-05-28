# PAZ CD

Proyecto de ingeniería de datos aplicado al dataset de exoplanetas.  
El flujo principal trabaja desde datos Raw hasta capas Silver, Gold, reportes, evidencias y análisis de performance.

## Estructura del repositorio

```text
├── artifacts/         
│   ├── figures/
│   ├── gold_by_discoverymethod.csv
│   ├── gold_by_host.csv
│   ├── quality_w03a.csv
│   ├── w06b_run_report.json
│   ├── w06b_stage_timings.csv
│   ├── w10b_explain_analyze_pruning.txt
│   ├── w11_explain_critical_q1.txt
│   └── w11_explain_critical_q2.txt
├── docs/                     # Reportes, contratos y bitácora
│   ├── data_contract.md
│   ├── decisions_log.md
│   ├── w03_join_case.md
│   ├── w03_sql_practice.md
│   ├── w03a_quality_report.md
│   ├── w03b_silver_report.md
│   ├── w04a_perf_report.md
│   ├── w05a_evidence.md
│   ├── w05b_gold_report.md
│   ├── w06b_run_log.md
│   ├── w08_report.md
│   ├── w09_quality.md
│   ├── w09_report.md
│   ├── w10_report.md
│   └── w11_perf_report.md
├── Notebooks/                # Notebooks semanales
│   ├── W01.ipynb
│   ├── W02.ipynb
│   ├── W03.ipynb
│   ├── W04.ipynb
│   ├── W05.ipynb
│   ├── W06.ipynb
│   ├── W07B_student.ipynb
│   ├── W08_assignment_student.ipynb
│   ├── W09_assignment_student.ipynb
│   ├── W10_student.ipynb
│   └── W11_student.ipynb
├── src/                      # Código fuente ejecutable
│   ├── ingest/
│   │   └── download_exoplanets.py
│   ├── pipeline/
│   │   ├── W06_pipeline.py
│   │   └── w06b_runner.py
│   ├── pipelines/
│   │   ├── W06_pipeline.py
│   │   ├── W06b_runner.py
│   │   ├── W07_pipeline.py
│   │   └── W07b_runner.py
│   └── utils/
│       └── paths.py
├── .gitignore
├── README.md
└── requirements.txt

