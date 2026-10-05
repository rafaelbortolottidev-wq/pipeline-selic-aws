import json
import boto3
import logging

from datetime import date, datetime, timedelta
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError


BUCKET_S3 = "rafael-portfolio-dados-aws"
ARQUIVO_BRONZE = "bronze/selic/selic_raw.json"

URL_API_BCB = (
    "https://api.bcb.gov.br/dados/serie/"
    "bcdata.sgs.1178/dados"
)

s3 = boto3.client("s3")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    logger.info("Iniciando ingestão incremental da Selic.")

    # 1. Lê a Bronze atual no S3
    resposta = s3.get_object(
        Bucket=BUCKET_S3,
        Key=ARQUIVO_BRONZE
    )

    conteudo = resposta["Body"].read().decode("utf-8")
    dados_existentes = json.loads(conteudo)

    logger.info(
        "Bronze carregada com %s registros.",
        len(dados_existentes)
    )

    # 2. Descobre a watermark
    ultima_data = max(
        datetime.strptime(
            registro["data"],
            "%d/%m/%Y"
        ).date()
        for registro in dados_existentes
    )

    data_inicial = ultima_data + timedelta(days=1)
    data_final = date.today()

    logger.info(
        "Watermark encontrada: %s",
        ultima_data.strftime("%d/%m/%Y")
    )

    logger.info(
        "Período da busca: %s até %s",
        data_inicial.strftime("%d/%m/%Y"),
        data_final.strftime("%d/%m/%Y")
    )

    # 3. Verifica se precisa consultar a API
    if data_inicial > data_final:
        dados_novos = []

    else:
        parametros = {
            "formato": "json",
            "dataInicial": data_inicial.strftime("%d/%m/%Y"),
            "dataFinal": data_final.strftime("%d/%m/%Y")
        }

        url = f"{URL_API_BCB}?{urlencode(parametros)}"

        # 4. Busca dados novos
        try:
            with urlopen(url, timeout=30) as resposta_api:
                dados_novos = json.loads(
                    resposta_api.read().decode("utf-8")
                )

        except HTTPError as erro:
            if erro.code == 404:
                dados_novos = []
            else:
                logger.exception(
                    "Erro ao consultar a API do Banco Central."
                )
                raise

    logger.info(
        "Registros novos encontrados: %s",
        len(dados_novos)
    )

    # 5. Atualiza a Bronze somente se houver dados novos
    if dados_novos:

        dados_completos = dados_existentes + dados_novos

        dados_completos = {
            registro["data"]: registro
            for registro in dados_completos
        }

        dados_completos = list(dados_completos.values())

        dados_completos.sort(
            key=lambda registro: datetime.strptime(
                registro["data"],
                "%d/%m/%Y"
            )
        )

        s3.put_object(
            Bucket=BUCKET_S3,
            Key=ARQUIVO_BRONZE,
            Body=json.dumps(
                dados_completos,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8"),
            ContentType="application/json"
        )

        logger.info(
            "Bronze atualizada no S3. Total: %s registros.",
            len(dados_completos)
        )

    else:
        dados_completos = dados_existentes

        logger.info(
            "Nenhum dado novo. Bronze não foi alterada."
        )

    logger.info("Execução finalizada com sucesso.")

    return {
        "statusCode": 200,
        "watermark_anterior": ultima_data.strftime("%d/%m/%Y"),
        "data_inicial_busca": data_inicial.strftime("%d/%m/%Y"),
        "data_final_busca": data_final.strftime("%d/%m/%Y"),
        "registros_novos": len(dados_novos),
        "total_bronze": len(dados_completos),
        "bronze_atualizada": len(dados_novos) > 0
    }