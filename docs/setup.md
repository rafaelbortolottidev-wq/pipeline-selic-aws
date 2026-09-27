# Configuração e execução

Este documento reúne apenas as configurações necessárias para executar e reproduzir o pipeline atual.

## 1. Ambiente Python

Dependências principais:

```text
pandas
requests
pyarrow
```

Execução local:

```powershell
python src/ingest_selic.py
python src/transform_selic.py
python src/build_gold_selic.py
```

Arquivos gerados:

```text
data/bronze/selic_raw.json
data/silver/selic.parquet
data/gold/selic_mensal.parquet
```

## 2. AWS CLI

Profile utilizado:

```text
selic-dev
```

Validar a autenticação:

```powershell
aws sts get-caller-identity --profile selic-dev
```

Uploads atuais:

```powershell
aws s3 cp data/bronze/selic_raw.json s3://rafael-portfolio-dados-aws/bronze/selic/selic_raw.json --profile selic-dev
aws s3 cp data/silver/selic.parquet s3://rafael-portfolio-dados-aws/silver/selic/selic.parquet --profile selic-dev
aws s3 cp data/gold/selic_mensal.parquet s3://rafael-portfolio-dados-aws/gold/selic/selic_mensal.parquet --profile selic-dev
```

Região utilizada:

```text
us-east-1
```

## 3. IAM

Usuário do projeto:

```text
pipeline-selic-dev
```

Permissões utilizadas pelo pipeline:

- acesso aos prefixos Bronze, Silver e Gold no S3;
- leitura e escrita em `athena-results/`;
- execução de consultas no Athena;
- leitura dos metadados necessários no Glue Data Catalog.

O Glue utiliza uma role separada:

```text
AWSGlueServiceRole-SelicCrawler
```

Credenciais não devem ser armazenadas no código ou versionadas no Git.

## 4. AWS Glue

Crawler:

```text
crawler-gold-selic
```

Fonte:

```text
s3://rafael-portfolio-dados-aws/gold/selic/
```

Configuração atual:

```text
Execução: On demand
Database: selic_analytics
Tabela gerada: selic
Formato: Parquet
```

## 5. Amazon Athena

Configuração:

```text
Region: us-east-1
Catalog: AwsDataCatalog
Database: selic_analytics
Table: selic
Workgroup: primary
Output: s3://rafael-portfolio-dados-aws/athena-results/
```

Consulta de validação:

```sql
SELECT *
FROM "selic_analytics"."selic"
LIMIT 10;
```

## 6. Power BI / ODBC

Driver utilizado:

```text
Amazon Athena ODBC x64 — 2.02.00.01
```

DSN local:

```text
Name: SelicAthena
Region: us-east-1
Catalog: AwsDataCatalog
Database: selic_analytics
Workgroup: primary
S3 Output: s3://rafael-portfolio-dados-aws/athena-results/
Authentication: IAM Profile
AWS Profile: selic-dev
```

No Power BI:

```text
Obter dados
→ Amazon Athena
→ DSN SelicAthena
→ AwsDataCatalog
→ selic_analytics
→ selic
```

Modo utilizado:

```text
Importar
```
