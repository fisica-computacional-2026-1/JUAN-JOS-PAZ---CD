
from pathlib import Path
import time
import duckdb


def sql_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def run_pipeline(project_root: Path) -> dict:
    project_root = Path(project_root).resolve()

    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    artifacts_dir = project_root / "artifacts"

    raw_csv = raw_dir / "pscomppars.csv"
    db_path = data_dir / "exoplanets_w06b.duckdb"

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if not raw_csv.exists():
        raise FileNotFoundError(f"No encuentro {raw_csv}")

    con = duckdb.connect(str(db_path))

    stages = []

    def stage(name, fn):
        t0 = time.perf_counter()
        fn()
        seconds = round(time.perf_counter() - t0, 6)
        stages.append({"mode": name, "seconds": seconds})

    def bronze():
        con.execute(f"""
        CREATE OR REPLACE VIEW raw_ps AS
        SELECT * FROM read_csv_auto({sql_quote(str(raw_csv.resolve()))})
        """)

    def silver():
        con.execute("DROP TABLE IF EXISTS fact_planet_sk")
        con.execute("DROP TABLE IF EXISTS dim_host_sk")
        con.execute("DROP TABLE IF EXISTS fact_planet")
        con.execute("DROP TABLE IF EXISTS dim_host_full")
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
        """)

    def dims():
        con.execute("DROP TABLE IF EXISTS dim_host_full")

        con.execute("""
        CREATE TABLE dim_host_full AS
        SELECT
          hostname,
          MAX(sy_dist) AS sy_dist,
          MAX(ra) AS ra,
          MAX(dec) AS dec,
          MAX(st_teff) AS st_teff,
          MAX(st_rad) AS st_rad,
          MAX(st_mass) AS st_mass
        FROM silver_planet
        GROUP BY hostname
        """)

        con.execute("""
        CREATE TABLE dim_host_sk (
          host_id INTEGER PRIMARY KEY,
          hostname VARCHAR NOT NULL UNIQUE,
          sy_dist DOUBLE,
          ra DOUBLE,
          dec DOUBLE,
          st_teff DOUBLE,
          st_rad DOUBLE,
          st_mass DOUBLE
        )
        """)

        con.execute("""
        INSERT INTO dim_host_sk
        SELECT
          ROW_NUMBER() OVER (ORDER BY hostname) AS host_id,
          hostname,
          sy_dist,
          ra,
          dec,
          st_teff,
          st_rad,
          st_mass
        FROM dim_host_full
        """)

    def facts():
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

        con.execute("""
        CREATE TABLE fact_planet_sk (
          pl_name VARCHAR PRIMARY KEY,
          host_id INTEGER NOT NULL REFERENCES dim_host_sk(host_id),
          discoverymethod VARCHAR,
          disc_year INTEGER,
          pl_orbper DOUBLE,
          pl_rade DOUBLE,
          pl_bmasse DOUBLE,
          pl_eqt DOUBLE
        )
        """)

        con.execute("""
        INSERT INTO fact_planet_sk
        SELECT
          f.pl_name,
          d.host_id,
          f.discoverymethod,
          f.disc_year,
          f.pl_orbper,
          f.pl_rade,
          f.pl_bmasse,
          f.pl_eqt
        FROM fact_planet f
        JOIN dim_host_sk d
          ON f.hostname = d.hostname
        """)

    def gold():
        con.execute("DROP VIEW IF EXISTS gold_by_discoverymethod")
        con.execute("""
        CREATE VIEW gold_by_discoverymethod AS
        SELECT
          discoverymethod,
          COUNT(*) AS n_planets,
          ROUND(AVG(pl_rade), 2) AS avg_radius,
          ROUND(AVG(pl_bmasse), 2) AS avg_mass,
          MIN(disc_year) AS first_year,
          MAX(disc_year) AS last_year
        FROM fact_planet_sk
        WHERE discoverymethod IS NOT NULL
        GROUP BY discoverymethod
        ORDER BY n_planets DESC
        """)

        con.execute("DROP VIEW IF EXISTS gold_by_host")
        con.execute("""
        CREATE VIEW gold_by_host AS
        SELECT
          d.hostname,
          COUNT(*) AS n_planets,
          ROUND(AVG(f.pl_rade), 2) AS avg_radius,
          ROUND(AVG(f.pl_bmasse), 2) AS avg_mass,
          MIN(f.disc_year) AS first_year,
          MAX(f.disc_year) AS last_year
        FROM fact_planet_sk f
        JOIN dim_host_sk d
          ON f.host_id = d.host_id
        GROUP BY d.hostname
        ORDER BY n_planets DESC
        """)

    def export():
        out1 = artifacts_dir / "gold_by_discoverymethod.csv"
        out2 = artifacts_dir / "gold_by_host.csv"

        con.execute(f"COPY gold_by_discoverymethod TO {sql_quote(str(out1))} WITH (HEADER, DELIMITER ',')")
        con.execute(f"COPY gold_by_host TO {sql_quote(str(out2))} WITH (HEADER, DELIMITER ',')")

    stage("bronze", bronze)
    stage("silver", silver)
    stage("dims", dims)
    stage("facts", facts)
    stage("gold", gold)
    stage("export", export)

    n_fact = con.execute("SELECT COUNT(*) FROM fact_planet_sk").fetchone()[0]

    orphan_rows = con.execute("""
    SELECT COUNT(*)
    FROM fact_planet_sk f
    LEFT JOIN dim_host_sk d
      ON f.host_id = d.host_id
    WHERE d.host_id IS NULL
    """).fetchone()[0]

    n_dim, n_keys = con.execute("""
    SELECT COUNT(*) AS n_rows, COUNT(DISTINCT hostname) AS n_keys
    FROM dim_host_sk
    """).fetchone()

    con.close()

    return {
        "stages": stages,
        "checks": {
            "n_fact_sk": n_fact,
            "orphan_rows": orphan_rows,
            "dim_host_rows": n_dim,
            "dim_host_keys": n_keys
        }
    }
