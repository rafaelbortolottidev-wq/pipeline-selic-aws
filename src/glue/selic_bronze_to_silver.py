import sys

from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from awsglue.utils import getResolvedOptions

from awsgluedq.transforms import EvaluateDataQuality

from pyspark.context import SparkContext
from pyspark.sql.functions import col, to_date


# Parâmetros do Glue Job
args = getResolvedOptions(sys.argv, ["JOB_NAME"])

# Inicializa Spark e Glue
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)


# Caminhos no S3
BRONZE_PATH = (
    "s3://rafael-portfolio-dados-aws/"
    "bronze/selic/selic_raw.json"
)

SILVER_PATH = (
    "s3://rafael-portfolio-dados-aws/"
    "silver/selic/"
)


# 1. Lê a Bronze
dados_bronze = (
    spark.read
    .option("multiline", "true")
    .json(BRONZE_PATH)
)


# 2. Transforma para Silver
dados_silver = (
    dados_bronze
    .withColumnRenamed("data", "data_referencia")
    .withColumnRenamed("valor", "taxa_selic_aa")
    .withColumn(
        "data_referencia",
        to_date(col("data_referencia"), "dd/MM/yyyy")
    )
    .withColumn(
        "taxa_selic_aa",
        col("taxa_selic_aa").cast("double")
    )
    .select(
        "data_referencia",
        "taxa_selic_aa"
    )
)


# 3. Converte DataFrame para DynamicFrame
dados_silver_dyf = DynamicFrame.fromDF(
    dados_silver,
    glue_context,
    "dados_silver"
)


# 4. Regras de Data Quality
regras_dq = """
Rules = [
    RowCount > 0,
    IsComplete "data_referencia",
    IsUnique "data_referencia",
    IsComplete "taxa_selic_aa",
    ColumnValues "taxa_selic_aa" > 0
]
"""


# 5. Executa Data Quality
resultado_dq = EvaluateDataQuality.apply(
    frame=dados_silver_dyf,
    ruleset=regras_dq,
    publishing_options={
        "dataQualityEvaluationContext": "selic_silver",
        "enableDataQualityCloudWatchMetrics": True,
        "enableDataQualityResultsPublishing": True
    }
)


# 6. Mostra resultados nos logs
resultado_dq_df = resultado_dq.toDF()

resultado_dq_df.show(
    truncate=False
)


# 7. Verifica se alguma regra falhou
quantidade_falhas = (
    resultado_dq_df
    .filter(col("Outcome") == "Failed")
    .count()
)

if quantidade_falhas > 0:
    raise ValueError(
        f"Data Quality reprovada: "
        f"{quantidade_falhas} regra(s) falharam."
    )


# 8. Grava Silver somente se Data Quality passar
(
    dados_silver.write
    .mode("overwrite")
    .parquet(SILVER_PATH)
)

print(
    f"Silver aprovada pelo Data Quality e gravada em: "
    f"{SILVER_PATH}"
)


job.commit()