# Arquitetura

## Objetivo

O projeto implementa um pipeline de Engenharia de Dados para dados históricos da taxa Selic, separando ingestão, tratamento, agregação, transferência para a AWS e consumo analítico.

## Fluxo atual

```text
API Banco Central
        ↓
01_ingest_selic.py
        ↓
Carga incremental
        ↓
data/bronze/selic_raw.json
        ↓
02_transform_selic.py
        ↓
data/silver/selic.parquet
        ↓
03_build_gold_selic.py
        ↓
data/gold/selic_mensal.parquet
        ↓
04_upload_s3.py
        ↓
boto3
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
- Período inicial do projeto: `01/01/2022`
- Campos de origem: `data` e `valor`

## Ingestão incremental

A Bronze local funciona como referência para determinar de onde a próxima carga deve continuar.

```text
Bronze não existe
→ inicia em 01/01/2022

Bronze existe
→ identifica a última data carregada
→ soma 1 dia
→ consulta somente registros posteriores
```

Depois da consulta, o processo combina histórico e novos registros, remove possíveis duplicidades pela data, ordena os dados e grava novamente a Bronze completa.

A lógica foi validada em dois cenários: inclusão de novos registros e reexecução sem novos dados. A segunda execução mantém o mesmo histórico, evitando duplicação.

## Camadas locais

### Bronze

```text
data/bronze/selic_raw.json
```

Responsabilidade:

```text
API → ingestão incremental → histórico bruto em JSON
```

### Silver

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

```text
data/gold/selic_mensal.parquet
```

Granularidade:

```text
diária → mensal
```

Campos:

```text
ano_mes
taxa_media
taxa_minima
taxa_maxima
taxa_fim_mes
```

## Upload com boto3

O `04_upload_s3.py` é responsável apenas pela transferência dos arquivos locais para o Amazon S3.

```text
Arquivo local                         Destino no S3

data/bronze/selic_raw.json        →  bronze/selic/selic_raw.json
data/silver/selic.parquet         →  silver/selic/selic.parquet
data/gold/selic_mensal.parquet    →  gold/selic/selic_mensal.parquet
```

O script usa o SDK `boto3` e o profile AWS local `selic-dev`. Os formatos JSON e Parquet já são definidos nas etapas anteriores; o boto3 apenas realiza o upload.

Como os objetos usam chaves fixas no S3, cada execução atualiza os mesmos arquivos de Bronze, Silver e Gold no bucket.

## Camada AWS

### Amazon S3

```text
s3://rafael-portfolio-dados-aws/
├── bronze/selic/
├── silver/selic/
├── gold/selic/
└── athena-results/
```

`athena-results/` é utilizado pelo Athena para armazenar resultados de consultas e não faz parte das camadas Bronze, Silver ou Gold.

### AWS Glue

O crawler lê a camada Gold no S3 e registra seu schema no Glue Data Catalog.

```text
Database: selic_analytics
Table: selic
```

Os dados permanecem fisicamente no S3; o Data Catalog mantém os metadados.

### Amazon Athena

Consulta a tabela catalogada pelo Glue diretamente sobre o Parquet no S3.

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

O arquivo `.pbix` é mantido localmente e não é versionado no Git.

## Decisões principais

- Bronze em JSON para preservar o dado próximo à origem.
- Ingestão incremental para evitar consultar todo o histórico a cada execução.
- Silver e Gold em Parquet para leitura analítica eficiente.
- Notebooks usados para inspeção e validação; código executável mantido em `src/`.
- Upload separado em `04_upload_s3.py` para não misturar processamento de dados com transferência para a AWS.
- boto3 substitui os uploads manuais via `aws s3 cp`.
- Glue Crawler aplicado à Gold, camada destinada ao consumo analítico.
- Athena usado como mecanismo SQL serverless sobre o S3.
- Power BI em modo Importar para o volume atual do projeto.

## Próxima evolução

A próxima fase remove a dependência da execução manual no computador local, introduzindo execução serverless, agendamento e monitoramento com serviços AWS.

A documentação representa o estado atual da arquitetura. A evolução histórica do projeto fica registrada no Git por commits, branches e Pull Requests.
