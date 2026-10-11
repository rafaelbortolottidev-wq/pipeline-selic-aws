# Implementação técnica — Pipeline Selic na AWS

> **Projeto de portfólio | Engenharia de Dados e DataOps**  
> **Versão documentada:** v1.0 (fechamento em andamento)  
> **Região:** `us-east-1`  
> **Fonte:** Banco Central do Brasil — API SGS, série `1178`

## 1. Objetivo e escopo

Construir um pipeline **serverless** para ingestão incremental da taxa Selic, organização em camadas Bronze/Silver/Gold, validação de qualidade, orquestração condicional, consultas SQL e consumo analítico no Power BI. A execução operacional ocorre na AWS; scripts locais são mantidos como recursos de estudo e reprodução.

A implementação combina **engenharia de dados** (PySpark, Parquet, catálogo e SQL) e **DataOps** (Git, testes, CI, CD manual, IAM e observabilidade). Este documento apresenta o que foi implementado, as decisões técnicas, as evidências e as verificações de encerramento.

> **Evidência 01 — Visão geral da arquitetura:** inserir em `docs/images/01-arquitetura.png` um diagrama com os serviços e os dois caminhos: processamento e consumo analítico. Antes de incorporar a imagem, conferir nomes e fluxos.

## 2. Arquitetura operacional

```text
EventBridge Scheduler (diário, 20h — America/Sao_Paulo)
        |
        v
AWS Step Functions — selic-pipeline-orchestration
        |
        v
AWS Lambda — selic-ingestion
        |  atualiza a Bronze no S3 somente se houver dados novos
        v
Choice: bronze_atualizada?
        |                  |
        | false            | true
        v                  v
Succeed              AWS Glue — selic-bronze-to-silver
(sem Glue)                 |  PySpark + Data Quality (quality gate)
                           v
                      S3 Silver (Parquet)
                           |
                           v
                      AWS Glue — selic-silver-to-gold
                           |
                           v
                      S3 Gold (Parquet)
                           |
                           v
                     Glue Data Catalog
                           |
                           v
                      Amazon Athena
                           |
                           v
                        ODBC
                           |
                           v
                        Power BI
```

O **EventBridge Scheduler** dispara a máquina de estados; a **Step Functions** coordena as etapas e desvia o fluxo quando não há registros novos. Os jobs Glue são executados em sequência com integração síncrona (`.sync`). O **CloudWatch** apoia a consulta de logs e métricas, incluindo os resultados de Data Quality.

**Decisão central:** não iniciar Glue em cargas sem novidades, reduzindo processamento e custo desnecessários.

> **Evidência 02 — Step Functions:** print do diagrama da máquina e de uma execução concluída, com a ramificação `bronze_atualizada = false` visível. Ocultar identificadores sensíveis.

## 3. Fonte e organização do Data Lake

A API SGS disponibiliza as colunas de origem `data` e `valor`. Os dados históricos foram organizados assim:

| Camada | Armazenamento | Responsabilidade |
|---|---|---|
| **Bronze** | JSON | Preservar registros próximos à origem e manter o histórico incremental |
| **Silver** | Parquet | Padronizar campos e tipos, validando integridade antes de publicar |
| **Gold** | Parquet | Agregar indicadores mensais para consulta e visualização |

Prefixos do bucket de dados:

```text
s3://rafael-portfolio-dados-aws/
├── bronze/selic/selic_raw.json
├── silver/selic/part-*.snappy.parquet
├── gold/selic/part-*.snappy.parquet
└── athena-results/
```

Os arquivos `part-*` representam os outputs do Spark; os nomes específicos podem variar entre execuções. O uso de Parquet nas camadas analíticas favorece armazenamento colunar e leitura seletiva no Athena.

> **Evidência 03 — Amazon S3:** prints dos prefixos Bronze, Silver e Gold, mostrando formatos e estrutura; não expor dados de credenciais.

## 4. Ingestão incremental com Lambda

**Função:** `selic-ingestion`  
**Tecnologias:** Python, `boto3` (S3) e `urllib` (requisição à API).

A função lê a Bronze, identifica a maior data existente (*watermark*), consulta apenas registros posteriores, combina os novos registros com o histórico, elimina duplicatas, ordena e grava o JSON **somente quando há atualização**.

Contrato relevante para a Step Functions:

```json
{"bronze_atualizada": false, "registros_novos": 0}
```

O exemplo acima representa o caso sem dados novos; quando há novidades, o sinal `bronze_atualizada` deve ser `true`.

**Validado anteriormente:** execução sem novos dados, encerrando a Step Functions sem rodar Glue.

> **Evidência 04 — Lambda:** print da função e de uma execução concluída com o retorno `bronze_atualizada` (ocultar eventuais detalhes sensíveis).

## 5. Transformação Bronze → Silver e Data Quality

**Job:** `selic-bronze-to-silver`  
**Stack:** AWS Glue 5.1, PySpark, Glue Data Quality  
**Configuração utilizada:** workers `G.1X`, quantidade `2`.

Transformações de schema:

```text
data  -> data_referencia (date)
valor -> taxa_selic_aa   (double)
```

**Quality gate:** antes de gravar a Silver, o job avalia as regras:

```text
RowCount > 0
IsComplete "data_referencia"
IsUnique "data_referencia"
IsComplete "taxa_selic_aa"
ColumnValues "taxa_selic_aa" > 0
```

Se houver regra reprovada, o script lança uma exceção e interrompe a gravação da Silver. **Última validação registrada:** 5 regras aprovadas, 0 reprovadas.

**Script versionado:** `src/glue/selic_bronze_to_silver.py`.

> **Evidência 05 — Glue Bronze → Silver:** print da configuração do job, execução bem-sucedida e resultado das cinco regras de Data Quality.

## 6. Transformação Silver → Gold

**Job:** `selic-silver-to-gold`  
**Entrada:** `s3://rafael-portfolio-dados-aws/silver/selic/`  
**Saída:** `s3://rafael-portfolio-dados-aws/gold/selic/`

O script cria `ano_mes` (`yyyy-MM`) e produz:

| Campo | Definição |
|---|---|
| `taxa_media` | Média dos valores no mês |
| `taxa_minima` | Menor taxa registrada no mês |
| `taxa_maxima` | Maior taxa registrada no mês |
| `taxa_fim_mes` | Taxa do último registro disponível no mês, obtida com janela ordenada por `data_referencia` decrescente |

**Última conferência documentada:** 58 linhas mensais, de `2022-01` a `2026-10`. Esse é um retrato histórico da validação, não uma garantia de atualização contínua.

**Script versionado:** `src/glue/selic_silver_to_gold.py`.

> **Evidência 06 — Glue Silver → Gold:** print do job concluído e do dataset Gold no S3.

## 7. Orquestração e agendamento

**Step Functions:** `selic-pipeline-orchestration`  
**Scheduler:** `selic-daily-ingestion`  
**Expressão:** `cron(0 20 * * ? *)` — fuso `America/Sao_Paulo`  
**Destino:** API `StartExecution` da Step Functions, entrada `{}`.

A role `selic-eventbridge-scheduler-role` foi configurada para iniciar a máquina. O Scheduler **não chama a Lambda diretamente**.

**Evidência observada:** execuções da máquina com sucesso, inclusive o caminho sem novos dados. **Validação pendente de comprovação documental:** associar uma execução especificamente ao disparo automático do Scheduler; uma execução manual bem-sucedida não comprova o gatilho temporal.

> **Evidência 07 — Scheduler:** print da programação e do status (`Enabled` ou `Disabled`).  
> **Evidência 08 — Execução automática:** print da execução da Step Functions com horário compatível e evidência da origem Scheduler, se disponível.

## 8. Catálogo, consulta e visualização

**Glue Data Catalog / Crawler**

```text
Crawler: crawler-gold-selic
Database: selic_analytics
Table: selic
Origem: s3://rafael-portfolio-dados-aws/gold/selic/
```

Como o schema e o prefixo da Gold permanecem estáveis, arquivos novos no mesmo prefixo não exigem necessariamente a execução do crawler a cada carga.

**Amazon Athena**

```text
Região: us-east-1
Catálogo: AwsDataCatalog
Database: selic_analytics
Tabela: selic
Workgroup: primary
Resultados: s3://rafael-portfolio-dados-aws/athena-results/
```

Consulta de conferência:

```sql
SELECT
    COUNT(*) AS total_registros,
    MIN(ano_mes) AS primeiro_mes,
    MAX(ano_mes) AS ultimo_mes
FROM "selic_analytics"."selic";
```

Último resultado registrado: `58 | 2022-01 | 2026-10`.

**Power BI** consome a tabela via Amazon Athena ODBC Driver, DSN local `SelicAthena`, autenticação pelo perfil AWS CLI `selic-dev` e modo **Importar**. O arquivo `.pbix` permanece fora do Git.

> **Evidência 09 — Athena:** print da consulta SQL e do resultado.  
> **Evidência 10 — Power BI:** print do relatório final, sem credenciais ou informações privadas.

## 9. Segurança e acesso IAM

Controles empregados:

- Usuário IAM dedicado para desenvolvimento e MFA; root reservado a ações administrativas excepcionais.
- Perfis e credenciais fora do código-fonte e do Git.
- Roles distintas para execução Glue, catálogo, orquestração e agendamento.
- Restrições específicas de acesso para publicação pelo GitHub Actions.

**Roles relevantes:** `AWSGlueServiceRole-SelicETL`, `AWSGlueServiceRole-SelicCrawler`, `selic-eventbridge-scheduler-role` e `GitHubActionsSelicDeployRole`. A Step Functions utiliza uma role de execução própria.

Para o CD, foi configurado um **provedor OIDC do GitHub**, com audiência `sts.amazonaws.com` e política de confiança restringindo o sujeito OIDC personalizado do repositório à branch `main`. A role de deploy possui `s3:PutObject` **somente nos dois objetos dos scripts Glue** no bucket de assets do serviço. Não armazena Access Keys no repositório.

> **Evidência 11 — Segurança:** print da configuração MFA/IAM e da role de CD. Ocultar números de conta, chaves, tokens e outros detalhes desnecessários à divulgação pública.

## 10. CI/CD com GitHub Actions

### 10.1 Integração contínua (CI)

**Arquivo:** `.github/workflows/ci.yml`  
**Gatilhos:** Pull Request para `main` e disparo manual (`workflow_dispatch`).

O job de CI baixa o repositório, configura Python 3.11, verifica sintaxe com `python -m compileall -q src`, instala `pandas` e `pytest` e executa `python -m pytest -v tests/`.

O teste inicial cobre a **transformação local com pandas** (nomes de colunas, tipos, valores e contagem). Não cobre, por si só, execução real de AWS Glue, S3 ou Step Functions. **Evidência:** PR #8 e execuções de CI aprovadas em PRs posteriores.

### 10.2 Entrega contínua (CD)

**Arquivo:** `.github/workflows/cd.yml`  
**Gatilho:** execução manual (`workflow_dispatch`) na branch `main`.

Fluxo:

```text
GitHub (main)
   |
   v
GitHub Actions — Selic - CD
   |
   v
Autenticação OIDC / IAM Role temporária
   |
   v
S3 de scripts do AWS Glue
   |-- scripts/selic-bronze-to-silver.py
   `-- scripts/selic-silver-to-gold.py
```

O CD publica o código versionado dos dois scripts Glue por meio de `aws s3 cp`. **Não inicia os jobs Glue** e não atualiza automaticamente o esquema do Data Catalog. A política IAM da role limita o upload aos dois caminhos necessários.

**Validação registrada:** execução `Selic - CD #5`, concluída com sucesso em **13 segundos**, após ajuste da política de confiança OIDC. Em seguida, foi removida a etapa temporária de diagnóstico, com merge da limpeza na `main`.

> **Evidência 12 — CI:** print de PR com check `Selic - CI` aprovado.  
> **Evidência 13 — CD:** print da execução `Selic - CD #5` com sucesso, preferencialmente incluindo o log da etapa de publicação.

**Limite conhecido:** o CD comprova a entrega dos scripts ao S3, mas não valida funcionalmente uma execução Glue após a publicação.

## 11. Observabilidade e diagnóstico

Logs e métricas podem ser consultados no CloudWatch:

```text
/aws/lambda/selic-ingestion
/aws-glue/jobs/logs-v2
/aws-glue/jobs/output
/aws-glue/jobs/error
/aws-glue/crawlers
```

Para Step Functions, começar pelo histórico e detalhes das execuções da máquina. Para Data Quality, consultar os resultados publicados pelo Glue e as métricas/logs correspondentes.

> **Evidência 14 — Observabilidade:** print de uma execução Lambda/Glue no CloudWatch ou da trilha de execução da Step Functions.

## 12. Reprodução e operação

### 12.1 Ambiente local (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pandas requests pyarrow boto3 pytest
```

- `venv`: cria um ambiente Python isolado.
- `Activate.ps1`: ativa o ambiente no PowerShell.
- `pip install`: instala dependências locais de apoio e testes; **não instala o runtime AWS Glue**.

Os scripts locais de apoio podem ser executados, conforme necessidade:

```powershell
python src/01_ingest_selic.py
python src/02_transform_selic.py
python src/03_build_gold_selic.py
python src/04_upload_s3.py
```

Esses comandos podem criar ou sobrescrever arquivos de dados locais ou publicar no S3; conferir o conteúdo de cada script antes de executar.

### 12.2 AWS CLI

Perfil: `selic-dev`; região utilizada: `us-east-1`.

```powershell
aws sts get-caller-identity --profile selic-dev
```

Esse comando identifica qual principal IAM está autenticado pelo perfil informado. Não incluir credenciais em arquivos versionados.

### 12.3 Testes locais

```powershell
python -m compileall -q src
python -m pytest -v tests/
```

`compileall` verifica sintaxe; `pytest` executa as asserções de teste. Ambos podem rodar sem instanciar serviços da AWS.

### 12.4 Execução manual da Step Functions

Entrada de teste:

```json
{}
```

- **Sem dados novos:** Lambda → Choice → sucesso, sem Glue.
- **Com dados novos:** Lambda → Glue Bronze/Silver → Glue Silver/Gold → sucesso, sujeito às verificações de qualidade.

Executar jobs Glue pode gerar custos; não iniciar apenas para criar capturas de tela.

### 12.5 Publicação de código

Acessar **GitHub → Actions → Selic - CD → Run workflow → `main`**. Esse procedimento envia os dois scripts Glue ao S3 e pode **sobrescrever o código de produção existente**, embora não execute os jobs.

## 13. Controle de custos e encerramento

Após a conferência final, desabilitar o cronograma sem excluir os recursos:

```text
Amazon EventBridge → Scheduler → Cronogramas
→ selic-daily-ingestion → Desabilitar
```

**Status do Scheduler:** precisa ser confirmado no console no momento do encerramento. Não declarar que foi desabilitado sem essa verificação.

Mesmo com o agendamento desativado, ainda podem existir custos residuais de armazenamento S3, logs e consultas/execuções manuais. Usar Billing / Cost Explorer para acompanhamento.

### Checklist de fechamento

- [x] Ingestão incremental com Lambda e Bronze no S3
- [x] Jobs Glue Bronze → Silver e Silver → Gold
- [x] Regras de Data Quality na Silver
- [x] Step Functions com desvio sem dados novos
- [x] EventBridge Scheduler configurado
- [x] Glue Data Catalog, Athena e Power BI conectados
- [x] Scripts Glue versionados no GitHub
- [x] CI: sintaxe e teste local com pytest aprovados
- [x] CD: publicação manual via OIDC, execução #5 bem-sucedida
- [ ] Registrar evidências visuais finais em `docs/images/`
- [ ] Comprovar documentalmente execução iniciada pelo Scheduler, se desejado
- [ ] Confirmar e documentar status **desabilitado** do Scheduler
- [ ] Publicar a documentação consolidada na `main`

## 14. Evoluções futuras (fora do escopo v1.0)

- Testes automatizados adicionais para transformações PySpark e integração entre serviços.
- Versionamento da definição ASL da Step Functions e, opcionalmente, infraestrutura como código (Terraform/CloudFormation).
- Alertas avançados, melhorias de observabilidade, monitoramento de custos e governança.
- Redshift, Lake Formation, EMR, Iceberg, Kinesis/streaming, DMS e Airflow/MWAA, conforme objetivos dos próximos projetos.

---

**Nota de divulgação:** imagens devem comprovar implementações reais; não incluir senhas, tokens, chaves de acesso, dados privados ou detalhes de segurança desnecessários em um repositório público.
