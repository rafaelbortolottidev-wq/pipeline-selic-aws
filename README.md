# Pipeline AWS para Análise Histórica da Selic

Pipeline de Engenharia de Dados para ingestão, transformação, armazenamento, catalogação, consulta e visualização de dados históricos da taxa Selic utilizando Python, AWS e Power BI.

## Objetivo

Construir um pipeline seguindo a arquitetura Bronze, Silver e Gold, armazenando os dados no Amazon S3, catalogando a camada analítica com AWS Glue, consultando os dados com Amazon Athena e disponibilizando o resultado para visualização no Power BI.

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
ODBC
        ↓
Power BI
```

## Tecnologias

- Python
- pandas
- requests
- PyArrow
- Jupyter Notebook
- Amazon S3
- AWS IAM
- AWS CLI
- AWS Glue
- Glue Data Catalog
- Amazon Athena
- Amazon Athena ODBC Driver 2.x
- Power BI Desktop
- Git
- GitHub

## Estrutura do projeto

```text
pipeline-selic-aws/
├── docs/
│   └── DOCUMENTACAO_TECNICA.md
├── notebooks/
│   ├── 01_bronze_data_profiling.ipynb
│   ├── 02_silver_data_validation.ipynb
│   └── 03_gold_data_analysis.ipynb
├── powerbi/
│   └── selic_dashboard.pbix
├── src/
│   ├── ingest_selic.py
│   ├── transform_selic.py
│   └── build_gold_selic.py
├── .gitignore
└── README.md
```

## Pipeline

**Bronze**  
Preserva os dados brutos recebidos da API do Banco Central em JSON.

**Silver**  
Padroniza nomes, converte tipos e salva os dados tratados em Parquet.

**Gold**  
Agrega os dados mensalmente para consumo analítico.

A camada Gold é armazenada no Amazon S3, catalogada pelo AWS Glue, consultada pelo Amazon Athena e consumida pelo Power BI através do driver ODBC do Athena.

## Resultado

```text
API Banco Central       ✅
Ingestão Python         ✅
Bronze                  ✅
Data Profiling          ✅
Silver                  ✅
Gold                    ✅
Amazon S3               ✅
AWS CLI                 ✅
IAM                     ✅
AWS Glue Crawler        ✅
Glue Data Catalog       ✅
Amazon Athena           ✅
Athena ODBC             ✅
Power BI                ✅
Carga incremental       ⏳
boto3                   ⏳
Automação               ⏳
Data Quality            ⏳
```

A camada Gold está disponível no Athena e foi conectada com sucesso ao Power BI por meio do DSN `SelicAthena`.

## Como executar

```powershell
python src/ingest_selic.py
python src/transform_selic.py
python src/build_gold_selic.py
```

## Power BI

O arquivo do relatório está localizado em:

```text
powerbi/selic_dashboard.pbix
```

A conexão utiliza:

```text
DSN: SelicAthena
Region: us-east-1
Catalog: AwsDataCatalog
Database: selic_analytics
Workgroup: primary
Modo: Importar
```

## Documentação

Os detalhes da arquitetura, transformações, configurações AWS, IAM, ODBC, Athena e Power BI estão disponíveis em:

[Documentação técnica completa](docs/DOCUMENTACAO_TECNICA.md)

## Próximos passos

- construir os visuais e indicadores do dashboard no Power BI;
- criar medidas DAX;
- implementar carga incremental;
- automatizar uploads com `boto3`;
- adicionar testes de qualidade dos dados;
- evoluir a orquestração e o monitoramento do pipeline.
