# Documentação Técnica — Pipeline AWS para Análise Histórica da Selic

## 1. Visão geral

Este projeto implementa um pipeline de Engenharia de Dados para ingestão, tratamento, agregação, armazenamento, catalogação e consulta de dados históricos da taxa Selic.

O fluxo foi construído com Python e serviços AWS, seguindo uma arquitetura em camadas Bronze, Silver e Gold.

```text
API Banco Central
        ↓
Python
        ↓
Bronze
        ↓
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
│
├── notebooks/
│   ├── 01_bronze_data_profiling.ipynb
│   ├── 02_silver_data_validation.ipynb
│   └── 03_gold_data_analysis.ipynb
│
├── src/
│   ├── ingest_selic.py
│   ├── transform_selic.py
│   └── build_gold_selic.py
│
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

A ingestão é executada pelo script:

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

Antes de definir as transformações da camada Silver, os dados da Bronze foram analisados no notebook:

```text
notebooks/01_bronze_data_profiling.ipynb
```

O notebook lê diretamente a Bronze:

```python
import pandas as pd

df = pd.read_json("../data/bronze/selic_raw.json")
```

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

O profiling permitiu definir as regras da camada Silver com base no dado real.

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

O formato Parquet foi utilizado por ser eficiente para processamento analítico e consultas colunares.

Comando:

```powershell
python src/transform_selic.py
```

A camada é validada no notebook:

```text
notebooks/02_silver_data_validation.ipynb
```

---

## 7. Camada Gold

A Gold prepara os dados para consumo analítico.

Arquivo:

```text
data/gold/selic_mensal.parquet
```

Script:

```text
src/build_gold_selic.py
```

A granularidade foi alterada de diária para mensal.

Indicadores gerados:

```text
ano_mes
taxa_media
taxa_minima
taxa_maxima
taxa_fim_mes
```

Fluxo:

```text
Silver diária
     ↓
agrupamento por ano/mês
     ↓
Gold mensal
```

A execução validada gerou:

```text
57 registros
```

Comando:

```powershell
python src/build_gold_selic.py
```

A Gold pode ser analisada por meio de:

```text
notebooks/03_gold_data_analysis.ipynb
```

---

## 8. Amazon S3

As três camadas foram armazenadas no Amazon S3.

Bucket:

```text
s3://rafael-portfolio-dados-aws/
```

Estrutura:

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

---

## 9. AWS CLI

Foi configurado um perfil dedicado:

```text
selic-dev
```

Para verificar a identidade autenticada:

```powershell
aws sts get-caller-identity --profile selic-dev
```

### Upload da Bronze

```powershell
aws s3 cp data/bronze/selic_raw.json s3://rafael-portfolio-dados-aws/bronze/selic/selic_raw.json --profile selic-dev
```

### Upload da Silver

```powershell
aws s3 cp data/silver/selic.parquet s3://rafael-portfolio-dados-aws/silver/selic/selic.parquet --profile selic-dev
```

### Upload da Gold

```powershell
aws s3 cp data/gold/selic_mensal.parquet s3://rafael-portfolio-dados-aws/gold/selic/selic_mensal.parquet --profile selic-dev
```

Para validar arquivos armazenados:

```powershell
aws s3 ls s3://rafael-portfolio-dados-aws/gold/selic/ --profile selic-dev
```

---

## 10. IAM e segurança

Foi utilizado um usuário IAM específico para o projeto.

```text
pipeline-selic-dev
```

O usuário root não é utilizado pelo pipeline.

Também foi configurada uma IAM Role específica para o AWS Glue Crawler:

```text
AWSGlueServiceRole-SelicCrawler
```

Boas práticas adotadas:

- MFA no usuário root;
- root sem Access Keys ativas;
- usuário IAM específico;
- profile AWS CLI dedicado;
- IAM Role separada para o Glue;
- credenciais fora do Git;
- arquivos sensíveis ignorados pelo `.gitignore`.

---

## 11. AWS Glue Crawler

Foi criado o Crawler:

```text
crawler-gold-selic
```

Fonte analisada:

```text
s3://rafael-portfolio-dados-aws/gold/selic/
```

Execução:

```text
On demand
```

O Crawler identifica automaticamente:

- formato do arquivo;
- colunas;
- tipos;
- localização no S3.

Execução validada:

```text
Status: Completed
Duração aproximada: 1 minuto
Table changes: 1
```

---

## 12. Glue Data Catalog

Foi criado o database:

```text
selic_analytics
```

O Glue Data Catalog não armazena os dados físicos.

Ele armazena os metadados necessários para que outros serviços possam localizar e interpretar os arquivos do S3.

O Crawler registrou a tabela:

```text
selic
```

Fluxo:

```text
S3 Gold
   ↓
Crawler
   ↓
Glue Data Catalog
   ↓
selic_analytics.selic
```

---

## 13. Amazon Athena

O Amazon Athena foi utilizado para consultar a camada Gold diretamente no S3 utilizando SQL.

Configuração:

```text
Data source: AwsDataCatalog
Database: selic_analytics
Table: selic
```

Consulta de teste:

```sql
SELECT *
FROM "selic_analytics"."selic"
LIMIT 10;
```

Resultado:

```text
10 registros retornados
aproximadamente 1.27 KB verificados
```

O Athena foi configurado para armazenar os resultados das queries em:

```text
s3://rafael-portfolio-dados-aws/athena-results/
```

Fluxo:

```text
Athena
   ↓
Glue Data Catalog
   ↓
S3 Gold
   ↓
resultado SQL
```

---

## 14. Ambiente Python

O projeto utiliza um ambiente virtual:

```text
.venv
```

Principais bibliotecas:

```text
pandas
requests
pyarrow
```

O `pyarrow` é necessário para leitura e escrita de arquivos Parquet.

---

## 15. Git e GitHub

O projeto utiliza versionamento com Git.

Fluxo aplicado:

```text
main
  ↓
feature branch
  ↓
commit
  ↓
push
  ↓
Pull Request
  ↓
merge
```

Branch utilizada na implementação principal:

```text
feat/selic-pipeline-glue-athena
```

Commit principal:

```text
feat: complete AWS Selic pipeline with Glue and Athena
```

O Pull Request foi posteriormente integrado à `main`.

---

## 16. .gitignore

O projeto evita versionar arquivos locais, temporários e sensíveis.

```gitignore
# Ambiente virtual Python
.venv/

# Dados gerados pelo pipeline
data/

# Cache do Python
__pycache__/
*.pyc

# Cache dos notebooks
.ipynb_checkpoints/

# Arquivos de ambiente/segredos
.env
```

---

## 17. Problemas encontrados e soluções

### AWS CLI sem região

Erro:

```text
NoRegion
```

Correção:

```powershell
aws configure set region us-east-1 --profile selic-dev
```

### Credencial inválida

Erro:

```text
InvalidClientTokenId
```

Foi necessário revisar e substituir a Access Key configurada.

### Perfil autenticando como root

O comando:

```powershell
aws sts get-caller-identity --profile selic-dev
```

permitiu identificar quando as credenciais configuradas não correspondiam ao usuário IAM esperado.

### PyArrow ausente no ambiente virtual

Erro ao gerar Parquet.

Correção:

```powershell
python -m pip install pyarrow
```

### Notebook realizando uma segunda ingestão

Inicialmente o notebook consultava a API diretamente.

A arquitetura foi corrigida para:

```text
ingest_selic.py
      ↓
Bronze
      ↓
Notebook de profiling
```

Dessa forma existe apenas uma ingestão oficial.

---

## 18. Decisões técnicas

### JSON na Bronze

Mantém o dado próximo ao formato da fonte.

### Parquet na Silver e Gold

Reduz armazenamento e leitura em cenários analíticos e é adequado para Athena.

### Profiling antes da transformação

As regras da Silver foram definidas somente após análise dos dados brutos.

### Crawler apenas na Gold

A Gold é a camada destinada ao consumo analítico e, portanto, foi a primeira camada catalogada para o Athena.

### Crawler On Demand

Evita execuções desnecessárias e ajuda no controle de custos.

---

## 19. Custos e boas práticas

Serviços utilizados podem gerar custos, principalmente:

- AWS Glue Crawler;
- Amazon Athena;
- Amazon S3.

Boas práticas adotadas:

- Crawler executado sob demanda;
- Parquet utilizado para reduzir leitura no Athena;
- consultas de teste com `LIMIT`;
- separação de `athena-results/`;
- monitoramento do volume verificado pelo Athena.

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
Power BI                ⏳
Carga incremental       ⏳
boto3                   ⏳
Automação               ⏳
Data Quality            ⏳
```

---

## 21. Próximos passos

- conectar o Amazon Athena ao Power BI;
- criar consultas analíticas adicionais;
- implementar carga incremental;
- utilizar `boto3` para integração Python → AWS;
- eliminar uploads manuais;
- adicionar testes de qualidade;
- automatizar a execução do pipeline;
- adicionar monitoramento;
- criar um diagrama visual final da arquitetura.