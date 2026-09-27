import json
from datetime import date
from pathlib import Path

import requests


# Fonte dos dados
URL_API_BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados"

# Saída deste processo
ARQUIVO_SAIDA_BRONZE = Path("data/bronze/selic_raw.json")


parametros_api = {
    "formato": "json",
    "dataInicial": "01/01/2022",
    "dataFinal": date.today().strftime("%d/%m/%Y"),
}


# 1. Extrai os dados da API
resposta_api = requests.get(
    URL_API_BCB,
    params=parametros_api,
    timeout=30,
)

resposta_api.raise_for_status()

dados_brutos = resposta_api.json()


# 2. Salva os dados na camada Bronze
ARQUIVO_SAIDA_BRONZE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

with open(
    ARQUIVO_SAIDA_BRONZE,
    "w",
    encoding="utf-8",
) as arquivo:
    json.dump(
        dados_brutos,
        arquivo,
        ensure_ascii=False,
        indent=2,
    )


print(f"Registros recebidos: {len(dados_brutos)}")
print(f"Arquivo Bronze criado: {ARQUIVO_SAIDA_BRONZE}")