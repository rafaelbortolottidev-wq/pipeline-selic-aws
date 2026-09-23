from pathlib import Path

import pandas as pd


ARQUIVO_ENTRADA = Path("data/silver/selic.parquet")
ARQUIVO_SAIDA = Path("data/gold/selic_mensal.parquet")

# Lê os dados tratados da camada Silver
df = pd.read_parquet(ARQUIVO_ENTRADA)
df = df.sort_values("data_referencia")

# Cria referência mensal
df["ano_mes"] = df["data_referencia"].dt.to_period("M").astype(str)

# Agrega os indicadores mensais da Selic
df_gold = (
    df.groupby("ano_mes", as_index=False)
    .agg(
        taxa_media=("taxa_selic_aa", "mean"),
        taxa_minima=("taxa_selic_aa", "min"),
        taxa_maxima=("taxa_selic_aa", "max"),
        taxa_fim_mes=("taxa_selic_aa", "last"),
    )
)

# Salva a camada Gold em Parquet
ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
df_gold.to_parquet(ARQUIVO_SAIDA, index=False)

print(f"Registros gerados: {len(df_gold)}")
print(f"Arquivo salvo em: {ARQUIVO_SAIDA}")