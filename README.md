# Pipeline Selic — Engenharia de Dados na AWS

Projeto de portfólio que implementa um pipeline de dados na AWS, desde a **ingestão incremental** da taxa Selic até o **consumo analítico**, com processamento PySpark, qualidade de dados, orquestração, observabilidade e CI/CD.

## Arquitetura

```text
EventBridge Scheduler (agendamento diário)
          ↓
AWS Step Functions
          ↓
AWS Lambda → Amazon S3 / Bronze (JSON)
          ↓
Há dados novos?
    ├── Não → encerra sem executar Glue
    └── Sim
          ↓
AWS Glue / PySpark + Data Quality → Silver (Parquet)
          ↓
AWS Glue / PySpark → Gold (Parquet)
          ↓
Glue Data Catalog → Athena → Power BI
```

A ingestão incremental consulta a **API SGS do Banco Central (série 1178)**. A Lambda utiliza a última data disponível na Bronze como referência (*watermark*) e evita reprocessamento quando não há novos registros.

**[ESPAÇO PARA PRINT 01 — Diagrama da arquitetura AWS]**

## Camadas do Data Lake

| Camada | Formato | Finalidade |
|---|---|---|
| **Bronze** | JSON | Preservação do histórico obtido na API |
| **Silver** | Parquet | Padronização de colunas/tipos e validações de qualidade |
| **Gold** | Parquet | Indicadores mensais para análise |

A Gold disponibiliza `ano_mes`, `taxa_media`, `taxa_minima`, `taxa_maxima` e `taxa_fim_mes`.

Na última validação registrada, a tabela analítica continha **58 meses (2022-01 a 2026-10)**.

## Serviços e competências demonstradas

| Área | Tecnologias e implementação |
|---|---|
| Ingestão | Python, boto3, AWS Lambda e API REST |
| Armazenamento | Amazon S3 e arquitetura Bronze/Silver/Gold |
| Processamento | AWS Glue ETL, PySpark e Parquet |
| Qualidade | AWS Glue Data Quality com 5 regras de validação |
| Orquestração | AWS Step Functions, execução condicional e EventBridge Scheduler |
| Consulta e BI | Glue Data Catalog, Crawler, Athena, ODBC e Power BI |
| Observabilidade | CloudWatch Logs, EventBridge Rules e SNS |
| Segurança | IAM, MFA, roles por serviço e OIDC para GitHub Actions |
| DataOps | Git, Pull Requests, pytest e GitHub Actions (CI/CD) |

## Data Quality

O job **Bronze → Silver** utiliza cinco regras de qualidade:

```text
RowCount > 0
IsComplete "data_referencia"
IsUnique "data_referencia"
IsComplete "taxa_selic_aa"
ColumnValues "taxa_selic_aa" > 0
```

A publicação da Silver é interrompida se alguma regra falhar. Na última validação registrada: **5 aprovadas, 0 reprovadas**.

## Automação e monitoramento

O agendamento `selic-daily-ingestion` foi configurado para iniciar a máquina `selic-pipeline-orchestration` às **20h (America/Sao_Paulo)**. A Step Functions executa a Lambda e só aciona os jobs Glue quando há novos dados.

O CloudWatch mantém os grupos de logs do projeto com **retenção de 14 dias**. A regra EventBridge `selic-glue-failure-alert` encaminha eventos de falha dos jobs Glue ao tópico SNS `selic-pipeline-alertas`. **A entrega de e-mail pelo SNS foi testada; o alerta de falha de ponta a ponta ainda não foi validado por uma falha real.**

## CI/CD com GitHub Actions

- **CI — `.github/workflows/ci.yml`:** executada automaticamente em Pull Requests para `main`; valida a sintaxe Python e roda testes com `pytest` da transformação local Bronze → Silver.
- **CD — `.github/workflows/cd.yml`:** execução manual na branch `main`, com autenticação **GitHub OIDC → IAM Role**, sem Access Keys armazenadas no GitHub. Publica os scripts PySpark versionados nos caminhos S3 dos dois jobs Glue, **sem executar os jobs**.

A primeira execução bem-sucedida do CD publicou os dois scripts no S3. A verificação de sintaxe e o teste unitário da transformação local também foram aprovados. Esses testes não substituem testes integrados do pipeline AWS.

**[ESPAÇO PARA PRINT 02 — GitHub Actions: CI e CD aprovados]**

## Estrutura principal do repositório

```text
pipeline-selic-aws/
├── .github/workflows/
│   ├── ci.yml
│   └── cd.yml
├── docs/
│   └── IMPLEMENTACAO_TECNICA.md
├── src/
│   ├── glue/
│   │   ├── selic_bronze_to_silver.py
│   │   └── selic_silver_to_gold.py
│   ├── 01_ingest_selic.py
│   ├── 02_transform_selic.py
│   ├── 03_build_gold_selic.py
│   └── 04_upload_s3.py
├── tests/
│   └── test_transform_selic.py
├── notebooks/
└── README.md
```

A estrutura acima mostra os principais arquivos confirmados no projeto. Código de infraestrutura e outros artefatos ainda devem ser verificados antes de serem listados como versionados. Dados locais e o arquivo `.pbix` não são publicados no repositório.

## Evidências e documentação técnica

Detalhes de arquitetura, operação, políticas de segurança, validações e espaços identificados para capturas reais da AWS estão em:

**[Implementação técnica do pipeline](docs/IMPLEMENTACAO_TECNICA.md)**


