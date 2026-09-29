# Pipeline AWS para Análise Histórica da Selic

Pipeline de Engenharia de Dados para ingestão incremental, transformação, armazenamento, catalogação, consulta e visualização de dados históricos da taxa Selic com Python e AWS.

## Arquitetura

```text
API Banco Central
        ↓
01_ingest_selic.py
Carga incremental
        ↓
Bronze local — JSON
        ↓
02_transform_selic.py
        ↓
Silver local — Parquet
        ↓
03_build_gold_selic.py
        ↓
Gold local — Parquet mensal
        ↓
04_upload_s3.py + boto3
        ↓
Amazon S3
        ↓
AWS Glue Data Catalog
        ↓
Amazon Athena
        ↓
Power BI
```

## Tecnologias

- Python, pandas, requests, PyArrow e boto3
- Jupyter Notebook
- Amazon S3
- AWS IAM e AWS CLI
- AWS Glue Crawler e Glue Data Catalog
- Amazon Athena
- Amazon Athena ODBC Driver
- Power BI Desktop
- Git e GitHub

## Estrutura do projeto

```text
pipeline-selic-aws/
├── docs/
│   ├── architecture.md
│   └── setup.md
├── notebooks/
│   ├── 01_bronze_data_profiling.ipynb
│   ├── 02_silver_data_validation.ipynb
│   └── 03_gold_data_analysis.ipynb
├── src/
│   ├── 01_ingest_selic.py
│   ├── 02_transform_selic.py
│   ├── 03_build_gold_selic.py
│   └── 04_upload_s3.py
├── .gitignore
└── README.md
```

Os arquivos gerados em `data/` e o arquivo `.pbix` são mantidos apenas no ambiente local e não são versionados no Git.

## Fluxo dos dados

| Etapa | Entrada | Processamento | Saída |
|---|---|---|---|
| Ingestão | API BCB — série 1178 | Busca apenas registros posteriores à última data da Bronze | `data/bronze/selic_raw.json` |
| Silver | Bronze | Padronização de nomes e tipos | `data/silver/selic.parquet` |
| Gold | Silver | Agregação mensal | `data/gold/selic_mensal.parquet` |
| Upload | Bronze, Silver e Gold locais | Envio para o S3 com boto3 | `s3://rafael-portfolio-dados-aws/` |

A ingestão incremental preserva o histórico existente, incorpora apenas novos registros e evita duplicidades por data. Reexecutar o processo sem novos dados mantém a Bronze inalterada.

A camada Gold contém:

```text
ano_mes
taxa_media
taxa_minima
taxa_maxima
taxa_fim_mes
```

## Execução local

```powershell
python src/01_ingest_selic.py
python src/02_transform_selic.py
python src/03_build_gold_selic.py
python src/04_upload_s3.py
```

Os notebooks são usados para profiling, validação e análise. O código executável do pipeline é mantido em `src/`.

## Estado atual

```text
API Banco Central       ✅
Bronze / Silver / Gold  ✅
Data Profiling          ✅
Carga incremental       ✅
boto3 / upload S3       ✅
Amazon S3               ✅
AWS Glue Data Catalog   ✅
Amazon Athena           ✅
Athena ODBC             ✅
Power BI                ✅
Automação AWS           ⏳
Monitoramento           ⏳
Data Quality            ⏳
```

## Documentação

- [Arquitetura](docs/architecture.md)
- [Configuração e execução](docs/setup.md)

## Próximos passos

- executar o pipeline na AWS sem dependência do computador local;
- adicionar agendamento com EventBridge;
- adicionar logs e monitoramento com CloudWatch;
- evoluir processamento e Data Quality nas próximas fases.
