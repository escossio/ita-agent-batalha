# ADR 0005 — Jornada de competição autorizada, com contexto incompleto

Decisão: conectar extrato à jornada real sem convertê-lo em calendário futuro. A ampliação foi solicitada explicitamente pelo usuário após a revisão local do inventário e certificação do adapter.

## Fonte e limites de decisão

`extrato_sintetico` fornece cliente de origem, timestamp, mês de referência, tipo/descrição, valor, categorias macro/micro, saldo após lançamento e campos de parcela, todos anuláveis. São observações históricas sintéticas externas. `vlr`/`saldo_apos` passam por Decimal/HALF_UP → int em centavos em Data Access. Fonte FLOAT continua marcada como aproximada; arredondamentos são explícitos.

Com esses dados, a jornada pode apresentar lançamentos na janela autorizada, seus saldos observados/categorias/parcelas e contar registros/observações de saldo. Finance calcula as contagens. Sem catálogo verificado de `tipo`, não somamos créditos como renda nem classificamos débitos como obrigações. Parcelas são contagens observadas, não autorização para criar prestações futuras. Timestamps empatados não permitem escolher saldo atual com segurança.

Não há próxima renda confirmada, data/valor de salário futuro, saldo atual confirmado, compromissos futuros completos, recorrência garantida, limite, produto ou elegibilidade. A projeção fica bloqueada. `FinancialContext.status=INCOMPLETE_FINANCIAL_CONTEXT`, `AgentResponse.status=needs_data`, `financial_result=null`. `observed` contém CompetitionLedger; `calculated` contém somente contagens demonstráveis; `estimates=[]`, `inferences=[]`, `missing` identifica lacunas. Ausência de saldo permanece null, não zero. Janela vazia não prova inexistência do cliente na fonte: retorna ausência de lançamentos na janela. Cliente sem vínculo autorizado é negado antes da consulta.

## Identidade e autorização

Modo competition exige sessão opaca emitida externamente, recebida em Authorization Bearer ou cookie ita_session. Registry privado liga SHA-256 da sessão, validade, customer_id interno, referência de origem, consentimento/contexto e janela máxima. API resolve cliente; frontend/Agent não escolhem id_usuario. Não há login/IdP bancário implementado; essa é uma interface de sessão provisionada pelo operador autorizado, suficiente para o runtime de competição com dados sintéticos, não uma alegação de autenticação bancária produtiva.

API assina prova curta (30s) vinculada a sessão, cliente, correlation ID, janela e gasto solicitado. A chave API–Policy só é montada nesses dois serviços. Agent apenas transporta a prova, que nunca vai ao modelo, logs ou resposta pública. Policy verifica assinatura, expiração, vínculo, revogação e consentimento do registry atual. Prova identifica a requisição; não substitui decisão default deny. Nível financeiro desconhecido permite somente a leitura/análise explicitamente autorizada, sem habilitar produtos. Estado emocional desconhecido/delicado e restrições anteriores continuam bloqueando ou gerando handoff.

Broker reautoriza `finance.project` e a dependência `data.ledger` separadamente. Data autentica a chamada por HMAC com chave exclusiva Broker–Data e reconsulta Policy independentemente antes de abrir BigQuery. MAC cobre rota, correlation ID, timestamp, nonce e corpo. Assinatura válida sem policy não basta. Replay é rejeitado durante 30s no processo Data; cache é limitado e fail closed. Esse cache não é garantia distribuída de exactly-once e não substitui TLS/IAM no GCP; todas as operações atuais são read-only. Host/daemon/configurador de secrets pertencem à base confiável.

Identidades expiradas/revogadas, troca de cliente/janela/valor, prova inválida, chamada direta, schema inválido, timeout e falhas não produzem contexto ou projeção permissivos. Nenhuma ferramenta financeira de escrita foi criada.

## Operação

Modos Data: postgres (jornada DEMO), bigquery (ADC real), bigquery_mock (mesmo adapter, transporte sintético explicitamente identificado). Não existe fallback entre modos. GCP não é dependência dos testes. A proveniência mock não é rotulada como leitura real da competição. Configuração de projeto/dataset/tabela/localização/moeda/unidade/orçamento é externa e exclusiva de Data; Google Cloud project pode ser fornecido por GOOGLE_CLOUD_PROJECT.

Limites: janela até 366 dias (ou menor no vínculo), query até 1000 linhas; paginação/truncamento bloqueiam; payload normalizado até 90 KB para atravessar os envelopes HTTP sem resposta parcial. Finance/Agent não recebem dados acima do limite. O job tem timeout solicitado e limite de bytes; cancelamento do provedor não é garantido, conforme ADR/documentação do adapter.

Rede Data–Policy foi adicionada para reautorização, e egress opcional pertence apenas a Data. Agent continua sem rede/segredo de Data/DB. Segredos de serviço locais são gerados em volumes; no GCP virão de secret store com IAM mínimo. Cookie de sessão deve ser Secure, HttpOnly e SameSite no ambiente TLS; não expor registry ou tokens na UI.

## Certificação

Unit/contract cobrem toda a cadeia em memória com transporte BigQuery sintético e falhas de ADC/timeout/schema/região/fonte. Worker executa duas jornadas por HTTP: DEMO PostgreSQL existente e competição com sessões/chaves efêmeras, mesmas imagens construídas uma vez, sem GCP. Testa negativos, nulos, arredondamento, parcelas, janela vazia, ausência de projeção, acesso Data sem assinatura e com assinatura mas sem policy, revogação, outages/recovery e shutdown limpo. Nenhum deploy GCP nesta passada.
