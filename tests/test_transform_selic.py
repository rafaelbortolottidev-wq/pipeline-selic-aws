
import importlib.util
from pathlib import Path

import pandas as pd


# Carrega o script de transformação sem executar main()
caminho = Path(__file__).resolve().parents[1] / "src/02_transform_selic.py"

spec = importlib.util.spec_from_file_location("transform_selic", caminho)
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


def test_transformar_bronze_silver():
    # Cria dados fictícios da API do Banco Central
    bronze = pd.DataFrame({
        "data": ["01/10/2026", "02/10/2026"],
        "valor": ["12.75", "12.50"],
    })

    # Executa somente a transformação
    silver = modulo.transformar_bronze_silver(bronze)

    # Confere se os nomes das colunas estão corretos
    assert list(silver.columns) == [
        "data_referencia",
        "taxa_selic_aa",
    ]

    # Confere os tipos e os valores transformados
    assert pd.api.types.is_datetime64_any_dtype(silver["data_referencia"])
    assert pd.api.types.is_numeric_dtype(silver["taxa_selic_aa"])
    assert silver["taxa_selic_aa"].tolist() == [12.75, 12.50]

    # Confere a quantidade de registros
    assert len(silver) == 2
