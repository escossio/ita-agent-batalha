# Fluxo oficial de implementação: 1 → 10

Fonte normativa: briefing de implantação do usuário, registrado em 2026-09-26.
Este documento registra obrigações e critérios futuros, não declara implementação concluída.

## Regra de avanço

Executar exatamente na ordem abaixo. Não pular etapas, antecipar implementação nem misturar responsabilidades.
Cada etapa precisa de evidência versionada, validação, atualização de `STATUS.md` e checkpoint Git.
Só iniciar a etapa seguinte após validar integralmente a anterior. Checkpoint parcial não libera avanço.
Bloqueios devem identificar causa e último estado válido, sem esconder falhas ou fabricar checks verdes.

## 1. Criar repositório e congelar as fontes

Criar repositório público `ita-agent-batalha` na conta do ambiente; inspecionar antes se o nome existir.
Preparar Git local e workspace isolado, estrutura inicial, README, `.gitignore`, `.env.example` e marcador de Compose.
Incorporar as duas planilhas, o protótipo HTML e Voz e Tom em `docs/source/`, com origem e função no README.
Preservar originais; se houver dados sensíveis, guardar o original fora do Git e publicar somente cópia sanitizada identificada.
Google Docs deve ter representação versionável, preferencialmente Markdown, com origem/data.
Registrar integridade com SHA-256. Derivados futuros ficam em `config/` ou `evals/`.

**Gate:** quatro fontes disponíveis, revisadas e congeladas; proveniência e hashes registrados; revisão de segurança de árvore/histórico antes do push; checkpoint Git.

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

A vertical slice “Até o próximo salário dá?” fica fora desta passada, mesmo se 1–10 terminarem;
exige instrução posterior explícita.
