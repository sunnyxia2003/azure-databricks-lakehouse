
# Databricks notebook source
# Project: Azure Databricks Enterprise Lakehouse
# Purpose: Incremental JSON ingestion into Bronze Delta Table

from pyspark.sql import functions as F

# 1. Configuration
SOURCE_PATH = "/Volumes/main/raw/telemetry_files/"
SCHEMA_PATH = "/Volumes/main/metadata/telemetry_schema/"
CHECKPOINT_PATH = "/Volumes/main/metadata/telemetry_checkpoint/"
TARGET_TABLE = "main.bronze.telemetry"

# 2. Create target schema
spark.sql("CREATE SCHEMA IF NOT EXISTS main.bronze")

# 3. Configure Auto Loader
bronze_df = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", SCHEMA_PATH)
    .option("cloudFiles.schemaEvolutionMode", "rescue")
    .option("rescuedDataColumn", "_rescued_data")
    .load(SOURCE_PATH)
)

# 4. Add ingestion metadata
bronze_df = (
    bronze_df
    .withColumn("_ingestion_timestamp", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
)

# 5. Write to Bronze Delta Table
query = (
    bronze_df.writeStream
    .format("delta")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable(TARGET_TABLE)
)

query.awaitTermination()

print(f"Bronze ingestion completed: {TARGET_TABLE}")
