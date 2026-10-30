import sqlite3
import sys
from pathlib import Path
import pandas as pd

# Settings
BASE_DIR = Path(__file__).resolve().parent
GENES = ["TP53", "KRAS", "EGFR", "STK11", "KEAP1"]

QUERY_FILE = BASE_DIR / "queries.sql"

FEATURE_FILE = BASE_DIR / "feature_table.tsv"
SITE_FILE = BASE_DIR / "site_stage_counts.tsv"
CHECK_FILE = BASE_DIR / "row_count_checks.txt"

checks = []


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def log(message):
    print(message)
    checks.append(message)


def validate(label, expected, actual):
    passed = expected == actual
    status = "OK" if passed else "FAILED"

    log(
        f"{label}: expected {expected:,}, "
        f"got {actual:,} [{status}]"
    )

    if not passed:
        raise ValueError(f"{label} validation failed.")


def load_queries():
    queries = {}
    current_name = None
    current_sql = []

    for line in QUERY_FILE.read_text().splitlines():

        if line.startswith("-- name:"):

            if current_name:
                queries[current_name] = "\n".join(
                    current_sql
                ).strip()

            current_name = line.split(":", 1)[1].strip()
            current_sql = []

        elif current_name:
            current_sql.append(line)

    if current_name:
        queries[current_name] = "\n".join(
            current_sql
        ).strip()

    return queries


def run_query(connection, sql):
    return pd.read_sql_query(sql, connection)


# --------------------------------------------------
# Database checks
# --------------------------------------------------

def check_database(connection):

    patients = connection.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    samples = connection.execute(
        "SELECT COUNT(*) FROM samples"
    ).fetchone()[0]

    log("\nDATABASE CHECKS")

    validate("Patient count", 566, patients)
    validate("Sample count", 566, samples)

    sample_counts = run_query(connection, """
        SELECT patient_id, COUNT(*) AS sample_count
        FROM samples
        GROUP BY patient_id
    """)

    validate(
        "Patients represented in samples",
        patients,
        len(sample_counts)
    )

    if not (sample_counts["sample_count"] == 1).all():
        raise ValueError(
            "Some patients do not have exactly one sample."
        )

    return patients


# --------------------------------------------------
# Query 1: Gene mutation counts
# --------------------------------------------------

def get_gene_counts(connection, queries, n_patients):

    log("\nQUERY 1: GENE MUTATION COUNTS")

    counts = run_query(
        connection,
        queries["q1_gene_counts"]
    )

    validate(
        "Patient-gene combinations",
        n_patients * len(GENES),
        len(counts)
    )

    if counts.duplicated(
        ["patient_id", "gene_symbol"]
    ).any():
        raise ValueError(
            "Duplicate patient-gene combinations found."
        )

    incorrect = run_query(
        connection,
        queries["q1_pitfall_filter_in_where"]
    )

    log(
        f"Incorrect WHERE query returned "
        f"{len(incorrect):,} rows instead of "
        f"{len(counts):,}."
    )

    # Reshape from long to wide format using pandas
    wide = counts.pivot(
        index="patient_id",
        columns="gene_symbol",
        values="n_protein_altering"
    ).reindex(columns=GENES)

    wide.columns = [
        f"{gene}_protein_altering_count"
        for gene in GENES
    ]

    validate("Wide gene table", n_patients, len(wide))

    return wide


# --------------------------------------------------
# Query 2: Tissue source site and stage
# --------------------------------------------------

def get_site_stage_counts(connection, queries, n_patients):

    log("\nQUERY 2: SITE AND STAGE COUNTS")

    result = run_query(
        connection,
        queries["q2_site_stage_counts"]
    )

    patients = run_query(
        connection,
        "SELECT patient_id, stage FROM patients"
    )

    samples = run_query(
        connection,
        """
        SELECT patient_id, tissue_source_site
        FROM samples
        """
    )

    # Independently calculate expected group counts
    expected = patients.merge(
        samples,
        on="patient_id",
        how="left",
        validate="one_to_one"
    )

    expected["stage"] = expected["stage"].fillna("Missing")

    expected = (
        expected.groupby(
            ["tissue_source_site", "stage"],
            dropna=False
        )
        .agg(n_patients=("patient_id", "nunique"))
        .reset_index()
    )

    actual_sorted = result.sort_values(
        ["tissue_source_site", "stage"]
    ).reset_index(drop=True)

    expected_sorted = expected.sort_values(
        ["tissue_source_site", "stage"]
    ).reset_index(drop=True)

    pd.testing.assert_frame_equal(
        actual_sorted,
        expected_sorted,
        check_dtype=False
    )

    validate(
        "Site-stage groups",
        len(expected),
        len(result)
    )

    validate(
        "Patients counted",
        n_patients,
        int(result["n_patients"].sum())
    )

    result.to_csv(
        SITE_FILE,
        sep="\t",
        index=False
    )

    return result


# --------------------------------------------------
# Query 3: Patient metadata
# --------------------------------------------------

def get_metadata(connection, queries, n_patients):

    log("\nQUERY 3: PATIENT METADATA")

    metadata = run_query(
        connection,
        queries["q3_patient_metadata"]
    )

    validate(
        "Patient metadata rows",
        n_patients,
        len(metadata)
    )

    if not metadata["patient_id"].is_unique:
        raise ValueError(
            "Patient metadata contains duplicate IDs."
        )

    return metadata


# --------------------------------------------------
# Independently verify gene counts
# --------------------------------------------------

def verify_gene_counts(connection, wide):

    placeholders = ",".join(["?"] * len(GENES))

    raw = pd.read_sql_query(
        f"""
        SELECT s.patient_id, m.gene_symbol
        FROM mutations AS m
        JOIN samples AS s
            ON m.sample_id = s.sample_id
        WHERE m.variant_classification <> 'Silent'
          AND m.gene_symbol IN ({placeholders})
        """,
        connection,
        params=GENES
    )

    independent = (
        raw.groupby(["patient_id", "gene_symbol"])
        .size()
        .unstack(fill_value=0)
        .reindex(
            index=wide.index,
            columns=GENES,
            fill_value=0
        )
    )

    if not (
        independent.to_numpy() == wide.to_numpy()
    ).all():
        raise ValueError(
            "Independent pandas recount does not match SQL."
        )

    log(
        "Independent pandas mutation recount: all counts match."
    )


# --------------------------------------------------
# Build final feature table
# --------------------------------------------------

def build_feature_table(metadata, wide, n_patients):

    log("\nBUILDING FINAL FEATURE TABLE")

    table = metadata.merge(
        wide,
        left_on="patient_id",
        right_index=True,
        how="left",
        validate="one_to_one"
    )

    validate(
        "Final joined patient count",
        n_patients,
        len(table)
    )

    gene_columns = list(wide.columns)

    # No mutation records means gene counts are unknown
    no_calls = table["n_mutation_calls"] == 0

    table.loc[no_calls, gene_columns] = pd.NA

    table[gene_columns] = table[gene_columns].astype("Int64")

    log("\nMISSING DATA REPORT")

    clinical_columns = [
        "sex",
        "age_at_diagnosis",
        "stage",
        "tissue_source_site",
        "tmb_nonsynonymous"
    ]

    for column in clinical_columns:
        log(
            f"{column}: {table[column].isna().sum()} missing"
        )

    log(
        f"Patients with no mutation calls: {no_calls.sum()}"
    )

    for column in gene_columns:
        zeros = (table[column] == 0).sum()
        missing = table[column].isna().sum()

        log(
            f"{column}: {zeros} zeros; "
            f"{missing} missing"
        )

    final_columns = [
        "patient_id",
        "sex",
        "age_at_diagnosis",
        "stage",
        "tissue_source_site",
        "tmb_nonsynonymous"
    ] + gene_columns

    final = table[final_columns]

    final.to_csv(
        FEATURE_FILE,
        sep="\t",
        index=False,
        na_rep="NA"
    )

    saved = pd.read_csv(FEATURE_FILE, sep="\t")

    validate(
        "Final TSV rows",
        n_patients,
        len(saved)
    )

    if not saved["patient_id"].is_unique:
        raise ValueError(
            "Final feature table contains duplicate patient IDs."
        )

    log(
        f"FINAL TABLE: {saved.shape[0]} rows "
        f"x {saved.shape[1]} columns"
    )

    return final


# --------------------------------------------------
# Main workflow
# --------------------------------------------------

def main(database_path):

    queries = load_queries()

    required = [
        "q1_gene_counts",
        "q1_pitfall_filter_in_where",
        "q2_site_stage_counts",
        "q3_patient_metadata"
    ]

    for name in required:
        if name not in queries:
            raise ValueError(f"Missing SQL query: {name}")

    connection = sqlite3.connect(database_path)

    try:

        n_patients = check_database(connection)

        wide = get_gene_counts(
            connection,
            queries,
            n_patients
        )

        get_site_stage_counts(
            connection,
            queries,
            n_patients
        )

        metadata = get_metadata(
            connection,
            queries,
            n_patients
        )

        verify_gene_counts(connection, wide)

        build_feature_table(
            metadata,
            wide,
            n_patients
        )

        log("\nALL VALIDATION CHECKS PASSED.")

    finally:
        connection.close()

        CHECK_FILE.write_text(
            "\n".join(checks) + "\n"
        )


if __name__ == "__main__":

    database = (
        sys.argv[1]
        if len(sys.argv) > 1
        else str(BASE_DIR / "cohort.db")
    )

    main(database)
