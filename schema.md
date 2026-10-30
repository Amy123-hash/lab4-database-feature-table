# Lab 4: Database Schema

## Database Overview

The database contains four tables from the TCGA Lung Adenocarcinoma (LUAD) cohort.

| Table | Rows | Grain |
|---|---:|---|
| patients | 566 | One row per patient |
| samples | 566 | One row per tumor sample |
| mutations | 200,789 | One row per mutation record |
| genes | 17,756 | One row per gene |

## Patients

Primary key: `patient_id`

| Column | Type | Description |
|---|---|---|
| patient_id | TEXT | Unique patient identifier |
| sex | TEXT | Patient sex |
| age_at_diagnosis | REAL | Age at diagnosis |
| stage | TEXT | Clinical tumor stage |
| vital_status | TEXT | Patient vital status |
| followup_months | REAL | Follow-up duration in months |

## Samples

Primary key: `sample_id`

| Column | Type | Description |
|---|---|---|
| sample_id | TEXT | Unique sample identifier |
| patient_id | TEXT | Patient identifier |
| tissue_source_site | TEXT | Tissue source site |
| tmb_nonsynonymous | REAL | Nonsynonymous tumor mutation burden |
| aneuploidy_score | REAL | Aneuploidy score |
| msi_mantis_score | REAL | MSI MANTIS score |

## Mutations

Primary key: `mutation_id`

| Column | Type | Description |
|---|---|---|
| mutation_id | INTEGER | Unique mutation identifier |
| sample_id | TEXT | Sample identifier |
| gene_symbol | TEXT | Gene symbol |
| variant_classification | TEXT | Mutation classification |
| variant_type | TEXT | Mutation type |
| protein_change | TEXT | Protein-level change |
| chromosome | TEXT | Chromosome |
| start_pos | INTEGER | Mutation start position |
| end_pos | INTEGER | Mutation end position |
| t_ref_count | INTEGER | Reference read count |
| t_alt_count | INTEGER | Alternate read count |

## Genes

Primary key: `gene_symbol`

| Column | Type | Description |
|---|---|---|
| gene_symbol | TEXT | Unique gene symbol |
| entrez_gene_id | INTEGER | Entrez Gene identifier |
| chromosome | TEXT | Chromosome |

## Foreign Key Relationships

- `samples.patient_id` references `patients.patient_id`.
- `mutations.sample_id` references `samples.sample_id`.
- `mutations.gene_symbol` references `genes.gene_symbol`.

## How the tables relate (checked in the database)

- **patients to samples:** the schema allows one-to-many, but here it is one-to-one. All 566 patients have exactly one sample, and no sample points to a missing patient.
- **samples to mutations:** one-to-many. The 562 samples with mutations have about 357 mutation rows each on average (up to 2,602). 4 samples have no mutation rows at all.
- **mutations to genes:** many-to-one. Every mutation points to a gene that exists in `genes`, and one gene can have many mutation rows.
- So the path from patient to mutation is `patients` to `samples` to `mutations`. A patient can have several mutations in the same gene, which is why counts must be grouped to one row per patient and gene before reshaping to wide format.

## Join Strategy and Grain

LEFT JOINs preserve all patients when combining patient, sample, and mutation information.

A CROSS JOIN between 566 patients and five target genes creates 2,830 patient-gene combinations.

The final feature table has one row per patient. In this dataset, each patient has exactly one sample.
