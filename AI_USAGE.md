# AI Usage

## Tools

- **Claude Sonnet 5.5 :** Used through claude.ai to help with the project and review wording and documentation.
- **ChatGPT (GPT-6):** Used to help understand the database structure, write and organize the SQL queries and Python script, troubleshoot errors, and verify the feature table.

## What the AI helped with

- Looking at `cohort.db` to understand the tables, their relationships, and missing data.
- Writing the SQL queries in `queries.sql`, including the gene-count query, site-by-stage query, patient-metadata query, and an incorrect `WHERE` example to understand why filters on optional tables should go in the `ON` clause.
- Writing and organizing `build_feature_table.py` to run the queries, reshape the gene counts from long to wide using pandas, and check the results.
- Drafting the README, schema, and data dictionary documentation.
- Explaining SQL joins, database grain, missing data, and why patients without mutation records should be handled differently from patients with zero mutations.

The original course-provided `cohort.db` was used without making changes to it. It was not rebuilt from the cBioPortal download.

## AI interactions and troubleshooting

One issue I ran into was an `OperationalError: no such table: mutations` when checking the second patient in Google Colab. I asked ChatGPT what the error meant. It explained that the database path could be pointing to a different database file that did not contain the expected tables. I then checked the database paths and table names, found the correct database, and reran the query successfully.

I also used AI to understand why the incorrect `WHERE` version of the gene-count query returned fewer rows than expected. This helped me understand how filtering a table after a LEFT JOIN can remove patients who do not have matching mutation records.

## How the output was checked

1. **Row counts:** The expected number of rows for Query 1 was 566 patients multiplied by 5 genes, which equals 2,830 rows. The query returned 2,830 rows. Query 2 returned 142 groups, with the patient counts adding up to 566. Query 3 returned 566 rows, and the final feature table contained 566 patients.

2. **Independent recount:** The Python script recalculates the gene mutation counts directly from the `mutations` and `samples` tables using pandas. These results were compared with the SQL results to make sure the counts matched.

3. **Checking two patients against the original database:** I used SQL queries in Google Colab to look at the original mutation records and compared them with the final feature table.
   - `TCGA-78-7147`: The original records showed 3 EGFR mutations and 1 TP53 mutation. The feature table showed TP53 = 1, KRAS = 0, EGFR = 3, STK11 = 0, and KEAP1 = 0.
   - `TCGA-17-Z023`: The original records showed one TP53 nonsense mutation and one TP53 silent mutation. The feature table counted only 1, confirming that silent mutations were excluded.

4. **Checking the table structure:** The script checks that every patient has one sample, each patient-gene combination appears once, and `patient_id` is unique in the final feature table.

## A judgment call about missing data

There were 4 patients with no mutation records in the database. I used `NA` instead of `0` for their five gene mutation counts because having no mutation records does not necessarily mean that the tumors had zero mutations. Their tumor mutation burden is listed as 0.0, but that does not confirm that they had no mutations. Using zero could be another approach, but I chose `NA` to represent unavailable information.

AI was used as a support tool and aid throughout the project, I reviewed the code and results to make sure I understood what was done and how the final feature table was created.
