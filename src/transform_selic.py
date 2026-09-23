from pathlib import Path

import pandas as pd


ARQUIVO_ENTRADA = Path("data/bronze/selic_raw.json")
ARQUIVO_SAIDA = Path("data/silver/selic.parquet")

# Lê os dados brutos da camada Bronze
df = pd.read_json(ARQUIVO_ENTRADA)

# Padroniza nomes e tipos das colunas
df = df.rename(columns={
    "data": "data_referencia",
    "valor": "taxa_selic_aa",
})

df["data_referencia"] = pd.to_datetime(
    df["data_referencia"],
    format="%d/%m/%Y",
)

df["taxa_selic_aa"] = pd.to_numeric(df["taxa_selic_aa"])

# Salva os dados tratados na camada Silver em Parquet
ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(ARQUIVO_SAIDA, index=False)

print(f"Registros processados: {len(df)}")
print(df.dtypes)
print(f"Arquivo salvo em: {ARQUIVO_SAIDA}")