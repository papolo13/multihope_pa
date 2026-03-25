"""
SILVER -> GOLD: Customers Aggregation
Reads the Silver layer and builds business-ready aggregates for reporting.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from src.utils.spark_session import create_spark_session
from pyspark.sql import functions as F

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parents[2]
SILVER_INPUT = PROJECT_ROOT / "data" / "silver" / "customers"
GOLD_OUTPUT = PROJECT_ROOT / "data" / "gold" / "customers_summary"


def aggregate_customers() -> int:
    logger.info("=== SILVER -> GOLD | customers_summary ===")

    spark = create_spark_session("SILVER_to_GOLD_customers")

    logger.info(f"Reading Silver layer from {SILVER_INPUT}")
    df = spark.read.parquet(str(SILVER_INPUT))

    logger.info("Building Gold aggregates...")

    df_gold = (
        df.groupBy("estado")
        .agg(
            F.count("customer_id").alias("total_customers"),
            F.countDistinct("email").alias("unique_emails"),
            F.min("_loadtime").alias("first_loadtime"),
            F.max("_loadtime").alias("last_loadtime"),
        )
        .orderBy(F.col("total_customers").desc())
        .withColumn("_created_at", F.current_timestamp())
    )

    record_count = df_gold.count()
    logger.info(f"Gold aggregation rows: {record_count}")

    logger.info(f"Saving to {GOLD_OUTPUT}")
    (
        df_gold.write
        .parquet(str(GOLD_OUTPUT))
    )

    logger.info(f"Gold layer written successfully — {record_count} rows.")
    spark.stop()
    return record_count


if __name__ == "__main__":
    aggregate_customers()
