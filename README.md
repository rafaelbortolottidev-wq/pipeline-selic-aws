# Pipeline AWS para Análise Histórica da Selic

Pipeline de Engenharia de Dados para ingestão, transformação, armazenamento e consulta de dados históricos da taxa Selic utilizando Python e serviços AWS.

## Objetivo

Construir um pipeline seguindo a arquitetura Bronze, Silver e Gold, armazenando os dados no Amazon S3 e disponibilizando a camada analítica para consultas SQL com Amazon Athena.

## Arquitetura

```text
API Banco Central
        ↓
Python
        ↓
Bronze — JSON
        ↓
Data Profiling
        ↓
Silver — Parquet
        ↓
Gold — Parquet agregado
        ↓
Amazon S3
        ↓
AWS Glue Crawler
        ↓
Glue Data Catalog
        ↓
Amazon Athena
        ↓
SQL
```

## Tecnologias

- Python
- pandas
- PyArrow
- Jupyter Notebook
- Amazon S3
- AWS Glue
- AWS IAM
- AWS CLI
- Amazon Athena
- Git e GitHub

## Estrutura do projeto

```text
pipeline-selic-aws/
├── notebooks/
│   ├── 01_bronze_data_profiling.ipynb
│   ├── 02_silver_data_validation.ipynb
│   └── 03_gold_data_analysis.ipynb
├── src/
│   ├── ingest_selic.py
│   ├── transform_selic.py
│   └── build_gold_selic.py
├── .gitignore
└── README.md
```

## Pipeline

**Bronze:** preserva os dados brutos recebidos da API do Banco Central.

**Silver:** padroniza nomes, tipos e armazena os dados tratados em Parquet.

**Gold:** agrega os dados mensalmente para consumo analítico.

A camada Gold é armazenada no Amazon S3, catalogada pelo AWS Glue e consultada pelo Amazon Athena.

## Resultado

```text
API Banco Central       ✅
Bronze                  ✅
Data Profiling          ✅
Silver                  ✅
Gold                    ✅
Amazon S3               ✅
AWS Glue Crawler        ✅
Glue Data Catalog       ✅
Amazon Athena           ✅
Power BI                ⏳
Automação               ⏳
```

A primeira consulta no Athena foi executada com sucesso sobre os arquivos Parquet catalogados pelo AWS Glue.

## Como executar

```powershell
python src/ingest_selic.py
python src/transform_selic.py
python src/build_gold_selic.py
```

## Próximos passos

- conectar o Amazon Athena ao Power BI;
- implementar carga incremental;
- automatizar uploads com `boto3`;
- adicionar testes de qualidade dos dados;
- evoluir a orquestração do pipeline.