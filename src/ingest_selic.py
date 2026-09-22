import json
from datetime import date
from pathlib import Path

import requests


URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados"

parametros = {
    "formato": "json",
    "dataInicial": "01/01/2021",
    "dataFinal": date.today().strftime("%d/%m/%Y"),
}

response = requests.get(URL, params=parametros, timeout=30)
response.raise_for_status()

dados = response.json()

pasta_destino = Path("data/bronze")
pasta_destino.mkdir(parents=True, exist_ok=True)

arquivo_destino = pasta_destino / "selic_raw.json"

with open(arquivo_destino, "w", encoding="utf-8") as arquivo:
    json.dump(dados, arquivo, ensure_ascii=False, indent=2)

print(f"Registros recebidos: {len(dados)}")
print(f"Arquivo salvo em: {arquivo_destino}")