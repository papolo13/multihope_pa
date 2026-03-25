"""
Unit tests for SILVER -> GOLD: customers aggregation.
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
        .appName("test_silver_to_gold")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )


@pytest.fixture
def silver_data(spark):
    data = [
        (1, "Alice", "alice@example.com", "US", "2024-01-01"),
        (2, "Bob", "bob@example.com", "MX", "2024-02-15"),
        (3, "Carlos", "carlos@example.com", "MX", "2024-03-10"),
        (4, "Diana", "diana@example.com", "US", "2024-04-20"),
    ]
    return spark.createDataFrame(
        data,
        ["customer_id", "name", "email", "country", "created_at"],
    )


def test_aggregation_row_count(silver_data):
    df_gold = silver_data.groupBy("country").agg(
        F.count("customer_id").alias("total_customers")
    )
    assert df_gold.count() == 2  # US and MX


def test_aggregation_values(silver_data):
    df_gold = silver_data.groupBy("country").agg(
        F.count("customer_id").alias("total_customers")
    )
    result = {row["country"]: row["total_customers"] for row in df_gold.collect()}
    assert result["US"] == 2
    assert result["MX"] == 2


def test_gold_columns(silver_data):
    df_gold = silver_data.groupBy("country").agg(
        F.count("customer_id").alias("total_customers"),
        F.countDistinct("email").alias("unique_emails"),
    )
    assert "total_customers" in df_gold.columns
    assert "unique_emails" in df_gold.columns
