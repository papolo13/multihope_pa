# CLAUDE.md

Este archivo proporciona orientación a Claude Code (claude.ai/code) cuando trabaja con el código de este repositorio.

## Descripción del proyecto

Pipeline ETL con arquitectura Medallion usando PySpark que lee desde una base de datos MySQL y escribe archivos Parquet en tres capas: RAW → BRONZE → SILVER → GOLD.

## Estructura
- notebooks/
- scripts/
- data/
- src
- config
- catalog/

## Objetivo
Ayudar a analizar, mantener y mejorar el proyecto sin romper notebooks ni rutas de datos.

## Memoria del proyecto

La memoria persistente de este proyecto se almacena en:

```
C:\Users\Usuario\.claude\projects\C--Users-Usuario-Documents-Cursos-programacion-con-ia-multihope-pa\memory\MEMORY.md
```

Este archivo es el índice de todas las memorias del proyecto (usuario, feedback, contexto, referencias).
Cada entrada apunta a un archivo `.md` individual dentro de ese directorio.
Claude debe leer y actualizar este índice al inicio de cada conversación relevante.

## Reglas
- No borrar archivos sin justificarlo.
- Explicar cambios antes de hacer modificaciones grandes.
- Priorizar análisis de notebooks, dependencias y fallas de ejecución.

## Configuración inicial

El `.venv` del proyecto usa **Python 3.11.9**. Asegúrate de usar esa versión al crear el entorno virtual.

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # o .venv\Scripts\activate en Windows
pip install -r requirements.txt
cp .env.example .env  # luego completar DB_USER y DB_PASSWORD
```

Java debe estar instalado para que PySpark funcione. El driver JDBC de MySQL (v8.0.33) se descarga automáticamente mediante `spark.jars.packages`.

## Ejecución del pipeline

**Como módulos Python (en orden):**
```bash
python -m src.raw_to_bronze.customers_ingestion
python -m src.bronze_to_silver.customers_transform
python -m src.silver_to_gold.customers_aggregation
```

**Como notebooks de Jupyter (en orden):**
1. `notebooks/00_precheck.ipynb` — valida el entorno (Python, Java, configs, SparkSession)
2. `notebooks/01_raw_to_bronze_customers.ipynb`
3. `notebooks/02_bronze_to_silver_customers.ipynb`
4. `notebooks/03_silver_to_gold_customers.ipynb`

## Tests

```bash
pytest tests/ -v
# Ejecutar un solo archivo de test:
pytest tests/test_bronze_to_silver.py -v
```

## Arquitectura

### Flujo de datos

```
MySQL (DB fake) → BRONZE → SILVER / QUARANTINE → GOLD
```

- **BRONZE** (`/data/bronze/`): Datos crudos desde MySQL vía JDBC — sin transformaciones
- **SILVER** (`/data/silver/`): Filas limpias, deduplicadas y validadas; columnas renombradas (ej. `id_cliente` → `customer_id`), email en minúsculas, columnas de metadata añadidas (`_ingested_at`, `_source_layer`)
- **QUARANTINE** (`/data/quarantine/`): Filas que fallaron las reglas de error de DQX
- **GOLD** (`/data/gold/`): Agregaciones de negocio — agrupadas por `estado`, con total de clientes, emails únicos, min/max loadtime

### Utilidades compartidas (`src/utils/`)

- `config_loader.py` — Combina `config/database.yml` + `config/spark_config.yml` + `.env` en un único diccionario de configuración. Se invoca al inicio de cada etapa del pipeline.
- `spark_session.py` — Fábrica que crea una SparkSession a partir de la configuración cargada, incluyendo la configuración del driver JDBC.

### Calidad de datos

La capa BRONZE → SILVER usa **Databricks Labs DQX** (`databricks-labs-dqx`) para definir reglas de calidad de forma declarativa:
- **Reglas de error** (envían a quarantine): `customer_id` no nulo, `nombre` no nulo/vacío, `email` no nulo/vacío
- **Reglas de advertencia** (solo se registran, pasan a Silver): `identificacion` no vacío, `estado` no nulo

### Configuración

- `config/database.yml` — Host MySQL, puerto, nombre de BD, clase del driver, opciones JDBC
- `config/spark_config.yml` — Configuración de SparkSession (master, memoria, shuffle partitions, paquetes JAR)
- `.env` — `DB_USER` y `DB_PASSWORD` (en gitignore)

La raíz del proyecto se resuelve dinámicamente desde los módulos utilitarios como `Path(__file__).parents[2]`.

### Catálogo de datos

`catalog/comercial/` documenta las cuatro tablas fuente (`customers`, `products`, `sales`, `shops`):
- `catalog.md` — definiciones de columnas legibles por humanos, relaciones FK, valores válidos
- `catalog.json` — formato legible por máquina para generación de SQL asistida por IA
