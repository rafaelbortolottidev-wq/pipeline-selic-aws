# Pipeline AWS para Análise Histórica da Selic

Projeto de Engenharia de Dados para ingestão, transformação, armazenamento, catalogação e consulta de dados históricos da taxa Selic utilizando Python e serviços AWS.

## Arquitetura

```text
API Banco Central
        ↓
Python
        ↓
Bronze — JSON bruto
        ↓
Data Profiling
        ↓
Silver — Parquet tratado
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