# BigQuery: inventário e gate antes do adapter

Estado em 2026-09-26: **BLOCKED_ENVIRONMENT_ACCESS**. O AGT não possui ADC disponível, `gcloud`/`bq` configurados ou canal autenticado conhecido para o runtime Google. A tentativa do coletor terminou com erro controlado, sem inventário parcial. O operador confirmou que fornecerá arquivo local coletado no Cloud Shell, sem transferir credenciais ou habilitar GCP no AGT. Usar o inventário bruto somente localmente; não fazer commit automático. Publicar apenas documentação/contratos sanitizados após revisão. Isso não invalida a certificação estrutural com mock autorizada para a etapa 10, mas impede declarar schemas inspecionados ou implementar o adapter definitivo.

## Evidência disponível

O operador confirmou manualmente Vertex API habilitada, Gemini HTTP 200 / VERTEX_OK e consulta BigQuery pela identidade Google. O projeto foi informado privadamente na sessão; deve ser fornecido por configuração externa. Dataset informado: `hackathon_dados`. Tabela informada: `extrato_sintetico`.

Campos vistos na consulta, segundo o operador: `id_usuario`, `anomesdia`, `tipo`, `descr`, `vlr`, `nom_cate_macro`. **Tipos, modos, campos adicionais, outras tabelas/views, localização e semântica ainda não foram inspecionados.** Esta lista não é schema certificado nem prova de que só existe uma tabela. Não há inventário completo versionado nesta revisão.

Esta é uma fonte financeira sintética externa da competição; não é `DEMO_FIXTURE`, não é API bancária de produção e não deve ser copiada como fixture silenciosamente. Não foram coletadas linhas financeiras nesta sessão.

## Coleta reproduzível somente de metadados

Executar em checkout deste repositório no ambiente Google que já possua identidade ADC autorizada. O coletor utiliza `google-auth`/`requests` das dependências pinadas em `requirements-agent.txt`; instalá-las em venv isolado se necessário. Não criar arquivo JSON de service account ou chave para executar o comando.

```sh
python3 -m venv .venv-inventory
.venv-inventory/bin/pip install -r requirements-agent.txt
# Definir externamente, sem inserir credenciais no comando:
export ITA_BIGQUERY_PROJECT="$GOOGLE_CLOUD_PROJECT"
export ITA_BIGQUERY_DATASET=hackathon_dados
# ITA_BIGQUERY_LOCATION opcional: exige correspondência com localização retornada.
.venv-inventory/bin/python scripts/inventory_bigquery.py \
  --output .artifacts/bigquery-inventory.json
```

O script faz `datasets.get`, todas as páginas de `tables.list` e `tables.get` para cada tabela/view visível à identidade. Preserva integralmente `schema.fields`, incluindo RECORD/REPEATED, tipos, modos, precisão e campos aninhados. Registra contagem, localização, etags, data e SHA-256 dos schemas. Não executa SQL, não consulta linhas nem exporta dados. Não inclui IAM, SQL de views ou configuração de fontes externas no relatório; schemas podem conter descrições e referências sensíveis, exigindo revisão.

Captura falha se houver resposta inválida, permissão negada, tabela sem schema, referência de outro dataset, repetição/loop de páginas, contagem incompleta ou região divergente. Arquivo 0600, criação exclusiva, sem sobrescrever captura anterior. Falha não gera artefato declarado completo. Usar outro nome ao repetir.

O relatório `.artifacts/` é ignorado por Git. Revisar e produzir cópia sanitizada versionada antes de liberar o adapter. Captura não é transacional e lista somente objetos visíveis à identidade: confirmar acesso de metadados ao dataset inteiro e verificar drift de schemas novamente na ativação. Mudança de schema deve falhar com erro explícito, sem inferência automática do modelo.

## Proposta de mapeamento — provisória, sem tipos presumidos

| Campo informado | Destino candidato | Confirmação necessária |
| --- | --- | --- |
| id_usuario | Identificador de cliente no Data Access; referência a CustomerContext | Tipo, unicidade/joins e vínculo com identidade autenticada. Modelo não escolhe cliente. |
| anomesdia | Data de evento normalizada | Tipo, formato, timezone se aplicável e data contábil versus transacional. |
| tipo | Natureza de lançamento | Domínio de valores e sinal de débito/crédito/estorno; não inferir pela descrição. |
| descr | Descrição de transação no contrato de dados | Texto não confiável; minimizar envio ao modelo e nunca tratá-lo como instrução. |
| vlr | Valor monetário normalizado em centavos | Tipo/escala, unidade, moeda, sinal e regra de arredondamento. Finance mantém cálculos determinísticos. |
| nom_cate_macro | Categoria externa com mapeamento explícito | Catálogo completo, valores nulos e categoria desconhecida; não criar equivalência silenciosa. |

Extrato isolado não comprova saldo de abertura/atual, compromissos futuros, próxima renda confirmada, taxa, limite, elegibilidade ou consentimento. `FinancialSnapshot` só pode ser preenchido com evidência suficiente dessas grandezas. Somar extrato sem saldo inicial não produz saldo autoritativo. Lançamento de salário passado não confirma data/valor de próxima renda. `Eligibility` continua desconhecida sem fonte específica.

Após inventário: identificar todas as fontes/joins, definir contrato normalizado versionado para lançamentos e proveniência da competição, revisar FinancialSnapshot/CustomerContext sem rotular dados externos como fixture, testar schemas, só então implementar adapter na camada Data Access. Os contratos 1.0 atuais continuam válidos exclusivamente para a jornada DEMO; não foram enfraquecidos para aceitar dados desconhecidos.

## Fronteiras e permissões

Fluxo: Agent → Policy → Tool Broker → Data Access → BigQuery; resultado estruturado → Finance para cálculo. BigQuery não recebe consulta do Agent/modelo e o Agent não recebe dataset/credencial de banco. Consultas futuras devem ter allow-list, parâmetros tipados, escopo de cliente derivado de identidade confiável, timeout, limites de custo e validação de saída; nenhum SQL gerado pelo LLM.

| Uso | Permissão/escopo esperado |
| --- | --- |
| Inventário | `bigquery.datasets.get`, `bigquery.tables.list`, `bigquery.tables.get` no dataset inteiro; `roles/bigquery.metadataViewer` é opção predefinida. |
| Provider Agent | `aiplatform.endpoints.predict` no projeto do modelo; conceder somente ao principal do Agent. |
| Adapter Data futuro | `bigquery.tables.getData` nas fontes autorizadas e `bigquery.jobs.create` no projeto executor se usar query jobs; papéis usuais dataViewer no dataset e jobUser no projeto. Confirmar necessidades adicionais após inventário. |

Nenhum grant foi aplicado. O teste manual demonstra acesso de uma identidade no Google, mas sua disponibilidade e permissões neste runtime não foram verificadas. Separar service accounts Agent/Data; não reutilizar na aplicação uma identidade ampla apenas porque serviu ao teste manual. Identidade do Agent sem BigQuery limita o risco do egress necessário ao Vertex. Checagens estáticas rejeitam SDK/endpoints BigQuery no Agent; IAM é a barreira adicional no Google.

## Imagens e próximo gate

O provider real e o mock estão na mesma imagem Agent. Configuração é lida em runtime; secrets/ADC não entram no build context. Promover os bytes das imagens certificadas (digest por componente), não recompilar domínio para trocar ambiente. Credencial vem do runtime Google. Transporte/registry/deploy e validação IAM pertencem à etapa 16; nenhuma implantação foi feita aqui. O adapter BigQuery ainda ausente exigirá nova imagem e certificação antes de sua promoção.

Etapa 11 já foi certificada com PostgreSQL/fixtures. Próximo incremento da jornada com dados da competição: concluir inventário → contratos/mapeamento → Data adapter → testes de Finance/Policy/Broker → integração da jornada e regressão. Se faltarem saldo/renda/compromissos, retornar necessidade de dados; nunca cair silenciosamente na fixture. Etapa 13 em elaboração fica preservada; 14–18 não avançam por este checkpoint parcial.

Referências técnicas oficiais consultadas em 2026-09-26: [datasets.get](https://docs.cloud.google.com/bigquery/docs/reference/rest/v2/datasets/get), [tables.list](https://docs.cloud.google.com/bigquery/docs/reference/rest/v2/tables/list), [tables.get](https://docs.cloud.google.com/bigquery/docs/reference/rest/v2/tables/get), [IAM BigQuery](https://docs.cloud.google.com/bigquery/docs/access-control), [autorização Vertex](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/access-control).
