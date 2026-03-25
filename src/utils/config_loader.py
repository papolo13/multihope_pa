import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parents[2]


def load_db_config() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    config_path = PROJECT_ROOT / "config" / "database.yml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    db = config["database"]
    return {
        "host": db["host"],
        "port": db["port"],
        "database": db["name"],
        "driver": db["driver"],
        "options": db.get("options", {}),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }


def get_jdbc_url(db_config: dict) -> str:
    opts = "&".join(f"{k}={v}" for k, v in db_config["options"].items())
    return (
        f"jdbc:mysql://{db_config['host']}:{db_config['port']}"
        f"/{db_config['database']}?{opts}"
    )
