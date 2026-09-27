from pathlib import Path

import pandas as pd


# Entrada deste processo
ARQUIVO_ENTRADA_SILVER = Path("data/silver/selic.parquet")

# Saída deste processo
ARQUIVO_SAIDA_GOLD = Path("data/gold/selic_mensal.parquet")


# 1. Lê os dados da camada Silver
dados_silver = pd.read_parquet(ARQUIVO_ENTRADA_SILVER)

dados_silver = dados_silver.sort_values("data_referencia")


# 2. Cria a referência mensal
dados_silver["ano_mes"] = (
    dados_silver["data_referencia"]
    .dt.to_period("M")
    .astype(str)
)


# 3. Cria os indicadores da camada Gold
dados_gold = (
    dados_silver
    .groupby("ano_mes", as_index=False)
    .agg(
        taxa_media=("taxa_selic_aa", "mean"),
        taxa_minima=("taxa_selic_aa", "min"),
        taxa_maxima=("taxa_selic_aa", "max"),
        taxa_fim_mes=("taxa_selic_aa", "last"),
    )
)


# 4. Salva os dados agregados na camada Gold
ARQUIVO_SAIDA_GOLD.parent.mkdir(
    parents=True,
    exist_ok=True,
)

dados_gold.to_parquet(
    ARQUIVO_SAIDA_GOLD,
    index=False,
)


print(f"Registros gerados: {len(dados_gold)}")
print(f"Arquivo Gold criado: {ARQUIVO_SAIDA_GOLD}")