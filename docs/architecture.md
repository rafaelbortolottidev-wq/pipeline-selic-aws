# Arquitetura

## Objetivo

O projeto implementa um pipeline de Engenharia de Dados para dados históricos da taxa Selic, separando ingestão, tratamento, agregação, armazenamento e consumo analítico.

## Fluxo atual

```text
API Banco Central
        ↓
ingest_selic.py
        ↓
Bronze — JSON
        ↓
transform_selic.py
        ↓
Silver — Parquet
        ↓
build_gold_selic.py
        ↓
Gold — Parquet mensal
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

## Fonte de dados

- Fonte: API SGS do Banco Central do Brasil
- Série: `1178`
- Período do projeto: `01/01/2022` até a observação mais recente disponível
- Campos de origem: `data` e `valor`

## Camadas de dados

### Bronze

Preserva o retorno da API em formato próximo ao dado de origem.

```text
data/bronze/selic_raw.json
```

Responsabilidade:

```text
API → extração → persistência do dado bruto
```

### Silver

Padroniza nomes e tipos para uso analítico.

```text
data/silver/selic.parquet
```

Transformações principais:

```text
data  → data_referencia
valor → taxa_selic_aa
```

Tipos esperados:

```text
data_referencia → datetime
taxa_selic_aa   → numérico
```

### Gold

Agrega a série diária em granularidade mensal.

```text
data/gold/selic_mensal.parquet
```

Campos:

```text
ano_mes
taxa_media
taxa_minima
taxa_maxima
taxa_fim_mes
```

## Camada AWS

### Amazon S3

Armazena os arquivos das camadas Bronze, Silver e Gold.

```text
s3://rafael-portfolio-dados-aws/
├── bronze/selic/
├── silver/selic/
├── gold/selic/
└── athena-results/
```

### AWS Glue

O crawler lê a camada Gold no S3 e registra seu schema no Glue Data Catalog.

```text
Crawler: crawler-gold-selic
Database: selic_analytics
Table: selic
```

O Glue Data Catalog armazena metadados; os dados físicos permanecem no S3.

### Amazon Athena

Consulta a tabela catalogada pelo Glue diretamente sobre os arquivos Parquet no S3.

```text
Catalog: AwsDataCatalog
Database: selic_analytics
Table: selic
Workgroup: primary
```

### Power BI

O Power BI consome a tabela `selic` pelo conector Amazon Athena usando ODBC em modo Importar.

```text
Power BI
   ↓
Amazon Athena
   ↓
Glue Data Catalog
   ↓
Amazon S3
```

## Decisões principais

- Bronze em JSON para preservar o dado próximo à origem.
- Silver e Gold em Parquet para uso analítico e leitura eficiente pelo Athena.
- Notebooks usados para inspeção e validação; código de produção mantido em `src/`.
- Glue Crawler aplicado à Gold, que é a camada de consumo analítico.
- Athena usado como mecanismo SQL serverless sobre o S3.
- Power BI em modo Importar para o volume atual do projeto.

## Evolução

A documentação representa sempre o estado atual da arquitetura. A evolução histórica do projeto fica registrada no Git por commits, branches e Pull Requests.
