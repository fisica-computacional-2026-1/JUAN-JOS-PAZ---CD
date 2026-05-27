# W05B — Gold Report

## 1. Gold output: `gold_by_discoverymethod`

Esta vista resume los planetas por método de descubrimiento. Incluye el número de planetas, radio promedio, masa promedio y rango de años de descubrimiento.

```sql
SELECT *
FROM gold_by_discoverymethod
LIMIT 10;
```

**Output:**

```text
┌───────────────────────────────┬───────────┬────────────┬──────────┬────────────┬───────────┐
│        discoverymethod        │ n_planets │ avg_radius │ avg_mass │ first_year │ last_year │
│            varchar            │   int64   │   double   │  double  │   int32    │   int32   │
├───────────────────────────────┼───────────┼────────────┼──────────┼────────────┼───────────┤
│ Transit                       │      4650 │       4.34 │   120.78 │       2002 │      2026 │
│ Radial Velocity               │      1181 │       9.76 │  1029.24 │       1995 │      2026 │
│ Microlensing                  │       278 │       9.98 │   816.13 │       2004 │      2026 │
│ Imaging                       │        93 │      13.66 │  4411.49 │       2004 │      2026 │
│ Transit Timing Variations     │        41 │       6.46 │   473.89 │       2011 │      2026 │
│ Eclipse Timing Variations     │        17 │      12.89 │  2102.72 │       2009 │      2023 │
│ Orbital Brightness Modulation │         9 │       9.65 │   350.32 │       2011 │      2021 │
│ Pulsar Timing                 │         8 │       5.41 │   278.16 │       1992 │      2024 │
│ Astrometry                    │         6 │      12.45 │  4673.61 │       2013 │      2025 │
│ Pulsation Timing Variations   │         2 │      12.75 │  2383.73 │       2007 │      2016 │
├───────────────────────────────┴───────────┴────────────┴──────────┴────────────┴───────────┤
│ 10 rows                                                                          6 columns │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Interpretación científica:**  
Esta tabla permite comparar qué métodos han detectado más planetas y qué tipo de planetas tienden a encontrar. Por ejemplo, métodos como tránsito suelen producir muchos descubrimientos, mientras que métodos como imagen directa pueden estar asociados a planetas más grandes o masivos.

---

## 2. Gold output: `gold_by_host`

Esta vista resume los planetas por sistema anfitrión. Incluye número de planetas por `hostname`, radio promedio, masa promedio y años de descubrimiento.

```sql
SELECT *
FROM gold_by_host
LIMIT 10;
```

**Output:**

```text
┌────────────┬───────────┬────────────┬──────────┬────────────┬───────────┐
│  hostname  │ n_planets │ avg_radius │ avg_mass │ first_year │ last_year │
│  varchar   │   int64   │   double   │  double  │   int32    │   int32   │
├────────────┼───────────┼────────────┼──────────┼────────────┼───────────┤
│ KOI-351    │         8 │        3.9 │    31.15 │       2013 │      2017 │
│ TRAPPIST-1 │         7 │       0.98 │     0.92 │       2016 │      2017 │
│ K2-138     │         6 │       2.58 │     6.04 │       2017 │      2021 │
│ HD 191939  │         6 │       6.59 │   176.97 │       2020 │      2022 │
│ HD 34445   │         6 │       8.86 │    86.69 │       2009 │      2017 │
│ Kepler-20  │         6 │       2.29 │     9.39 │       2011 │      2016 │
│ HD 219134  │         6 │       3.67 │    25.24 │       2015 │      2015 │
│ TOI-1136   │         6 │       3.05 │     6.59 │       2022 │      2022 │
│ TOI-178    │         6 │       2.22 │     4.05 │       2021 │      2021 │
│ Kepler-11  │         6 │       2.97 │     7.85 │       2010 │      2010 │
├────────────┴───────────┴────────────┴──────────┴────────────┴───────────┤
│ 10 rows                                                       6 columns │
└─────────────────────────────────────────────────────────────────────────┘
```

**Interpretación científica:**  
Esta tabla permite identificar sistemas con varios planetas confirmados. Los sistemas con mayor `n_planets` son útiles para estudiar arquitecturas planetarias múltiples y comparar propiedades promedio entre sistemas.