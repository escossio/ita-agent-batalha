# BigQuery: inventário inspecionado e contrato de dados

Estado: **LOCAL_SCHEMA_REVIEWED**. Inventário de metadados gerado pelo operador no Cloud Shell em 2026-09-26T23:33:13Z, recebido e inspecionado localmente no AGT. Foram conferidos dataset.json, tables.json e todos os arquivos tables/*.json: referências de projeto/dataset/tabela e localização coincidem; a listagem contém **uma tabela**, `extrato_sintetico`, com **11 campos**, todos `NULLABLE`. Localização informada no metadata: `us-central1`; continua configuração externa no adapter.

O bruto permanece fora do Git e do contexto Docker. Contém metadados de acesso/identidade que não são necessários à publicação. Esta documentação contém somente estrutura revisada e decisões do adapter; nenhum IAM binding, principal, URL privada, identificador de projeto ou linha financeira foi copiado. A inspeção descreve o snapshot fornecido e a visibilidade da identidade coletora, não uma garantia sobre objetos ocultos ou alterações posteriores. Nenhuma chamada GCP foi feita no AGT nesta revisão.

## Schema e mapeamento sanitizados

| Campo da fonte | Tipo BigQuery | Modo | Destino/validação em Data Access |
| --- | --- | --- | --- |
| id_usuario | STRING | NULLABLE | Seleção por parâmetro e verificação por linha; vínculo ao customer_id deve vir de identidade confiável, não do modelo |
| anomesdia | TIMESTAMP | NULLABLE | occurred_at UTC; REST segundos decimais → micros inteiros → timestamp, sem float |
| anomes | INTEGER | NULLABLE | source_year_month, YYYYMM válido; preservado separadamente da data UTC |
| tipo | STRING | NULLABLE | source_type opaco; catálogo/sinal ainda não verificados |
| descr | STRING | NULLABLE | description; texto não confiável, sem execução/interpretação como instrução |
| vlr | FLOAT | NULLABLE | amount_cents inteiro assinado ou null; conversão decimal no Data Access |
| nom_cate_macro | STRING | NULLABLE | macro_category externa, sem classificação inventada |
| nom_cate_micro | STRING | NULLABLE | micro_category externa, sem classificação inventada |
| saldo_apos | FLOAT | NULLABLE | balance_after_cents inteiro assinado ou null; observação após lançamento, não saldo atual automaticamente |
| parcela_atual | FLOAT | NULLABLE | installment_number inteiro exato ou null; nunca multiplicar por 100/arredondar |
| parcela_total | FLOAT | NULLABLE | installment_count inteiro exato ou null; nunca multiplicar por 100/arredondar |

Moeda e unidade não constam no schema. O adapter exige configuração explícita BRL/unidade major antes de converter reais para centavos; não há default silencioso. Esta é fonte **sintética externa da competição**, com proveniência `COMPETITION_SYNTHETIC_BIGQUERY`, diferente de `DEMO_FIXTURE`.

## Contratos e normalização

`LedgerReadRequest` e `CompetitionLedger` 1.0 têm schemas versionados, validação estrita e extras proibidos. Requisição interna contém correlation ID, customer_id, referência opaca do usuário na fonte e janela UTC de até 366 dias. O mapeamento de identidade é responsabilidade do chamador confiável em Data Access. Nenhum desses campos representa autorização.

`CompetitionLedger` preserva campos anuláveis, origem aproximada FLOAT64, sinal original e flags de arredondamento de cada campo monetário. Todos os valores monetários que saem do Data Access são int em centavos ou null. Não atravessam float/Decimal/string monetária para Finance. Null não vira zero. NaN, infinito, booleano, texto inválido e excesso de limite falham. Por valor: Decimal da representação textual → ×100 → ROUND_HALF_UP → int, antes de qualquer agregação. Detalhes e limites em [ADR 0004](../adr/0004-competition-ledger-normalization.md).

Parcelas são contagens, não valores monetários: exigem número finito, não negativo e sem parte fracionária. Zero é preservado sem inventar semântica; campos podem estar ausentes independentemente. Se ambos existem, parcela atual não pode exceder total. Sem ID de transação no schema, duplicatas não são eliminadas e timestamps empatados não definem qual saldo é o último.

O resultado sempre declara `complete_financial_context=false`. `FinancialSnapshot`, Eligibility e CustomerContext existentes não foram enfraquecidos ou preenchidos por inferência do extrato. Saldo após lançamento não garante saldo atual; empréstimo/crédito histórico não é renda recorrente; não há data da próxima renda, compromissos futuros, elegibilidade, taxa, limite ou consentimento nesse schema.

## Adapter e fronteiras

`services/data/bigquery.py` implementa leitura REST/ADC substituível por transporte mock. Antes de cada consulta, verifica referência da tabela, tipo TABLE, região e todos os campos/tipos/modos; schema divergente bloqueia a leitura. Apenas SELECT fixo com colunas allow-listed, filtro de cliente e janela por parâmetros nomeados. Projeto/dataset/tabela vêm de configuração validada, nunca de entrada do modelo.

Limites: maximumBytesBilled obrigatório, janela de 366 dias, até 1000 linhas, respostas HTTP até 4 MiB, timeout HTTP, timeout de job solicitado e correlation ID na chamada. Resultado paginado/truncado, job incompleto, erro, resposta de outro cliente ou fora da janela falham; não se entrega histórico parcial como completo. Sem retry de query, consulta livre, writes ou fallback para fixture. Para volume maior, reduzir janela com estratégia explícita em incremento posterior. Timeout de job é uma tentativa de interrupção pelo BigQuery, não garantia de custo zero; orçamento de bytes continua obrigatório.

**Estado de integração:** adapter e contratos implementados, testes locais/CI com transporte sintético; sem chamada real, endpoint novo, tool nova, egress Data ou alteração de grants. A jornada certificada continua PostgreSQL/DEMO. O adapter não está conectado automaticamente a data.snapshot, porque faltam identidade autorizada, regras semânticas e dados para a projeção. Nenhum resultado de extrato é fornecido ao Agent/Finance por atalho.

A ativação deve seguir Agent → Policy → Tool Broker → Data Access → BigQuery; Finance continua sendo autoridade dos cálculos. Agent/modelo nunca consultam BigQuery. Não basta escolher um customer_id pelo frontend nem usar o registro DEMO de Policy como autorização para dados externos. Antes de ligar uma tool: mapear identidade autenticada no servidor, definir decisão Policy e contrato de resultado, integrar Broker e auditar, testar bypass e regressão. Isso preserva os gates anteriores.

## Configuração e permissões futuras

Todas obrigatórias para construir o adapter a partir do ambiente: ITA_BIGQUERY_PROJECT, ITA_BIGQUERY_DATASET, ITA_BIGQUERY_TABLE, ITA_BIGQUERY_LOCATION, ITA_BIGQUERY_CURRENCY=BRL, ITA_BIGQUERY_MONEY_UNIT=major e ITA_BIGQUERY_MAX_BYTES_BILLED. Exemplo sem valores privados em .env.example. São parâmetros do Data Access; não são passados ao Agent. As variáveis sozinhas não ativam uma rota de leitura.

ADC por identidade do runtime Google, sem token/chave/JSON de service account no AGT/repo/imagem. Dependências HTTP/ADC pinadas em requirements-gcp.txt, instaladas apenas em Agent e Data. Domain/Policy/Finance não importam Google. A imagem Data contém o adapter testado e pode ser promovida por digest, sem recompilar lógica para trocar configuração. Nenhum deploy foi realizado.

| Uso | Permissões esperadas |
| --- | --- |
| Inventário | bigquery.datasets.get, bigquery.tables.list, bigquery.tables.get no dataset; metadataViewer é opção predefinida |
| Data adapter | bigquery.tables.get e bigquery.tables.getData nas fontes autorizadas, bigquery.jobs.create no projeto executor; dataViewer no dataset + jobUser no projeto são opções predefinidas |
| Agent provider | aiplatform.endpoints.predict; identidade separada, sem permissões BigQuery |

Nenhum grant foi aplicado ou auditado no runtime Google. O acesso manual relatado pelo operador não comprova o menor privilégio de futuras service accounts.

## Repetir inventário sem publicar bruto

No ambiente Google já autorizado, instalar requirements-gcp.txt em venv e executar scripts/inventory_bigquery.py com projeto/dataset externos. O coletor anterior permanece disponível: somente metadata, arquivo exclusivo 0600 em .artifacts/, sem SQL/linhas. Revisar localmente cada nova captura; publicar apenas documentação/contratos sanitizados após aprovação dos checks. O bruto recebido nesta revisão não foi transformado nem sobrescrito.

Referências oficiais: [tipos aproximados e nulabilidade](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/data-types), [jobs.query e limites](https://docs.cloud.google.com/bigquery/docs/reference/rest/v2/jobs/query), [tables.get](https://docs.cloud.google.com/bigquery/docs/reference/rest/v2/tables/get), [IAM BigQuery](https://docs.cloud.google.com/bigquery/docs/access-control).
