# Lab 4: Database-Driven Feature Table

## Project Overview

This project uses SQL and Python to analyze a relational SQLite database from the TCGA Lung Adenocarcinoma (LUAD) cohort.

The goals are to:

1. Explore the database schema and table relationships.
2. Calculate mutation counts for TP53, KRAS, EGFR, STK11, and KEAP1.
3. Summarize patients by tissue source site and stage.
4. Build a patient-level feature table.
5. Document and handle missing data.

## Database

The course-provided database contains:

- 566 patients
- 566 samples
- 200,789 mutation records
- 17,756 genes

The database is not included in the submission ZIP or intended for upload to GitHub.

## Project Files

| File | Description |
|---|---|
| queries.sql | SQL queries for the analysis |
| build_feature_table.py | Python analysis and validation script |
| feature_table.tsv | Final patient-level feature table |
| site_stage_counts.tsv | Patient counts by site and stage |
| row_count_checks.txt | Validation results |
| schema.md | Database schema documentation |
| data_dictionary.md | Feature-table variable definitions |
| AI_USAGE.md | AI assistance documentation |

## Requirements

- Python 3
- pandas
- SQLite

## Reproducing the Analysis

1. Obtain the course-provided `cohort.db` from the course repo (`data/raw/lab4-cbioportal-luad/cohort.db`).
2. Place `cohort.db`, `queries.sql`, and `build_feature_table.py` in the same directory.
3. Install pandas if necessary:

   `pip install pandas`

4. Run:

   `python build_feature_table.py cohort.db`

## Expected Results

The final feature table contains 566 rows and 11 columns. The script writes `feature_table.tsv`, `site_stage_counts.tsv` and `row_count_checks.txt` next to itself, and stops with an error if any check fails.

The analysis uses LEFT JOINs to preserve patients, a CROSS JOIN to create patient-gene combinations, and pandas to reshape the gene counts into wide format.

## Queries and Row Counts

The schema, keys, grain and table relationships are in [`schema.md`](schema.md). All queries are in `queries.sql`. The expected and actual row counts below come from `row_count_checks.txt`.

| Query | One row is... | Expected | Got | Why |
|---|---|---|---|---|
| `q1_gene_counts` | one patient and one gene | 2,830 | 2,830 | 566 patients x 5 genes. Zeros are kept because the gene and Silent filters are in the `ON` clause of the `LEFT JOIN` |
| `q2_site_stage_counts` | one tissue source site and stage that occurs | 142 | 142 | distinct site and stage pairs, counted separately in pandas. Patients with no stage are kept as `Missing`, and the counts add up to 566 |
| `q3_patient_metadata` | one patient | 566 | 566 | patients `LEFT JOIN` samples is one-to-one (checked in the script) |

`q1_pitfall_filter_in_where` is the same query as Query 1 with the filters moved to `WHERE`. It returns only 700 rows instead of 2,830, because every patient-gene pair with no protein-altering mutation disappears. This is why optional-side filters belong in `ON`.

## Patient Counts Before and After Joins

| Step | Patients |
|---|---|
| `patients` table, before any join | 566 |
| after `patients` LEFT JOIN `samples` LEFT JOIN `mutations` (Query 3) | 566 |
| gene-count table after the long-to-wide reshape | 566 |
| final feature table | 566 |

## Missing Data

| Type of missing data | How many patients | What was done |
|---|---|---|
| missing `sex` | 52 | kept as `NA` |
| missing `age_at_diagnosis` | 71 | kept as `NA` |
| missing `stage` | 54 | kept as `NA` in the feature table, and shown as a `Missing` group in Query 2 |
| no protein-altering mutation in a gene (tumor has mutation records) | e.g. 275 for TP53 | `0`, because the tumor has records and none qualifies |
| tumor with no mutation records at all | 4 | `NA` in all five gene columns, because "no mutation found" cannot be told apart from "not called" |

Nobody was dropped, and no value was filled in or replaced with 0 without being listed above. See [`data_dictionary.md`](data_dictionary.md) for every column, its units and its source table.
