---
specialty: data-engineering
last_researched: 2026-05
---

# Data Engineering - CV Framing Rules

**Used by:** cv_targeted, axis-classifier

## Capability vocabulary

- Data pipeline design and implementation (batch and streaming)
- Data warehouse, data lake, and lakehouse architecture (open table formats: Iceberg, Delta Lake, Hudi)
- ETL/ELT system design and orchestration (Airflow, Prefect, Dagster, dbt)
- Data modeling (dimensional, normalized, semi-structured)
- Schema design and evolution
- Data quality and observability programs (dbt tests, Great Expectations, Soda; Monte Carlo, Bigeye)
- Data governance, lineage, and cataloging
- Real-time/streaming data architecture (Kafka, Flink, Spark Structured Streaming)
- Data contracts, data products, and data mesh patterns
- Data platform migration leadership
- DataOps practices (CI/CD for data, infrastructure-as-code, deployment automation)
- Data infrastructure cost optimization
- Cross-functional data delivery (analytics engineering, ML/AI, operational systems)

## Terminology

- ETL, ELT, reverse ETL (Hightouch, Census), CDC (change data capture)
- OLAP, OLTP
- Data warehouse, data lake, lakehouse, data mesh; medallion architecture (Bronze/Silver/Gold)
- Star schema, snowflake schema, dimensional modeling, slowly changing dimensions (SCD)
- Schema-on-read, schema-on-write
- Open table formats: Apache Iceberg, Delta Lake, Apache Hudi
- SQL, NoSQL (document, columnar, key-value, graph)
- Processing engines: Apache Spark, Spark Structured Streaming, Apache Flink, Kafka Streams, ksqlDB
- Orchestration: Airflow, Prefect, Dagster; transformation: dbt (Core/Cloud), analytics engineering
- Platforms: Snowflake, Databricks, Redshift, BigQuery, Microsoft Fabric, Synapse
- AWS (S3, Glue, EMR, Athena, Kinesis, MSK), GCP (BigQuery, Dataflow, Dataproc, Pub/Sub), Azure (Data Factory, Fabric, Event Hubs)
- Data quality and observability: dbt tests, Great Expectations, Soda, Elementary; Monte Carlo, Bigeye
- Lineage, data catalog (Atlan, Collibra, Unity Catalog), data contracts, data products
- DAG, orchestration, idempotency; exactly-once vs at-least-once delivery; watermarking

## Knowledge-transfer mode

- Training delivery, curriculum design, and adoption coaching on this specialty's capabilities, methods, tools, or artifacts, when concurrently practicing the specialty in the role.

## Adjacency

Translation signal for entries tagged with adjacent specialties:

- **ai-engineering**: feature pipelines, MLOps infrastructure, vector-store ingestion, and model-data integration work translates directly. Where capabilities tagged in ai-engineering rest on the underlying data infrastructure, that infrastructure work reads as data-engineering depth.
- **data-science**: when data infrastructure was extended with analytical methods (custom quality checks, anomaly detection layered into pipelines, statistical methods on top of warehouse-served data), the analytical layer reads as data-science depth and the infrastructure layer reads as data-engineering depth.
- **operations-strategy**: when data platform decisions (vendor evaluation, build-vs-buy, architecture choices made strategically) preceded or accompanied the implementation, the strategy layer reads as operations-strategy depth and the build layer reads as data-engineering depth.
- **quality-compliance**: when the data systems were subject to CSV/CSA validation, quality-compliance co-tags as the validation framing and data-engineering carries the build.
