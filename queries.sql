-- name: q1_gene_counts
-- One row per patient and target gene. Expected rows: 566 patients x 5 genes = 2,830.
-- The gene and Silent filters are in the ON clause (not WHERE) so patients with no
-- matching mutation stay in the result with a count of 0.
WITH target_genes(gene_symbol) AS (
    VALUES
        ('TP53'),
        ('KRAS'),
        ('EGFR'),
        ('STK11'),
        ('KEAP1')
)
SELECT
    p.patient_id,
    g.gene_symbol,
    COUNT(m.mutation_id) AS n_protein_altering
FROM patients AS p
CROSS JOIN target_genes AS g
LEFT JOIN samples AS s
    ON p.patient_id = s.patient_id
LEFT JOIN mutations AS m
    ON s.sample_id = m.sample_id
    AND m.gene_symbol = g.gene_symbol
    AND m.variant_classification <> 'Silent'
GROUP BY
    p.patient_id,
    g.gene_symbol
ORDER BY
    p.patient_id,
    g.gene_symbol;


-- name: q1_pitfall_filter_in_where
-- Incorrect example, kept for comparison only: filtering in WHERE turns the LEFT JOIN
-- into an inner join, so every patient-gene pair with no mutation disappears.
WITH target_genes(gene_symbol) AS (
    VALUES
        ('TP53'),
        ('KRAS'),
        ('EGFR'),
        ('STK11'),
        ('KEAP1')
)
SELECT
    p.patient_id,
    g.gene_symbol,
    COUNT(m.mutation_id) AS n_protein_altering
FROM patients AS p
CROSS JOIN target_genes AS g
LEFT JOIN samples AS s
    ON p.patient_id = s.patient_id
LEFT JOIN mutations AS m
    ON s.sample_id = m.sample_id
WHERE
    m.gene_symbol = g.gene_symbol
    AND m.variant_classification <> 'Silent'
GROUP BY
    p.patient_id,
    g.gene_symbol;


-- name: q2_site_stage_counts
-- Number of patients by tissue source site and stage. Each patient is counted once, and
-- patients with no recorded stage are kept as 'Missing'. Expected rows: the distinct
-- (site, stage) pairs in the data (counted independently in the Python script).
SELECT
    s.tissue_source_site,
    COALESCE(p.stage, 'Missing') AS stage,
    COUNT(DISTINCT p.patient_id) AS n_patients
FROM patients AS p
LEFT JOIN samples AS s
    ON p.patient_id = s.patient_id
GROUP BY
    s.tissue_source_site,
    COALESCE(p.stage, 'Missing')
ORDER BY
    s.tissue_source_site,
    stage;


-- name: q3_patient_metadata
-- One row per patient with clinical and sample information. Expected rows: 566.
-- n_mutation_calls counts ALL mutation rows (Silent included); it is only used to spot
-- tumors with no mutation records and is dropped before the final table is written.
SELECT
    p.patient_id,
    p.sex,
    p.age_at_diagnosis,
    p.stage,
    s.tissue_source_site,
    s.tmb_nonsynonymous,
    COUNT(m.mutation_id) AS n_mutation_calls
FROM patients AS p
LEFT JOIN samples AS s
    ON p.patient_id = s.patient_id
LEFT JOIN mutations AS m
    ON s.sample_id = m.sample_id
GROUP BY
    p.patient_id,
    p.sex,
    p.age_at_diagnosis,
    p.stage,
    s.tissue_source_site,
    s.tmb_nonsynonymous
ORDER BY
    p.patient_id;
