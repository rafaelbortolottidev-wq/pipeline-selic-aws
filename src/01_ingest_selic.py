import json
from datetime import date, datetime, timedelta
from pathlib import Path

import requests


# Fonte dos dados
URL_API_BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados"

# Saída deste processo
ARQUIVO_SAIDA_BRONZE = Path("data/bronze/selic_raw.json")

# Primeira data do histórico do projeto
DATA_INICIAL_HISTORICA = date(2022, 1, 1)


# 1. Lê os dados existentes na Bronze
if ARQUIVO_SAIDA_BRONZE.exists():

    with open(ARQUIVO_SAIDA_BRONZE, "r", encoding="utf-8") as arquivo:
        dados_existentes = json.load(arquivo)

else:
    dados_existentes = []


# 2. Define a data inicial da próxima carga
if dados_existentes:

    ultima_data = max(
        datetime.strptime(registro["data"], "%d/%m/%Y").date()
        for registro in dados_existentes
    )

    data_inicial = ultima_data + timedelta(days=1)

else:
    data_inicial = DATA_INICIAL_HISTORICA


data_final = date.today()


# 3. Consulta somente os registros novos
parametros_api = {
    "formato": "json",
    "dataInicial": data_inicial.strftime("%d/%m/%Y"),
    "dataFinal": data_final.strftime("%d/%m/%Y"),
}

print(f"Última carga até: {data_inicial - timedelta(days=1)}")
print(f"Buscando novos dados a partir de: {data_inicial}")


if data_inicial <= data_final:

    resposta_api = requests.get(
        URL_API_BCB,
        params=parametros_api,
        timeout=30,
    )

    # A API pode retornar 404 quando ainda não existem dados no período
    if resposta_api.status_code == 404:
        dados_novos = []
    else:
        resposta_api.raise_for_status()
        dados_novos = resposta_api.json()

else:
    dados_novos = []


# 4. Junta histórico + registros novos
dados_completos = dados_existentes + dados_novos


# 5. Remove possíveis duplicidades pela data
dados_completos = {
    registro["data"]: registro
    for registro in dados_completos
}

dados_completos = list(dados_completos.values())


# 6. Ordena os registros pela data
dados_completos.sort(
    key=lambda registro:
    datetime.strptime(registro["data"], "%d/%m/%Y")
)


# 7. Salva a Bronze atualizada
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
        dados_completos,
        arquivo,
        ensure_ascii=False,
        indent=2,
    )


# 8. Resultado da execução
print(f"Novos registros recebidos: {len(dados_novos)}")
print(f"Total de registros na Bronze: {len(dados_completos)}")
print(f"Arquivo Bronze atualizado: {ARQUIVO_SAIDA_BRONZE}")