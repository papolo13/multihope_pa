"""
Unit tests for BRONZE -> SILVER: customers transformation.
"""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


@pytest.fixture(scope="session")
def spark():
    return (
        SparkSession.builder.master("local[1]")
        .appName("test_bronze_to_silver")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )


@pytest.fixture
def bronze_data(spark):
    data = [
        (1, "  Alice  ", "Alice@Example.COM", "US", "2024-01-01"),
        (2, "Bob", "bob@example.com", "MX", "2024-02-15"),
        (2, "Bob", "bob@example.com", "MX", "2024-02-15"),  # duplicate
        (None, "Ghost", "ghost@example.com", "US", "2024-03-01"),  # null id
    ]
    return spark.createDataFrame(
        data,
        ["customer_id", "name", "email", "country", "created_at"],
    )


def test_drop_duplicates(bronze_data):
    df_clean = bronze_data.dropDuplicates()
    assert df_clean.count() == 3


def test_filter_null_customer_id(bronze_data):
    df_clean = bronze_data.filter(F.col("customer_id").isNotNull())
    assert df_clean.count() == 3


def test_email_lowercase(bronze_data):
    df_clean = bronze_data.withColumn("email", F.lower(F.col("email")))
    emails = [row.email for row in df_clean.collect()]
    assert all(e == e.lower() for e in emails)


def test_metadata_columns(bronze_data):
    df = bronze_data.withColumn("_ingested_at", F.current_timestamp())
    assert "_ingested_at" in df.columns
