# Lab 4: Feature Table Data Dictionary

`feature_table.tsv` has 566 rows (one per patient) and 11 columns. It is tab-separated, and missing values are written as `NA`.

| Column | Meaning | Type | Units / values | Source table | Missing values |
|---|---|---|---|---|---|
| `patient_id` | TCGA patient barcode, unique per row | text | e.g. `TCGA-05-4244` | `patients.patient_id` | none |
| `sex` | Patient sex as recorded | text | `female`, `male` | `patients.sex` | 52 patients are `NA` (not recorded) |
| `age_at_diagnosis` | Age when the cancer was diagnosed | numeric | years | `patients.age_at_diagnosis` | 71 patients are `NA` (not recorded) |
| `stage` | Tumor stage as recorded | text | `I`, `IA`, `IB`, `II`, `IIA`, `IIB`, `IIIA`, `IIIB`, `IV` (kept as recorded, not merged) | `patients.stage` | 54 patients are `NA` (not recorded) |
| `tissue_source_site` | Name of the institution that supplied the tumor sample | text | 34 distinct institution names | `samples.tissue_source_site` | none |
| `tmb_nonsynonymous` | Tumor mutation burden (non-synonymous mutations) | numeric | mutations per megabase | `samples.tmb_nonsynonymous` | none. The 4 tumors with no mutation records show `0.0`, which comes from the same absent records, so treat it with caution |
| `TP53_protein_altering_count` | Protein-altering mutations in TP53 in the patient's tumor | integer | count, 0 or more | `mutations` (joined through `samples`) | `NA` for the 4 tumors with no mutation records |
| `KRAS_protein_altering_count` | Same, for KRAS | integer | count, 0 or more | `mutations` | same 4 patients are `NA` |
| `EGFR_protein_altering_count` | Same, for EGFR | integer | count, 0 or more | `mutations` | same 4 patients are `NA` |
| `STK11_protein_altering_count` | Same, for STK11 | integer | count, 0 or more | `mutations` | same 4 patients are `NA` |
| `KEAP1_protein_altering_count` | Same, for KEAP1 | integer | count, 0 or more | `mutations` | same 4 patients are `NA` |

## What the gene count columns count

Each count is the number of rows in `mutations` for the patient's tumor and that gene whose `variant_classification` is not `Silent`.

- **Counted (protein-altering):** `Missense_Mutation`, `Nonsense_Mutation`, `Splice_Site`, `Frame_Shift_Del`, `Frame_Shift_Ins`, `In_Frame_Del`, `In_Frame_Ins`, `Translation_Start_Site`, `Nonstop_Mutation`.
- **Excluded:** `Silent`.
- The database only contains coding-sequence and splice-site mutations (UTR, intron, flank and RNA variants were removed when it was built), so none of those are counted.
- The count is per mutation row. A patient with three different EGFR mutations has `EGFR_protein_altering_count = 3`; it is not a yes/no flag.

## Zero versus NA in the gene columns

- **`0`:** the tumor has mutation records, and none of them is a protein-altering mutation in that gene.
- **`NA`:** the tumor has no mutation records at all (4 patients: TCGA-64-1678, TCGA-69-8453, TCGA-78-7143, TCGA-86-A4D0). "No mutation found" cannot be told apart from "not called", so the count is unknown, not zero.

## Missing clinical values

`sex`, `age_at_diagnosis` and `stage` are kept as `NA` when not recorded. They were not filled in, guessed or dropped, so every patient stays in the table.
