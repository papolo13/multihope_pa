"""
Unit tests for RAW -> BRONZE: customers ingestion.
Uses a local SparkSession with mock data instead of a real MySQL connection.
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parents[1]))

from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    return (
        SparkSession.builder.master("local[1]")
        .appName("test_raw_to_bronze")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )


@pytest.fixture
def sample_customers(spark):
    data = [
        (1, "Alice", "alice@example.com", "US", "2024-01-01"),
        (2, "Bob", "bob@example.com", "MX", "2024-02-15"),
        (3, "Carlos", "carlos@example.com", "MX", "2024-03-10"),
    ]
    return spark.createDataFrame(
        data,
        ["customer_id", "name", "email", "country", "created_at"],
    )


def test_sample_dataframe_count(sample_customers):
    assert sample_customers.count() == 3


def test_sample_dataframe_schema(sample_customers):
    columns = sample_customers.columns
    assert "customer_id" in columns
    assert "email" in columns
    assert "country" in columns


def test_parquet_write_read(spark, sample_customers, tmp_path):
    output = str(tmp_path / "bronze" / "customers")
    sample_customers.write.mode("overwrite").parquet(output)

    df_read = spark.read.parquet(output)
    assert df_read.count() == 3
    assert set(df_read.columns) == set(sample_customers.columns)


def test_jdbc_url_format():
    from src.utils.config_loader import get_jdbc_url

    db_config = {
        "host": "www.bigdataybi.com",
        "port": 3306,
        "database": "fake",
        "options": {"useSSL": "false", "allowPublicKeyRetrieval": "true"},
    }
    url = get_jdbc_url(db_config)
    assert url.startswith("jdbc:mysql://www.bigdataybi.com:3306/fake")
    assert "useSSL=false" in url
    assert "allowPublicKeyRetrieval=true" in url
