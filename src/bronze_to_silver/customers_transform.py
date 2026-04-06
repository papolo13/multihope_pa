"""
BRONZE -> SILVER: Customers Transformation
Reads the Bronze Parquet layer, applies DQX data quality checks,
and writes clean records to Silver. Quarantined rows are logged and saved separately.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from src.utils.spark_session import create_spark_session
from pyspark.sql import functions as F
from databricks.labs.dqx.engine import DQEngineCore
from databricks.labs.dqx.rule import DQRule, DQRuleColSet
from databricks.labs.dqx.col_functions import is_not_null, is_not_null_and_not_empty

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parents[2]
BRONZE_INPUT = PROJECT_ROOT / "data" / "bronze" / "customers"
SILVER_OUTPUT = PROJECT_ROOT / "data" / "silver" / "customers"
QUARANTINE_OUTPUT = PROJECT_ROOT / "data" / "quarantine" / "customers"

def _build_checks() -> list[DQRule]:
    """Build DQX checks after SparkSession is available."""
    return [
        # Errors: rows failing these are quarantined and excluded from Silver
        DQRule(
            name="customer_id_not_null",
            criticality="error",
            check=is_not_null("customer_id"),
        ),
        DQRule(
            name="nombre_not_null_or_empty",
            criticality="error",
            check=is_not_null_and_not_empty("nombre"),
        ),
        DQRule(
            name="email_not_null_or_empty",
            criticality="error",
            check=is_not_null_and_not_empty("email"),
        ),
        # Warnings: flagged in quarantine log but rows still pass to Silver
        DQRule(
            name="identificacion_not_empty",
            criticality="warn",
            check=is_not_null_and_not_empty("identificacion"),
        ),
        DQRule(
            name="estado_not_null",
            criticality="warn",
            check=is_not_null("estado"),
        ),
    ]


def transform_customers() -> int:
    logger.info("=== BRONZE -> SILVER | customers ===")

    spark = create_spark_session("BRONZE_to_SILVER_customers")
    checks = _build_checks()

    logger.info(f"Reading Bronze layer from {BRONZE_INPUT}")
    df = spark.read.parquet(str(BRONZE_INPUT))

    logger.info("Applying transformations...")

    # Rename id_cliente -> customer_id (standardize to English)
    df = df.withColumnRenamed("id_cliente", "customer_id")

    # Trim all string columns and standardize email to lowercase
    df_clean = (
        df
        .select([
            F.trim(F.col(c)).alias(c) if t == "string" else F.col(c)
            for c, t in df.dtypes
        ])
        .dropDuplicates()
        .withColumn(
            "email",
            F.when(F.col("email").isNotNull(), F.lower(F.col("email"))),
        )
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_layer", F.lit("bronze"))
    )

    # ---------------------------------------------------------------------------
    # DQX validation
    # ---------------------------------------------------------------------------
    logger.info("Running DQX quality checks...")
    engine = DQEngineCore(spark) # type: ignore
    valid_df, quarantine_df = engine.apply_checks_and_split(df_clean, checks)

    quarantine_count = quarantine_df.count()
    valid_count = valid_df.count()
    logger.info(f"DQX results — valid: {valid_count}, quarantined: {quarantine_count}")

    if quarantine_count > 0:
        logger.warning(f"{quarantine_count} rows failed quality checks and were quarantined.")
        quarantine_df.write.mode("overwrite").option("compression", "snappy").parquet(
            str(QUARANTINE_OUTPUT)
        )
        logger.info(f"Quarantine layer written to {QUARANTINE_OUTPUT}")

    # ---------------------------------------------------------------------------
    # Write Silver
    # ---------------------------------------------------------------------------
    logger.info(f"Saving Silver layer to {SILVER_OUTPUT}")
    valid_df.write.parquet(
        str(SILVER_OUTPUT)
    )
    logger.info(f"Silver layer written successfully — {valid_count} records.")

    spark.stop()
    return valid_count


if __name__ == "__main__":
    transform_customers()
