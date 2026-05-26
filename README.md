# JUAN-JOS-PAZ---CD
Notebooks, entregables de la materia Ciencia de Datos

estructura

ing-cd-exoplanets/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── raw/
│   │   └── pscomppars.csv
│   ├── silver/
│   │   └── pscomppars_silver.parquet
│   ├── gold/
│   │   ├── gold_exoplanets_by_year.parquet
│   │   ├── gold_exoplanets_by_method.parquet
│   │   └── gold_exoplanets_by_facility.parquet
│   └── exoplanets.duckdb
│
├── notebooks/
│   ├── 01_exploracion_inicial.ipynb
│   ├── 02_profiling_pscomppars.ipynb
│   ├── 03_sql_basico_duckdb.ipynb
│   ├── 04_modelo_relacional.ipynb
│   ├── 05_checks_calidad.ipynb
│   ├── 06_raw_to_silver.ipynb
│   ├── 07_silver_to_gold.ipynb
│   └── 08_demo_final.ipynb
│
├── src/
│   ├── ingest/
│   │   └── download_exoplanets.py
│   │
│   ├── pipelines/
│   │   ├── raw_to_silver.py
│   │   └── silver_to_gold.py
│   │
│   ├── quality/
│   │   └── checks.py
│   │
│   ├── sql/
│   │   ├── create_tables.sql
│   │   ├── load_raw.sql
│   │   ├── h2_queries.sql
│   │   └── gold_queries.sql
│   │
│   └── utils/
│       └── paths.py
│
├── docs/
│   ├── bitacora_tecnica.md
│   ├── data_contract_v1.md
│   ├── data_contract_v2.md
│   ├── preguntas_ciencia_negocio.md
│   ├── modelo_relacional.md
│   ├── changelog_schema.md
│   └── informe_tecnico.md
│
└── artifacts/
    ├── figures/
    ├── reports/
    └── evidence/
