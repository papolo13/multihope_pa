import yaml
from pathlib import Path
from pyspark.sql import SparkSession

PROJECT_ROOT = Path(__file__).parents[2]


def create_spark_session(app_name: str = "MultihopePipeline") -> SparkSession:
    config_path = PROJECT_ROOT / "config" / "spark_config.yml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    spark_conf = config.get("spark", {})

    builder = SparkSession.builder.appName(app_name)
    for key, value in spark_conf.items():
        builder = builder.config(key, str(value))

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark
