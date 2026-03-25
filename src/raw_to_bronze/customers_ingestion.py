"""
RAW -> BRONZE: Customers Ingestion
Reads the `customers` table from MySQL and saves it locally in Parquet format.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from src.utils.config_loader import load_db_config, get_jdbc_url
from src.utils.spark_session import create_spark_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

BRONZE_OUTPUT = Path(__file__).parents[2] / "data" / "bronze" / "customers"


def ingest_customers() -> int:
    logger.info("=== RAW -> BRONZE | customers ===")

    db_config = load_db_config()
    jdbc_url = get_jdbc_url(db_config)

    spark = create_spark_session("RAW_to_BRONZE_customers")

    logger.info(
        f"Connecting to {db_config['host']}:{db_config['port']}"
        f"/{db_config['database']}"
    )

    df = (
        spark.read.format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", "customers")
        .option("user", db_config["user"])
        .option("password", db_config["password"])
        .option("driver", db_config["driver"])
        .load()
    )

    record_count = df.count()
    logger.info(f"Records read from MySQL: {record_count}")

    logger.info(f"Saving to {BRONZE_OUTPUT}")
    (
        df.write
        .parquet(str(BRONZE_OUTPUT))
    )

    logger.info(f"Bronze layer written successfully — {record_count} records.")
    spark.stop()
    return record_count


if __name__ == "__main__":
    ingest_customers()
