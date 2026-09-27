# Estado da implantação

Data: 2026-09-26. Repositório público: https://github.com/escossio/ita-agent-batalha.

## Instrução vigente

Somente artefatos locais; GitHub/repositório é a fonte versionada principal. Google Drive não é dependência, runtime ou bloqueio; não reconstruir integração.
Voz e Tom: **SOURCE_PENDING_LOCAL_COPY**, dependência documental não bloqueante para estrutura e preparação. Não inventar conteúdo; regras específicas só serão definitivas com fonte local versionada.

## Etapas

| Etapa | Estado | Evidência |
| --- | --- | --- |
| 1 | Gate estrutural aprovado com pendência documental | Três fontes congeladas; hashes/ZIP/XML/sanitização conferidos; manifesto atualizado conforme instrução do usuário |
| 2 | Concluída | PR #1 integrado; seis checks e CodeQL verdes no commit 535da98; merge 2aa4652 |
| 3 | Concluída | PR #2; SHA d2c8eac validado em worker e Actions; merge 01945d7 |
| 4 | Concluída | PR #3; SHA 5a6b62d com checks/worker aprovados; merge ad360a3 |
| 5 | Concluída | PR #4; SHA 0403328, CI/worker aprovados; merge f0e5461 |
| 6 | Concluída | PR #5; SHA 9c585df aprovado em CI/worker; merge 96f1b54 |
| 7 | Concluída | PR #6; SHA dd04465 aprovado em CI/worker, inclusive Policy HTTP; merge 5a0fa23 |
| 8 | Concluída | PR #7; SHA e7f10e7, 55 testes/CI/worker aprovados; merge e5401f3 |
| 9 | Concluída | PR #8; SHA 6313b9b aprovado em CI/worker; 66 testes; merge 78845aa |
| 10 | Concluída com mock autorizado | PR #10; SHA 7c6e99f; 76 testes/CI/worker aprovados; merge 40e0ca8. Vertex real aguarda ADC externo |
| 11 | Concluída | PR #11; SHA 06667df; 78 testes e integração PostgreSQL/Web em CI/worker; merge 40ea31b |
| 12 | Concluída | PR #12; SHA 9b94506; 87 testes e outages/recovery em worker/Actions; merge 19a78e2 |
| 13 | Parcial, preservada em branch isolada | Runner em elaboração; sem certificação dos 250; ampliação GCP solicitada antes de prosseguir |
| 14 | Não iniciada | Aguarda gate 13 |
| 15 | Não iniciada | Auditoria básica existente; observabilidade completa aguarda gate 14 |
| 16 | Não iniciada | Mapeamento inicial existente; portabilidade completa aguarda gate 15 |
| 17 | Não iniciada | Aguarda gate 16 |
| 18 | Não iniciada | Sem freeze/release; aguarda certificação completa |

Originais preservados: XLSX byte a byte; HTML original privado e cópia pública sanitizada. Histórico de recepção em docs/source/INTAKE_REVIEW.md. Etapas anteriores de acesso remoto são históricas e não geram dependência atual.

## Validação e limites — registro histórico da etapa 1

Manifesto e hashes das três fontes locais aprovados; fonte ausente permanece sem conteúdo/hash. Alteração de autorização registrada em IMPLEMENTATION_ORDER.md. Nenhum serviço global alterado, nenhuma suíte pesada local, nenhuma vertical slice iniciada. Governance, Compose runtime e testes de produto serão validados nas etapas respectivas.

## Pendências documentais

- Cópia local de Voz e Tom, não bloqueante para estrutura.
- Aplicar 11–18 somente após os respectivos gates anteriores.
- CT-150 determina encerrar abordagem para “agora não”; a contraparte atribuída a Voz e Tom continua não verificada.

## Evidência da etapa 2

- Main protegida pela API: PR obrigatório, checks strict (lint, unit-contract, architecture, build, secret-scan, analyze), enforce_admins, conversas resolvidas, sem force push/deletion. Zero aprovações obrigatórias pois há um mantenedor; não há revisão independente simulada.
- Secret scanning e push protection ativos; Dependabot alerts habilitados, updates automáticos desabilitados, automerge false. CODEOWNERS e workflows pinados por SHA.
- Local: lint aprovado; 3 testes curtos aprovados; check de arquitetura reporta honestamente 0 arquivos runtime; build round-trip do pacote fonte aprovado; scans de árvore, histórico e XML expandido sem achados. Build de containers será acrescentado na etapa 3.
- Durante os testes, a planilha de cenários no workspace foi alterada externamente para 19.517 bytes e ZIP inválido. Cópia preservada privadamente; restaurado o exemplar certificado do Git (24.017 bytes, hash do manifesto), sem mudança de conteúdo versionado. Testes repetidos passaram.
- Preflight workers: um indisponível, dois compatíveis disponíveis. Runner global é específico de outro repositório e não foi executado/modificado. Fluxo isolado do ITA será preparado na etapa 3 com fallback entre workers.

- Segundo arquivo local divergente preservado fora do Git; trabalho continuado em worktree isolado com hashes certificados. A versão incorreta nunca foi incorporada aos commits.

## Etapa 3 — certificada

Compose: web, api, agent, policy, tool-broker, finance, data, postgres, observability e job secrets-init. Imagens base pinadas por digest, redes segmentadas, secrets gerados fora do Git e usuário de aplicação PostgreSQL sem superuser. Agent não tem rede/segredo/arquivo de banco, Finance ou Data.

Local no AGT: `docker compose config --quiet` aprovado; lint e 6 unit tests curtos aprovados; análise de 9 arquivos runtime sem violação. Build/up/smoke/shutdown aprovados em worker e no GitHub, sem execução pesada local. Bypass por DNS e IP direto negado; todos os healthchecks e saída limpa verificados. Recursos efêmeros removidos.

## Etapa 4 — contratos

CustomerContext, FinancialSnapshot, Eligibility, PolicyDecision, ToolRequest, ToolResult, AgentResponse e AuditEvent definidos em Pydantic estrito, com JSON Schema 1.0 versionado. Centavos inteiros, extras proibidos, dados ausentes explícitos e invariantes de deny/resultados/correlation/customer. Regeneração sem drift entra no CI. Não há lógica financeira, Policy Engine ou Agent implementados nesta etapa.

## Etapa 5 — transformação reproduzível

Fontes originais inalteradas. Regras R001–R014 preservam predicados e localização; tabelas completas preservam células e linhas. Dataset contém CT-001–CT-250, cinco famílias de 50, sem perdas. Regeneração exata verificada em CI; expectativas textuais não equivalem a evals executados (runner funcional na etapa 13). Cinco categorias de Voz e Tom permanecem vazias e provisórias, sem conteúdo inventado.

## Etapa 6 — decisões explícitas

ADRs 0001–0003 registram oito ambiguidades/conflitos, limites locais de opções, arbitragem deny-overrides e semântica temporal financeira. “Agora não” encerra abordagem sem agendar; contraparte de Voz e Tom permanece não confirmada. Permissões não podem ser reabertas por tom de voz ou dados ausentes.

## Etapa 7 — Policy Engine

Entradas estruturadas e PolicyDecision com validade/vínculo de requisição. Allow-list, bloqueios de produto/ferramenta, humano, nível financeiro, elegibilidade e linguagem. Fatos/contexto confiáveis são responsabilidade do serviço, nunca grants do LLM. Interface interna preparada; wiring HTTP com Broker nas etapas seguintes.

Validação da etapa 7: 43 testes curtos e lint/arquitetura/scans aprovados; smoke distribuído inclui chamadas HTTP reais de Policy com e sem consentimento.

## Etapa 8 — Finance Engine

Projeção em centavos, categorias de compromissos, histórico, simulação de gasto e custos com taxa verificada. MissingData não gera número. Fixtures sintéticas DEMO, sem contratos reais presumidos. Smoke de worker chama Finance por HTTP a partir da rede do Broker.

## Etapa 9 — Tool Broker

66 testes curtos aprovados. Grants/decision_id do chamador não autorizam; Policy carrega contexto DEMO do servidor. Leitura dependente de dados exige autorização própria. Contrato Projection reforçado na origem para rejeitar números internamente incoerentes. HTTP tem destinos fixos, sem redirects/proxy; logs de auditoria sem payload financeiro. Data usa adaptador de fixture explícito nesta etapa, sem fallback; persistência PostgreSQL pertence à vertical slice (11). Smoke distribuído inclui Broker → Policy → Data/Finance e caso negado.

## Histórico — checkpoint anterior à escolha do provider

Etapas 1–9 estruturalmente certificadas, com exceção documental autorizada para Voz e Tom. Último componente certificado: 6313b9b861e7038b8790b0678c6884e9b3419693, integrado pelo PR #8 em 78845aae96d51f8342c1569fad8f0c85946c6520. Evidência em docs/architecture/STAGE_09_VALIDATION.json.

Etapa 10 aguarda escolha do usuário sobre provedor/credencial. Inspeção de presença (sem exibir valores) não encontrou OPENAI_API_KEY no ambiente e arquivos locais usuais. A skill de credenciais exige decisão antes de implementar código de API; não se presume autorização para criar/reutilizar chave. Nenhuma chave foi criada, nenhum endpoint de modelo foi chamado e nenhum Agent funcional foi declarado concluído. Após resposta, continuar a etapa 10; não reiniciar 1–9.

Governança: main protegida, PRs e sete checks obrigatórios, sem automerge/autofix. Scans de árvore/histórico/XLSX expandido sem achados. Um worker indisponível foi contornado por outro compatível; nenhum build, PostgreSQL completo ou smoke pesado executado no AGT.

Limitações atuais: Data é fixture DEMO explícita, ainda sem persistência da jornada; interface de cliente não tem autenticação bancária real; não existe vertical slice, runner funcional de 250 evals ou release. Integridade de 250 cenários não significa 250 PASS de comportamento. Voz e Tom continua SOURCE_PENDING_LOCAL_COPY, não bloqueante documental.

## Etapa 10 — autorização posterior de provider

O usuário escolheu Vertex AI/Gemini, ADC e abstração substituível; autorizou mock para certificação e ativação real externa sem bloquear arquitetura. Isso supera o ponto de parada documental anterior. ADC indisponível no AGT (DefaultCredentialsError), sem chave criada nem chamada real ao modelo. Provider REST/ADC implementado com contratos estritos; mock não é fallback silencioso. Agent respeita deny, chama apenas Policy/Broker e compõe valores exclusivamente do Finance. Composição de linguagem inicialmente limitada a vocabulário seguro, sem atribuir conteúdo à fonte Voz e Tom ausente.

Configuração tocada: compose.yaml, compose.vertex.yaml, .env.example, infra/docker/Dockerfile, .dockerignore e requirements-agent.txt. Nenhuma configuração global do host alterada.

Etapa 10: 76 testes curtos aprovados; Compose base e override Vertex validados sem subir containers no AGT. Certificação real de Gemini permanece não executada; mock e transporte Vertex simulado são identificados separadamente.

## Etapa 11 — vertical slice

Web apresenta pergunta/gasto, API valida e converte representação monetária sem float, Agent coordena Policy/Broker, Finance calcula e Data consulta PostgreSQL. Fixture é seed explícito, não fallback. Integração altera saldo no banco e verifica mudança da resposta pela Web. Configuração alterada: Dockerfile, requirements-data.txt, .dockerignore, workflow CodeQL (inclui JavaScript) e verify.sh. Original HTML permanece arquivado e intacto.

## Etapa 12 — testes adversariais

Threat model atualizado com controles/evidências e limites do mock. Testes cobrem falha de autorização/validação/ferramenta, ausência/incerteza, injeção, exfiltração, invenção financeira, produtos, humano e bypass. Worker derruba Policy/Broker/Finance/Data/PostgreSQL um a um, exige fail closed e verifica recuperação da jornada. Nenhuma falha é convertida em PASS por fallback.

Correção de teste na etapa 12: o transporte simulado agora converte MissingData no mesmo erro estruturado MISSING_DATA do HTTP real. A falha não foi ignorada; regressão repetida após a correção.

## Histórico — ampliação GCP antes da recepção do inventário

Provider oficial `VertexGeminiProvider`, port `ModelProvider` preservado; mock explícito permanece em CI. Projeto/região/modelo são externos. VERTEX_OK e leitura BigQuery foram confirmados manualmente pelo usuário no Google, não reproduzidos pelo AGT.

Inventário BigQuery: **BLOCKED_ENVIRONMENT_ACCESS**. Não há ADC disponível nesta sessão nem canal de execução autenticado no Google. Coletor de metadados implementado e testado, captura real tentada e falhou sem produzir inventário. Não foram obtidos schemas/tipos/nulabilidade/todas as tabelas. A tabela extrato_sintetico e seis nomes de campos são informação do usuário, não inventário completo. Adapter definitivo fica condicionado à inspeção integral; nenhum schema ou cálculo foi presumido. Fonte da competição é sintética externa, distinta das fixtures locais.

Gate anterior de 10–12 com mock permanece válido; esta ampliação está parcial. Etapas 14–18 não foram iniciadas. Rascunho da etapa 13 preservado em setup/13-evals; não foi misturado neste checkpoint. Detalhes e comandos: docs/architecture/BIGQUERY_INVENTORY.md.

Validação desta ampliação: 93 testes curtos, lint, arquitetura (26 arquivos, zero violações) e Compose base/Vertex aprovados; CI/worker serão vinculados ao SHA do PR. Configuração alterada: .env.example (variáveis não secretas do coletor) e .gitignore (venv isolada do inventário); nenhum host, IAM, serviço global, deploy ou infraestrutura paga alterado. Voz e Tom continua SOURCE_PENDING_LOCAL_COPY não bloqueante.

Instrução posterior confirmada: o operador entregará inventário de metadados gerado no Cloud Shell como arquivo local. Nenhum token/chave/credencial será fornecido ao AGT. Não tentar habilitar acesso GCP no AGT. Inventário bruto somente local/privado; publicar exclusivamente documentação/contratos sanitizados após revisão. Mock/fixtures continuam independentes de GCP.

Correção durante CI desta ampliação: CodeQL sinalizou duas comparações parciais de URL no verificador estático de arquitetura. Substituídas por parsing explícito de hostname; nenhum alerta foi suprimido ou contornado. Regressão e certificação repetidas no SHA corrigido.

## Etapa 10 / BigQuery — inventário local recebido e mapeado

Checkpoint anterior integrado pelo PR #13, merge 5df2349; SHA 3f9507c certificado com 93 testes/CI/worker. Inventário agora recebido localmente, gerado em 2026-09-26T23:33:13Z: uma tabela listada, extrato_sintetico, 11 campos NULLABLE. Identidades e localização conferidas entre listagem e metadados. Bloqueio de inventário resolvido; nenhuma credencial ou acesso GCP no AGT necessário. Bruto preservado fora do Git/imagem; contém metadata de IAM que não foi publicado.

Implementados contratos LedgerReadRequest/CompetitionLedger e adapter REST de leitura em Data Access. vlr e saldo_apos FLOAT são normalizados individualmente via Decimal/HALF_UP para centavos inteiros antes de qualquer Finance; nulos preservados, inválidos rejeitados, origem aproximada e arredondamento explícitos. Campos de parcela FLOAT são contagens inteiras exatas, sem arredondamento. Documentação sanitizada e ADR 0004 registram mapeamento e limites.

Adapter preparado com consulta parametrizada, ADC externo, validação de schema/identidade/região, janela/linhas/custo limitados e falha fechada. Não houve chamada real ao BigQuery, alteração de Policy/Broker/Finance/Agent, nova rota ou egress. Jornada PostgreSQL/DEMO preservada. Ativação de fonte externa depende de vínculo de identidade confiável/Policy e semântica/dados necessários; metadata não comprova próxima renda, obrigações futuras nem saldo atual. Moeda/unidade exigem configuração explícita.

Configurações tocadas: .env.example, requirements-agent.txt, requirements-data.txt, novo requirements-gcp.txt, .dockerignore e Dockerfile. Nenhuma configuração global/infraestrutura externa alterada. Testes e CI deste checkpoint serão vinculados ao SHA do PR; validação pesada exclusivamente distribuída. Etapa 13 preservada em branch isolada; 14–18 não antecipadas.

Validação local deste mapeamento: 107 testes curtos aprovados, 10 schemas sem drift, lint/arquitetura (29 arquivos, zero violações), Compose base/Vertex aprovados. Hashes dos originais privados conferidos sem alteração; SOURCE_FIELDS coincide com os 11 campos/tipos/modos recebidos. Certificação de imagem Data inclui import ADC/adapter e normalização sem contato GCP.

## Integração da vertical slice BigQuery — em execução

Instrução posterior autoriza conectar o adapter pela jornada real, sem deploy. Contratos estendidos de forma aditiva no protocolo 1.0: janela explícita, data.ledger, prova de identidade opaca e FinancialContext com INCOMPLETE_FINANCIAL_CONTEXT. Observações, contagens determinísticas, listas vazias de estimativas/inferências e dados ausentes são separados e validados. Não há conversão implícita para FinancialSnapshot. A jornada DEMO permanece compatível. Checkpoint de contratos precede o wiring runtime; certificação ponta a ponta ainda pendente.

## Wiring competition — certificada

API vincula sessão privada a cliente e assina prova curta para Policy; Broker reautoriza cada capacidade; Data autentica Broker e reconsulta Policy. CompetitionLedger normalizado atravessa Broker → Finance → FinancialContext → AgentResponse/Web. UI só apresenta janela UTC e evidências, sem cliente selecionável/calculadora financeira. FinancialContext distingue observações, contagens, estimativas/inferências vazias e lacunas. Projeção futura/recorrência/produtos/limites continuam bloqueados.

Configuração alterada: compose.yaml (redes Data–Policy e chaves por par), novo compose.bigquery.yaml (modo/registry/egress exclusivo Data), .env.example e requirements-dev.txt. Nenhuma infraestrutura externa/live/credencial GCP foi criada; bruto privado permanece fora do Git/imagens. CI agora inclui ambas as jornadas e falhas/recuperação/shutdown. Certificação real do GCP é próximo passo externo, não dependência local.

Validação local do wiring: 120 testes curtos e 11 schemas aprovados; lint e arquitetura (34 arquivos) sem violações; Compose base e overrides BigQuery+Vertex combinados aprovados. Secret scan e certificação distribuída/GitHub exigidos antes do merge.

Certificação do código em 997d8fb20b096332f6b998df704c2d1cd42b37f6, PR #15: 120 testes; lint, unit/contract, arquitetura, secret scan, CodeQL (zero alertas abertos no PR), Compose/build e ambas as jornadas em containers aprovados no GitHub e em worker distribuído. Falhas/recuperação, bloqueio de acesso direto e shutdown limpo aprovados; fallback entre workers funcionou, sem suíte pesada no AGT. Evidência distribuída associada ao SHA com status PASS. Este registro documental também passa pelos checks obrigatórios antes do merge. Sem chamada/deploy GCP; certificação do transporte real/ADC permanece pendência externa explícita.

## Cloud Run readiness — passada autorizada, etapa 16 permanece aberta

Runtime final Cloud Run confirmado pelo operador. Trabalho nesta branch é preflight/pacote de implantação, sem deploy, API habilitada, IAM, Artifact Registry ou gcloud executado no AGT. Cloud SQL/VPC Access fora do caminho crítico; Agent Engine opcional. PostgreSQL continua apenas no modo DEMO local. Etapas 13–18 não são declaradas concluídas por esta preparação.

Primeiro checkpoint: PORT dinâmico, URLs HTTPS Cloud Run configuráveis, ID token por audience com verificação de assinatura/caller no receptor além do IAM da plataforma. Cloud não usa as chaves HMAC de serviço locais; prova de contexto do cliente usa assinatura remota IAM signJwt da API, verificada pela Policy. Chave privada nunca sai do Google. Registry permanece configuração externa revogável, a montar via Secret Manager. SDK de autenticação presente em todos os containers HTTP; domínio preservado. Testes targeted do adapter cloud aprovados; scripts, arquitetura e certificação completa seguem pendentes neste checkpoint.

Segundo checkpoint: pacote Cloud Shell e ADR 0006 preparados, sete SAs/arestas explícitas, bootstrap fechado/configure separado, publicação Web isolada e destroy apenas de preview próprio. Build valida SHA/checks e registra tags SHA/digests/labels OCI, sem latest. Preflight somente leitura, sem generateContent ou linhas de extrato; aponta bloqueios sem habilitar APIs. Configuração tocada: Dockerfile (auth SDK/labels), .env.example, infra/gcp/cloudrun/env.example e services.json; nenhum host/Compose global alterado.

Lint, 141 testes curtos, 11 schemas, integridade das fontes/250 cenários e arquitetura (35 arquivos, zero violações) preparados para certificação pública e distribuída deste SHA. Worker deverá provar PORT=9091/startup/SIGTERM/read-only/sem volumes dos oito containers HTTP e repetir ambas as jornadas anteriores. Nenhum comando gcloud real nos testes (subprocesses simulados). Compatibilidade local não equivale a IAM/deploy Google certificado. Próximo gate obrigatório continua sendo o operador executar preflight e devolver saída sanitizada; etapa 16 NÃO concluída.

Revisão de publicação detectou cinco falsos positivos: identidades sintéticas explícitas e URL adversarial no teste cloud. Exceção restrita aos valores revisados nesse único arquivo, com teste garantindo bloqueio em outros arquivos/endereço não aprovado. Nenhuma credencial real envolvida; scan deve passar antes de push.

CodeQL encontrou comparação incompleta de URL no novo guard estático de Vertex. Corrigido na origem com parsing explícito de hostname em todos os ramos; alerta não suprimido. Novo SHA deve repetir checks e certificação antes do merge.

O alerta CodeQL persistiu no teste de sufixo mesmo após parsing. O guard agora compara os labels DNS completos e o identificador regional do serviço, sem busca parcial de URL. Verificação funcional do guard preservada; aguarda nova análise sem supressão.

Pacote da passada no PR #16: preparação Cloud Run implementada; resultado final de Actions/CodeQL/worker vinculado ao SHA no PR antes da integração. Readiness local não muda os estados externos AINDA NÃO TESTADO/BLOQUEADO. Após integração, o único próximo gate operacional é preflight somente-leitura no Cloud Shell; nenhum deploy ou encerramento da etapa 16 autorizado nesta passada.
