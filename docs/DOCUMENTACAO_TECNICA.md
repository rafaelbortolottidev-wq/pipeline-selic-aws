# Documentação Técnica — Pipeline AWS para Análise Histórica da Selic

## 1. Visão geral

Este projeto implementa um pipeline de Engenharia de Dados para ingestão, transformação, agregação, armazenamento, catalogação, consulta e visualização de dados históricos da taxa Selic.

O fluxo foi construído com Python, serviços AWS e Power BI, seguindo uma arquitetura em camadas Bronze, Silver e Gold.

```text
API Banco Central
        ↓
Python
        ↓
Bronze
        ↓s
Data Profiling
        ↓
Silver
        ↓
Gold
        ↓
Amazon S3
        ↓
AWS Glue Crawler
        ↓
Glue Data Catalog
        ↓
Amazon Athena
        ↓
Amazon Athena ODBC
        ↓
Power BI
```

---

## 2. Fonte de dados

Os dados são obtidos por meio da API SGS do Banco Central do Brasil.

Série utilizada:

```text
1178
```

Período definido para o projeto:

```text
01/01/2022 até a observação mais recente disponível
```

Estrutura original retornada pela API:

```text
data
valor
```

---

## 3. Estrutura do projeto

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

---

## 4. Camada Bronze

A camada Bronze preserva os dados no formato mais próximo possível do retorno da fonte.

Arquivo:

```text
data/bronze/selic_raw.json
```

Script responsável:

```text
src/ingest_selic.py
```

Fluxo:

```text
API BCB
   ↓
requests
   ↓
JSON
   ↓
Bronze
```

Comando de execução:

```powershell
python src/ingest_selic.py
```

---

## 5. Data Profiling

Antes da transformação para Silver, os dados da Bronze são analisados no notebook:

```text
notebooks/01_bronze_data_profiling.ipynb
```

O notebook lê diretamente o arquivo Bronze e não realiza uma nova chamada à API.

Foram avaliados:

- quantidade de registros;
- estrutura das colunas;
- tipos;
- valores nulos;
- duplicidades;
- intervalo de datas;
- consistência dos valores.

Resultado observado:

```text
Valores nulos:
data     0
valor    0

Registros duplicados:
0
```

---

## 6. Camada Silver

A Silver contém os dados tratados e tipados.

Arquivo:

```text
data/silver/selic.parquet
```

Script:

```text
src/transform_selic.py
```

Transformações aplicadas:

```text
data  → data_referencia
valor → taxa_selic_aa
```

Tipos:

```text
data_referencia → datetime
taxa_selic_aa   → numérico
```

O formato Parquet foi utilizado por ser adequado a processamento analítico e leitura colunar.

Comando:

```powershell
python src/transform_selic.py
```

Validação:

```text
notebooks/02_silver_data_validation.ipynb
```

---

## 7. Camada Gold

A camada Gold prepara os dados para consumo analítico.

Arquivo:

```text
data/gold/selic_mensal.parquet
```

Script:

```text
src/build_gold_selic.py
```

Granularidade:

```text
diária → mensal
```

Indicadores gerados:

```text
ano_mes
taxa_media
taxa_minima
taxa_maxima
taxa_fim_mes
```

A execução validada gerou 57 registros mensais.

Comando:

```powershell
python src/build_gold_selic.py
```

Notebook de análise:

```text
notebooks/03_gold_data_analysis.ipynb
```

---

## 8. Amazon S3

Bucket utilizado:

```text
s3://rafael-portfolio-dados-aws/
```

Estrutura lógica:

```text
bronze/
└── selic/
    └── selic_raw.json

silver/
└── selic/
    └── selic.parquet

gold/
└── selic/
    └── selic_mensal.parquet

athena-results/
```

O prefixo `athena-results/` é utilizado pelo Athena para armazenar resultados das consultas.

---

## 9. AWS CLI

Profile utilizado:

```text
selic-dev
```

Validação de identidade:

```powershell
aws sts get-caller-identity --profile selic-dev
```

Uploads:

```powershell
aws s3 cp data/bronze/selic_raw.json s3://rafael-portfolio-dados-aws/bronze/selic/selic_raw.json --profile selic-dev
aws s3 cp data/silver/selic.parquet s3://rafael-portfolio-dados-aws/silver/selic/selic.parquet --profile selic-dev
aws s3 cp data/gold/selic_mensal.parquet s3://rafael-portfolio-dados-aws/gold/selic/selic_mensal.parquet --profile selic-dev
```

---

## 10. IAM e segurança

Usuário IAM do projeto:

```text
pipeline-selic-dev
```

IAM Role do Glue:

```text
AWSGlueServiceRole-SelicCrawler
```

Boas práticas adotadas:

- usuário root sem uso programático;
- MFA no root;
- usuário IAM específico para o projeto;
- profile AWS CLI dedicado;
- IAM Role separada para o Glue;
- credenciais fora do Git;
- `.env` ignorado;
- princípio de menor privilégio nas policies.

### 10.1 Policy de S3

Policy:

```text
PipelineSelicS3Access
```

Permite acesso controlado aos prefixos:

```text
bronze/selic/*
silver/selic/*
gold/selic/*
athena-results/*
```

O prefixo `athena-results/*` foi adicionado para permitir que o Athena grave e leia os resultados das consultas executadas via ODBC e Power BI.

### 10.2 Policy do Athena

Policy:

```text
PipelineSelicAthenaAccess
```

Permite:

- consultar o workgroup `primary`;
- iniciar consultas;
- acompanhar execução;
- ler resultados;
- navegar no catálogo;
- ler metadados do Glue;
- acessar o database `selic_analytics`.

---

## 11. AWS Glue Crawler

Crawler:

```text
crawler-gold-selic
```

Fonte:

```text
s3://rafael-portfolio-dados-aws/gold/selic/
```

Execução:

```text
On demand
```

O crawler identifica:

- formato do arquivo;
- colunas;
- tipos;
- localização no S3.

A execução foi validada com sucesso e registrou a tabela da Gold no Glue Data Catalog.

---

## 12. Glue Data Catalog

Database:

```text
selic_analytics
```

Tabela:

```text
selic
```

Formato:

```text
Parquet
```

O Glue Data Catalog armazena apenas metadados. Os dados físicos permanecem no Amazon S3.

Fluxo:

```text
S3 Gold
   ↓
Glue Crawler
   ↓
Glue Data Catalog
   ↓
selic_analytics.selic
```

---

## 13. Amazon Athena

Configuração:

```text
Region: us-east-1
Data source: AwsDataCatalog
Database: selic_analytics
Table: selic
Workgroup: primary
Query result location: s3://rafael-portfolio-dados-aws/athena-results/
```

Consulta de validação:

```sql
SELECT *
FROM "selic_analytics"."selic"
LIMIT 10;
```

Resultado validado:

```text
10 registros retornados
aproximadamente 1.27 KB verificados
```

---

## 14. Amazon Athena ODBC

Driver instalado no Windows:

```text
Amazon Athena ODBC (x64)
Versão 2.02.00.01
```

Foi criado um DSN local para uso pelo Power BI.

Configuração:

```text
Data Source Name: SelicAthena
Description: Pipeline Selic - Athena
Region: us-east-1
Catalog: AwsDataCatalog
Database: selic_analytics
Workgroup: primary
S3 Output Location: s3://rafael-portfolio-dados-aws/athena-results/
Encryption: NOT_SET
```

Autenticação:

```text
Authentication Type: IAM Profile
AWS Profile: selic-dev
```

Observações:

- `SelicAthena` é apenas o nome local do DSN no Windows;
- `Pipeline Selic - Athena` é uma descrição local;
- `AwsDataCatalog` é o catálogo utilizado pelo Athena;
- `selic_analytics` é o database registrado no Glue Data Catalog.

---

## 15. Power BI

Arquivo:

```text
powerbi/selic_dashboard.pbix
```

Fluxo de conexão:

```text
Power BI
   ↓
Amazon Athena Connector
   ↓
DSN SelicAthena
   ↓
AwsDataCatalog
   ↓
selic_analytics
   ↓
selic
```

Modo utilizado:

```text
Importar
```

A tabela `selic` foi localizada no Navigator do Power BI e carregada com sucesso.

Campos disponíveis:

```text
ano_mes
taxa_media
taxa_minima
taxa_maxima
taxa_fim_mes
```

---

## 16. Problemas encontrados e soluções

### MissingAuthenticationTokenException

Causa:

```text
ODBC sem autenticação válida configurada
```

Solução:

```text
Authentication Type: IAM Profile
AWS Profile: selic-dev
```

### AccessDeniedException em athena:GetWorkGroup

Causa:

```text
pipeline-selic-dev sem permissão para consultar o workgroup primary
```

Solução:

```text
criação da policy PipelineSelicAthenaAccess
```

### Access denied when writing to athena-results

Causa:

A policy S3 permitia `PutObject` apenas em Bronze, Silver e Gold.

Solução:

Adicionar o recurso:

```text
arn:aws:s3:::rafael-portfolio-dados-aws/athena-results/*
```

à policy `PipelineSelicS3Access`.

### NoRegion

Correção:

```powershell
aws configure set region us-east-1 --profile selic-dev
```

### InvalidClientTokenId

Foi necessário revisar e substituir a credencial configurada no profile.

### PyArrow ausente

Correção:

```powershell
python -m pip install pyarrow
```

### Notebook realizando segunda ingestão

A arquitetura foi corrigida para:

```text
ingest_selic.py
      ↓
Bronze
      ↓
Notebook de profiling
```

---

## 17. Decisões técnicas

### Bronze em JSON

Mantém o dado próximo ao formato da fonte.

### Silver e Gold em Parquet

Formato colunar adequado para analytics e Athena.

### Profiling antes da transformação

As regras da Silver foram definidas após análise do dado real.

### Glue Crawler na Gold

A Gold é a camada destinada ao consumo analítico.

### Athena serverless

Permite SQL sobre arquivos no S3 sem provisionamento de servidor de banco de dados.

### ODBC entre Athena e Power BI

Mantém o Athena como camada de consulta e desacopla o Power BI do armazenamento físico no S3.

### Power BI em modo Importar

Adequado ao volume atual do projeto e reduz consultas repetidas ao Athena durante a exploração do relatório.

---

## 18. Git e GitHub

Fluxo utilizado:

```text
main
  ↓
feature/docs branch
  ↓
commit
  ↓
push
  ↓
Pull Request
  ↓
merge
```

Branches utilizadas:

```text
feat/selic-pipeline-glue-athena
docs/improve-project-documentation
```

Commits relevantes:

```text
feat: complete AWS Selic pipeline with Glue and Athena
docs: improve README and add technical documentation
```

---

## 19. Custos e boas práticas

Principais serviços que podem gerar custos:

- Amazon S3;
- AWS Glue Crawler;
- Amazon Athena.

Boas práticas adotadas:

- crawler sob demanda;
- uso de Parquet;
- consultas de teste com `LIMIT`;
- prefixo separado `athena-results/`;
- IAM com permissões específicas;
- Power BI em modo Importar para o cenário atual.

---

## 20. Estado atual

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
Dashboard final         ⏳
Carga incremental       ⏳
boto3                   ⏳
Automação               ⏳
Data Quality            ⏳
```

---

## 21. Próximos passos

- construir os visuais e indicadores do dashboard no Power BI;
- criar medidas DAX;
- validar tipos e formatação no modelo;
- implementar carga incremental;
- automatizar uploads com `boto3`;
- adicionar testes de qualidade de dados;
- evoluir a orquestração;
- adicionar monitoramento;
- documentar a versão final do dashboard.
