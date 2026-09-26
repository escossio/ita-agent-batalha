# Fluxo oficial de implementação: 1 → 18

Fonte normativa: briefing de implantação do usuário, registrado em 2026-09-26.
Este documento registra obrigações e critérios futuros, não declara implementação concluída.

## Regra de avanço

Executar exatamente na ordem abaixo. Não pular etapas, antecipar implementação nem misturar responsabilidades.
Cada etapa precisa de evidência versionada, validação, atualização de `STATUS.md` e checkpoint Git.
Só iniciar a etapa seguinte após validar integralmente a anterior. Checkpoint parcial não libera avanço.
Bloqueios devem identificar causa e último estado válido, sem esconder falhas ou fabricar checks verdes.

## Atualização autorizada pelo usuário — fontes locais

A instrução posterior do usuário prevalece sobre o gate documental original: Voz e Tom recebe `SOURCE_PENDING_LOCAL_COPY`. Sua ausência é uma dependência documental **não bloqueante** para repositório, governança, containers, contratos, arquitetura e preparação dos componentes. Os demais gates continuam obrigatórios, em sequência, com evidências e checkpoints.

O gate da etapa 1 libera avanço estrutural com as três fontes locais revisadas/congeladas e a quarta explicitamente pendente; isso não certifica conteúdo ausente. As partes de etapas posteriores que dependam especificamente de Voz e Tom permanecem provisórias e rastreadas, sem conteúdo inventado. Google Drive não faz parte do caminho crítico, das dependências ou do runtime; não reconstruir acesso. GitHub e o repositório público são a fonte versionada principal.

As etapas 11–18 foram fornecidas posteriormente pelo usuário e incorporadas abaixo. As etapas 1–10 continuam válidas, sem reinício. A vertical slice está expressamente autorizada na etapa 11, somente após os gates 1–10.

## 1. Criar repositório e congelar as fontes

Criar repositório público `ita-agent-batalha` na conta do ambiente; inspecionar antes se o nome existir.
Preparar Git local e workspace isolado, estrutura inicial, README, `.gitignore`, `.env.example` e marcador de Compose.
Incorporar as duas planilhas, o protótipo HTML e Voz e Tom em `docs/source/`, com origem e função no README.
Preservar originais; se houver dados sensíveis, guardar o original fora do Git e publicar somente cópia sanitizada identificada.
Google Docs deve ter representação versionável, preferencialmente Markdown, com origem/data.
Registrar integridade com SHA-256. Derivados futuros ficam em `config/` ou `evals/`.

**Gate vigente:** fontes locais disponíveis revisadas e congeladas; proveniência e hashes registrados; Voz e Tom marcado `SOURCE_PENDING_LOCAL_COPY` quando ausente; revisão de segurança de árvore/histórico antes do push; checkpoint Git. Exceção documental não bloqueante autorizada acima.

## 2. Governança do GitHub

Aplicar padrão dos projetos maduros: proteção de `main`, PRs, required checks, CODEOWNERS, CodeQL,
secret scanning, Dependabot quando aplicável, lint, testes, build, architecture checks e documentação de segurança.
Organizar workflows; proibir autofix, automerge e edição automática do produto por agentes.
CI certifica. Se branch protection falhar por permissão/API, registrar erro e comandos/configuração exatos pendentes.

**Gate:** configurações verificadas por leitura da API e checks reais; limitações explícitas; checkpoint Git. A exceção documental para branch protection não autoriza inventar proteção ativa.

## 3. Containerização e execução no AGT

Criar fronteiras físicas/lógicas e de rede: web, api, agent, policy, tool-broker, finance/data, postgres e observability.
Fluxo: Browser → web/api → agent → policy/tool-broker → finance/data → postgres.
Agent não acessa PostgreSQL, não executa ferramentas nem autoriza sua ação. Broker é a porta de ferramentas;
Policy decide; Finance calcula deterministicamente. PostgreSQL em rede interna; expor apenas o necessário.
Secrets externos/env/secret store; healthchecks, startup previsível, shutdown limpo, logs estruturados e correlation/request ID.
`docker compose up` deve iniciar a fundação de forma reproduzível. Scripts AGT dentro do workspace, sem mudanças globais.

**Gate:** Compose validado, subida/smoke e fronteiras verificadas no ambiente apropriado; documentar `ARCHITECTURE.md`, `CONTAINERS.md` e diagrama Mermaid versionado; checkpoint Git.

## 4. Contratos antes da lógica

Definir contratos tipados/versionados: CustomerContext, FinancialSnapshot, Eligibility, PolicyDecision,
ToolRequest, ToolResult, AgentResponse e AuditEvent. Campos obrigatórios/opcionais e versões explícitos;
proibir estruturas livres onde dados críticos precisam de validação. LLM deve respeitar os contratos.

**Gate:** testes de schema/contract, incluindo entradas inválidas, aprovados; checkpoint Git.

## 5. Documentos em artefatos executáveis

Excel não entra no runtime. Converter regras para YAML/JSON reproduzível com IDs/rastreabilidade de origem.
Converter cenários para `evals/scenarios.jsonl`, expectativas e runners; avaliação/regressão, não treinamento automático.
Verificar exatamente 250 cenários, IDs únicos, famílias identificadas, contagens esperadas por família e ausência de perdas.
Separar Voz e Tom em orientação de geração, comportamento, segurança, restrição de produto e handoff humano.
Regras determinísticas não podem existir somente em prompt. Toda transformação deve ser reexecutável a partir das fontes.

**Gate:** regeneração e integridade comparadas às fontes congeladas, testes aprovados; checkpoint Git.

## 6. Conflitos e hierarquia de policies

Inspecionar contradições/ambiguidades, registrar decisões em `docs/adr/` e não resolver silenciosamente.
Analisar o conflito informado no briefing: “agora não” encerra a abordagem em cenários, mas Voz e Tom pode prever retorno posterior.
Definir contextos de aplicação com rastreabilidade e testes. O conflito ainda precisa ser confirmado nas fontes.
Hierarquia inicial: segurança da pessoa → restrições obrigatórias/compliance → autorização/policy → regra financeira → elegibilidade → política conversacional → voz e tom.

**Gate:** conflitos relevantes decididos explicitamente em ADRs e hierarquia testável; checkpoint Git.

## 7. Policy Engine

Componente independente, default deny, entradas estruturadas e saída PolicyDecision.
Cobrir ações/produtos permitidos e proibidos, humano, crédito, máximo de opções, linguagem,
ferramentas autorizadas, nível financeiro e segurança. Policy não é prompt; LLM nunca sobrescreve deny.

**Gate:** testes unitários extensos e checks verdes; somente então checkpoint Git.

## 8. Finance Engine determinístico

Separar cálculos do LLM: saldo atual, compromissos, próxima renda, saldo projetado, impacto de gasto,
recorrências, parcelas, assinaturas, variáveis, histórico, simulações e juros/custos com dados confiáveis.
LLM nunca é autoridade para taxa, parcela, saldo, limite, elegibilidade, custo, disponibilidade ou resultados calculáveis.
Sem APIs reais, usar fixtures sintéticas identificadas como DEMO. Não inventar contratos de sistemas Itaú reais.

**Gate:** cálculos determinísticos e casos de borda validados, dados DEMO explícitos; checkpoint Git.

## 9. Tool Broker

Única porta para capacidades executáveis: allow-list, schemas, validação de entrada/saída,
timeout, erros, correlation ID, auditoria, policy enforcement, identificação da ferramenta, duração, resultado e status.
Fluxo Agent → Policy → Tool Broker → Finance Engine/Data Access/outras ferramentas autorizadas.
Agent não deve conseguir contornar o broker.

**Gate:** testes de bypass e de enforcement aprovados; checkpoint Git.

## 10. Agent / Orchestrator

Somente agora introduzir framework/modelo LLM, substituível por interface sem reescrever domínio, Policy ou Broker.
Agent compreende intenção, mantém contexto permitido, solicita ferramentas, consome PolicyDecision/resultados
estruturados, produz linguagem natural conforme Voz e Tom e devolve AgentResponse.
Não pode acessar banco/SQL, executar ferramentas diretamente, autorizar ações, ignorar deny,
inventar elegibilidade/taxa/saldo, calcular finanças criticamente como autoridade, escolher produto fora das regras ou movimentar dinheiro.

**Gate:** testes/checks verdes, fronteiras verificadas e documentação mínima completa; checkpoint Git.

## 11. Primeira vertical slice completa

Transformar “Até o próximo salário dá?”, hoje apenas fonte HTML com números fixos, em execução real:
Web → API → Agent → Policy e Tool Broker → Finance Engine e Data Access/fixtures → PostgreSQL → AgentResponse → Web.
Frontend apenas apresenta e envia intenção/dados permitidos; remover dele cálculos financeiros e decisões críticas.
Exigir request/correlation ID, intenção identificada, CustomerContext válido, autorização pelo Policy,
tools executadas pelo Broker, números do Finance Engine, dados DEMO explícitos, camada conversacional final pelo Agent,
AgentResponse validado, audit trail e erros estruturados. Sem fallback para valores fixos e sem LLM substituir cálculos.
Testes de integração e `docs/demo/VERTICAL_SLICE.md`: entrada, fluxo, serviços, regras, tools, cálculo, resposta e rastreabilidade.

**Gate:** jornada real ponta a ponta e testes/checks verdes; checkpoint Git.

## 12. Testar a vertical slice de forma adversarial

Cobrir happy path; saldo insuficiente; próxima renda ausente; histórico ausente; compromissos superiores ao saldo;
gasto maior que saldo; valores inválidos; entrada incompleta; Broker, Finance e PostgreSQL indisponíveis;
resposta de tool inválida; timeout; resposta LLM inválida; LLM pedindo tool proibida; bypass de Policy;
acesso direto ao banco; produto inelegível e produto bloqueado; estado financeiro/emocional delicado;
handoff humano; dados incertos; prompt injection; tentativa de revelar configuração;
tentativa de inventar taxa, limite e elegibilidade.

Testar fail closed: falhou autorização/validação → não executa; tool falhou → informa falha;
faltou dado → não inventa; dado incerto → sinaliza incerteza. Documentar ameaças/mitigações em THREAT_MODEL.md.

**Gate:** nenhuma fragilidade estrutural pendente na jornada e testes adversariais aprovados; checkpoint Git.

## 13. Integrar 250 cenários como eval/regressão

Dataset é avaliação, não fine-tuning automático. Runner executa contra o sistema, sem exigir texto literal.
Verificar intenção, contexto, policy, produtos permitidos/bloqueados, tool correta, ausência de tools proibidas,
cálculo, autonomia, ausência de invenção financeira, elegibilidade, segurança, humano, proatividade,
tom compatível, estimativas, ausência de julgamento, transparência de custo e decisão final do cliente.
Classificar cada cenário como PASS, FAIL, BLOCKED ou NOT_IMPLEMENTED; não mascarar os dois últimos como sucesso.
Relatório agregável por cenário, família, regra, componente e tipo de falha.
Estrutura: scenarios.jsonl, expectations/, runners/, reports/ e README em evals/.
Integrar ao CI; documentar camadas rápida/completa para custo/modelo e testes determinísticos sem LLM.

**Gate:** runner funcional, cobertura e relatório explícito dos 250 cenários, CI adequado; checkpoint Git.

## 14. Expandir para outras famílias

Somente após jornada principal e evals estáveis. Implementar capacidades reutilizáveis, não 250 fluxos.
Para cada família: intenção → dados → regras → tools → cálculos determinísticos → policies → Agent → testes → evals da família → regressão das anteriores.
Sem resposta por scenario_id nem exceções frontend para passar testes.
Separação: LLM compreende/compõe; Policy autoriza/restringe; Finance calcula; Broker executa; Data fornece; frontend apresenta.
Produzir matriz de capacidades por família.

**Gate por incremento:** família estável, testes/evals e regressões executados; checkpoint após cada família/incremento rastreável.

## 15. Observabilidade e rastreabilidade ponta a ponta

Tracing e métricas com OpenTelemetry ou abstração equivalente, sem fornecedor no domínio.
Mesmo correlation/trace ID em API, Agent, Policy, Broker, Finance e Data Access.
Eventos: request, intenção, policy solicitada/decidida, tool solicitada/autorizada/bloqueada,
duração de tool, erro, chamada/duração de Finance, chamada/duração de modelo, resposta validada, handoff e resultado final.
Logs estruturados; não registrar senhas, tokens, secrets, cartão completo, dados bancários reais sensíveis ou conteúdo privado sem finalidade operacional.
Métricas mínimas: requests, latência, erros, policy denies, tool/model failures, eval pass rate, handoffs e timeouts.
Compatibilidade AGT/local e futura GCP; documentar `docs/architecture/OBSERVABILITY.md`.

**Gate:** traces/eventos/métricas correlacionáveis e revisão de redaction validados; checkpoint Git.

## 16. Portabilidade GCP

Sem migração definitiva ou infraestrutura paga/externa sem necessidade explícita.
Mapear web/api/agent/policy/broker → Cloud Run/equivalente; PostgreSQL → Cloud SQL/AlloyDB;
secrets → Secret Manager; identidade → IAM/Service Accounts; telemetria → OpenTelemetry/Cloud Operations;
imagens → Artifact Registry; configuração → env/config gerenciada.
Documentar em infra/gcp/: serviços, dependências, portas, variáveis, secrets, service accounts, permissões mínimas,
fluxo de implantação e diferenças do AGT/local. IaC inicial se adequado; sem IDs/credenciais/valores privados fixos.
Configuração ambiental externa ao domínio e IAM com menor privilégio.

**Gate:** portabilidade comprovável sem reescrita do domínio, não exige deployment produtivo; checkpoint Git.

## 17. Documentação e roteiro de demonstração

Explicar problema, agente controlado versus chatbot, arquitetura e caminhos de bloqueio.
LLM pode compreender linguagem/intenção, organizar contexto, solicitar ferramentas e compor explicação.
Não pode autorizar, acessar banco diretamente, inventar elegibilidade/taxa/saldo/limite, movimentar dinheiro ou ignorar deny.
Explicar uso dos 250 cenários em regressão. Roteiro reproduzível da jornada principal deve evidenciar entrada,
interpretação, policy, ferramenta, cálculo, resposta e audit trail. Preparar segundo caso de deny se possível.
Criar `docs/demo/DEMO_SCRIPT.md`, `ARCHITECTURE_EXPLANATION.md` e `EVALUATION.md`.
README como entrada pública, sem detalhes privados desnecessários do laboratório.

**Gate:** pessoa sem contexto consegue entender e reproduzir a demo documentada; checkpoint Git.

## 18. Freeze, certificação e release da apresentação

Working tree limpa; nenhum segredo, credencial, .env real, dado pessoal indevido ou artefato importante fora do Git; docs atualizadas.
Checkout limpo deve validar compose config/build/up, healthchecks, smoke e shutdown limpo.
Executar unit, contract, architecture, integration, security, policy, finance, broker, vertical slice e evals.
Todos os required checks verdes, sem bypass. Relatório final com total/PASS/FAIL/BLOCKED/NOT_IMPLEMENTED explícitos.
Executar secret scan, dependency scan, CodeQL, revisão de exposição pública e validação das fontes.
README deve explicar o que é, como funciona, subir, testar, rodar evals e demo.
Somente depois da certificação: tag/release com SHA, data, estado de evals, limitações e artefatos da apresentação.
Não alterar versão congelada sem novo SHA e recertificação dos checks afetados.

**Gate:** certificação completa com evidências e limitações honestas; release publicada e freeze registrado.

## Checkpoints, regressão e correções na origem

Commits pequenos/coerentes/rastreáveis: testar → documentar → diff → secrets → commit → push/PR conforme governança.
A cada expansão: testes locais curtos → contratos → nova capacidade → regressão existente → evals → CI.
Carga pesada permanece exclusivamente nos workers.
Falha estrutural exige voltar ao componente responsável: autorização em Policy; número em Finance;
tool indevida em Policy/Broker; contrato insuficiente em contracts; resposta em Agent/voice rules;
dado incorreto em Data/fixture. Corrigir e retestar antes de avançar, sem workaround no frontend.

## Operação e portabilidade obrigatórias

- Inspecionar estado/dependências antes de alterar; preservar outros projetos e serviços globais. Não usar tmux nem tocar live externo.
- AGT coordena. Cargas PostgreSQL completas, migrações pesadas, suítes full e validações longas vão para workers pelo SHA correto, com fallback entre workers compatíveis. Pool indisponível bloqueia; carga pesada local exige autorização explícita.
- Integrar o fluxo `andy-ci-distributed <sha> postgres` ou equivalente compatível com este projeto; não presumir que o runner existente aceita qualquer repositório.
- GitHub Actions permanece certificação pública.
- GCP apenas mapeamento futuro: containers → Cloud Run; PostgreSQL → Cloud SQL/AlloyDB; secrets → Secret Manager; identity → IAM/Service Accounts; telemetry → OpenTelemetry/Google Cloud Operations. Não migrar nem acoplar domínio.
- Documentação mínima ao concluir: README, fontes, ARCHITECTURE, IMPLEMENTATION_ORDER, CONTAINERS, ADRs, THREAT_MODEL, SECURITY_BOUNDARIES, demo, config, evals, infra e testes.
- Antes de **cada push**, revisar segredos/tokens/senhas, `.env`, dumps, dados pessoais/bancários reais, credenciais do laboratório, IPs/URLs privados e todo o histórico. Apagar depois do push não desfaz exposição.

## Relatório final obrigatório

Informar URL pública, branch/commit, árvore, documentos incorporados, estado individual 1–10,
checks, resultados de testes, containers, resultado de `docker compose config`, subida/smoke,
pendências, divergências e riscos encontrados antes da publicação. Distinguir “não executado” de “aprovado”.

A instrução posterior explícita autoriza a vertical slice exclusivamente na etapa 11, após validar 1–10.
