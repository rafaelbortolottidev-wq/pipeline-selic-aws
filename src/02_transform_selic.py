
# Biblioteca para trabalhar com caminhos de arquivos
from pathlib import Path

# Biblioteca para manipulação e transformação de dados
import pandas as pd


# =========================================================
# 1. CONFIGURAÇÃO DOS CAMINHOS
# =========================================================

# Arquivo JSON que contém os dados da camada Bronze
ARQUIVO_ENTRADA_BRONZE = Path("data/bronze/selic_raw.json")

# Arquivo Parquet que receberá os dados tratados na Silver
ARQUIVO_SAIDA_SILVER = Path("data/silver/selic.parquet")


# =========================================================
# 2. FUNÇÃO DE TRANSFORMAÇÃO
# =========================================================

def transformar_bronze_silver(dados_bronze):
    """
    Recebe um DataFrame da Bronze e devolve um DataFrame
    com os nomes e tipos das colunas padronizados.

    Não lê nem grava arquivos.
    Isso permite testar a transformação separadamente.
    """

    # Renomeia as colunas para nomes mais descritivos
    # copy() cria uma cópia para trabalhar sem alterar
    # diretamente o DataFrame recebido
    dados_silver = dados_bronze.rename(columns={
        "data": "data_referencia",
        "valor": "taxa_selic_aa",
    }).copy()

    # Converte a data de texto para o tipo datetime
    # Exemplo: "10/10/2026" -> datetime
    dados_silver["data_referencia"] = pd.to_datetime(
        dados_silver["data_referencia"],
        format="%d/%m/%Y",
    )

    # Converte a taxa Selic para um tipo numérico
    # Exemplo: "12.75" -> 12.75
    dados_silver["taxa_selic_aa"] = pd.to_numeric(
        dados_silver["taxa_selic_aa"]
    )

    # Devolve os dados tratados para quem chamou a função
    return dados_silver


# =========================================================
# 3. FUNÇÃO PRINCIPAL
# =========================================================

def main():
    """
    Executa o processamento local completo:
    Bronze -> Transformação -> Silver.
    """

    # Lê o arquivo JSON da camada Bronze
    dados_bronze = pd.read_json(ARQUIVO_ENTRADA_BRONZE)

    # Executa a função de transformação
    dados_silver = transformar_bronze_silver(dados_bronze)

    # Cria a pasta Silver caso ela ainda não exista
    ARQUIVO_SAIDA_SILVER.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Grava o DataFrame tratado no formato Parquet
    # index=False evita salvar o índice do pandas
    dados_silver.to_parquet(
        ARQUIVO_SAIDA_SILVER,
        index=False,
    )

    # Exibe informações para acompanhamento da execução
    print(f"Registros processados: {len(dados_silver)}")
    print(dados_silver.dtypes)
    print(f"Arquivo Silver criado: {ARQUIVO_SAIDA_SILVER}")


# =========================================================
# 4. CONTROLE DE EXECUÇÃO
# =========================================================

# Executa main() somente quando este arquivo é
# chamado diretamente pelo Python.
#
# Quando o pytest importar este módulo para testar
# transformar_bronze_silver(), main() não será executada.

if __name__ == "__main__":
    main()
