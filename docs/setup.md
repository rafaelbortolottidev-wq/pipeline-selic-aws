# Configuração e execução

Este documento reúne apenas as configurações necessárias para executar e reproduzir o pipeline atual.

## 1. Ambiente Python

Criar o ambiente virtual:

```powershell
python -m venv .venv
```

Ativar no PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Dependências principais:

```text
pandas
requests
pyarrow
boto3
```

Instalação do boto3:

```powershell
python -m pip install boto3
```

## 2. Execução local

Executar na raiz do projeto, nesta ordem:

```powershell
python src/01_ingest_selic.py
python src/02_transform_selic.py
python src/03_build_gold_selic.py
python src/04_upload_s3.py
```

Arquivos locais gerados:

```text
data/bronze/selic_raw.json
data/silver/selic.parquet
data/gold/selic_mensal.parquet
```

A ingestão é incremental: quando a Bronze já existe, o script identifica a última data carregada e consulta a API apenas a partir do dia seguinte. Se não houver novos registros, o histórico é preservado.

A pasta `data/` não é versionada no Git.

## 3. AWS CLI e autenticação local

Profile utilizado pelo projeto:

```text
selic-dev
```

Validar a autenticação:

```powershell
aws sts get-caller-identity --profile selic-dev
```

Região utilizada:

```text
us-east-1
```

A AWS CLI continua sendo útil para configuração e validação do ambiente local. Os uploads do pipeline, porém, são realizados pelo Python com boto3.

## 4. Upload para o Amazon S3

Script:

```text
src/04_upload_s3.py
```

Execução:

```powershell
python src/04_upload_s3.py
```

Mapeamento atual:

```text
data/bronze/selic_raw.json
→ s3://rafael-portfolio-dados-aws/bronze/selic/selic_raw.json

data/silver/selic.parquet
→ s3://rafael-portfolio-dados-aws/silver/selic/selic.parquet

data/gold/selic_mensal.parquet
→ s3://rafael-portfolio-dados-aws/gold/selic/selic_mensal.parquet
```

O boto3 usa o profile `selic-dev` configurado localmente. Credenciais não são armazenadas no código nem versionadas no Git.

## 5. IAM

O projeto utiliza um usuário IAM dedicado para acesso programático aos recursos necessários.

Permissões utilizadas pelo pipeline:

- leitura e escrita nos prefixos Bronze, Silver e Gold do S3;
- leitura e escrita em `athena-results/`;
- execução de consultas no Athena;
- leitura dos metadados necessários no Glue Data Catalog.

O Glue utiliza uma role IAM separada.

## 6. AWS Glue

O crawler aponta para:

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

## 7. Amazon Athena

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

## 8. Power BI / ODBC

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

O arquivo `.pbix` é mantido localmente e está ignorado pelo Git.
