import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions

from pyspark.context import SparkContext
from pyspark.sql import Window
from pyspark.sql.functions import (
    avg,
    col,
    date_format,
    max,
    min,
    row_number
)


# Parâmetros do Glue Job
args = getResolvedOptions(sys.argv, ["JOB_NAME"])

# Inicializa Spark e Glue
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)


# Caminhos no S3
SILVER_PATH = (
    "s3://rafael-portfolio-dados-aws/"
    "silver/selic/"
)

GOLD_PATH = (
    "s3://rafael-portfolio-dados-aws/"
    "gold/selic/"
)


# 1. Lê a Silver em Parquet
dados_silver = spark.read.parquet(SILVER_PATH)


# 2. Cria a coluna ano_mes
dados_silver = dados_silver.withColumn(
    "ano_mes",
    date_format(col("data_referencia"), "yyyy-MM")
)


# 3. Calcula média, mínima e máxima por mês
dados_agregados = (
    dados_silver
    .groupBy("ano_mes")
    .agg(
        avg("taxa_selic_aa").alias("taxa_media"),
        min("taxa_selic_aa").alias("taxa_minima"),
        max("taxa_selic_aa").alias("taxa_maxima")
    )
)


# 4. Identifica a taxa do último dia de cada mês
janela = Window.partitionBy("ano_mes").orderBy(
    col("data_referencia").desc()
)

dados_fim_mes = (
    dados_silver
    .withColumn("ordem", row_number().over(janela))
    .filter(col("ordem") == 1)
    .select(
        "ano_mes",
        col("taxa_selic_aa").alias("taxa_fim_mes")
    )
)


# 5. Junta as métricas mensais
dados_gold = (
    dados_agregados
    .join(dados_fim_mes, on="ano_mes", how="inner")
    .orderBy("ano_mes")
)


# 6. Exibe informações nos logs
dados_gold.printSchema()

print(
    f"Registros Gold gerados: {dados_gold.count()}"
)


# 7. Grava a Gold em Parquet
(
    dados_gold.write
    .mode("overwrite")
    .parquet(GOLD_PATH)
)

print(
    f"Gold gravada em: {GOLD_PATH}"
)


job.commit()