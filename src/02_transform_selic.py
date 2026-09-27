from pathlib import Path

import pandas as pd


# Entrada deste processo
ARQUIVO_ENTRADA_BRONZE = Path("data/bronze/selic_raw.json")

# Saída deste processo
ARQUIVO_SAIDA_SILVER = Path("data/silver/selic.parquet")


# 1. Lê os dados da camada Bronze
dados_bronze = pd.read_json(ARQUIVO_ENTRADA_BRONZE)


# 2. Padroniza nomes e tipos das colunas
dados_silver = dados_bronze.rename(columns={
    "data": "data_referencia",
    "valor": "taxa_selic_aa",
})

dados_silver["data_referencia"] = pd.to_datetime(
    dados_silver["data_referencia"],
    format="%d/%m/%Y",
)

dados_silver["taxa_selic_aa"] = pd.to_numeric(
    dados_silver["taxa_selic_aa"]
)


# 3. Salva os dados tratados na camada Silver
ARQUIVO_SAIDA_SILVER.parent.mkdir(
    parents=True,
    exist_ok=True,
)

dados_silver.to_parquet(
    ARQUIVO_SAIDA_SILVER,
    index=False,
)


print(f"Registros processados: {len(dados_silver)}")
print(dados_silver.dtypes)
print(f"Arquivo Silver criado: {ARQUIVO_SAIDA_SILVER}")