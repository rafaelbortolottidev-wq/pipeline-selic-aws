from pathlib import Path

import boto3

# Objetivo: automatizar o upload dos arquivos locais para o Amazon S3 usando boto3, substituindo o AWS CLI.

# Configuração AWS
PERFIL_AWS = "selic-dev"
BUCKET_S3 = "rafael-portfolio-dados-aws"


# Arquivos locais → destinos no S3 De-Para
ARQUIVOS_UPLOAD = {
    Path("data/bronze/selic_raw.json"): "bronze/selic/selic_raw.json",
    Path("data/silver/selic.parquet"): "silver/selic/selic.parquet",
    Path("data/gold/selic_mensal.parquet"): "gold/selic/selic_mensal.parquet",
}


# Cria uma sessão na AWS usando o profile configurado localmente
sessao = boto3.Session(profile_name=PERFIL_AWS)

# Cria um cliente para acessar o serviço Amazon S3
s3 = sessao.client("s3")


# Envia os arquivos
for arquivo_local, caminho_s3 in ARQUIVOS_UPLOAD.items():

    if not arquivo_local.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_local}")

    s3.upload_file(
        str(arquivo_local),
        BUCKET_S3,
        caminho_s3,
    )

    print(f"Upload concluído: {arquivo_local} → s3://{BUCKET_S3}/{caminho_s3}")