import json
from datetime import date
from pathlib import Path

import requests


URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados"
ARQUIVO_SAIDA = Path("data/bronze/selic_raw.json")

parametros = {
    "formato": "json",
    "dataInicial": "01/01/2022",
    "dataFinal": date.today().strftime("%d/%m/%Y"),
}

# Consulta a API do Banco Central
response = requests.get(URL, params=parametros, timeout=30)
response.raise_for_status()

dados = response.json()

# Cria a pasta Bronze e salva o dado bruto
ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)

with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as arquivo:
    json.dump(dados, arquivo, ensure_ascii=False, indent=2)

print(f"Registros recebidos: {len(dados)}")
print(f"Arquivo salvo em: {ARQUIVO_SAIDA}")