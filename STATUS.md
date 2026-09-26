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
| 10 | Bloqueada antes da implementação | Aguarda escolha de provedor/credencial do modelo; consulta enviada ao usuário, nenhum segredo criado ou API chamada |
| 11 | Não iniciada | Aguarda gate 10; vertical slice autorizada somente após 1–10 |
| 12 | Não iniciada | Aguarda gate 11 |
| 13 | Não iniciada | Dataset íntegro; runner de eval funcional ainda não implementado |
| 14 | Não iniciada | Aguarda gate 13 |
| 15 | Não iniciada | Auditoria básica existente; observabilidade completa aguarda gate 14 |
| 16 | Não iniciada | Mapeamento inicial existente; portabilidade completa aguarda gate 15 |
| 17 | Não iniciada | Aguarda gate 16 |
| 18 | Não iniciada | Sem freeze/release; aguarda certificação completa |

Originais preservados: XLSX byte a byte; HTML original privado e cópia pública sanitizada. Histórico de recepção em docs/source/INTAKE_REVIEW.md. Etapas anteriores de acesso remoto são históricas e não geram dependência atual.

## Validação e limites

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

## Checkpoint certificado e ponto de retomada

Etapas 1–9 estruturalmente certificadas, com exceção documental autorizada para Voz e Tom. Último componente certificado: 6313b9b861e7038b8790b0678c6884e9b3419693, integrado pelo PR #8 em 78845aae96d51f8342c1569fad8f0c85946c6520. Evidência em docs/architecture/STAGE_09_VALIDATION.json.

Etapa 10 aguarda escolha do usuário sobre provedor/credencial. Inspeção de presença (sem exibir valores) não encontrou OPENAI_API_KEY no ambiente e arquivos locais usuais. A skill de credenciais exige decisão antes de implementar código de API; não se presume autorização para criar/reutilizar chave. Nenhuma chave foi criada, nenhum endpoint de modelo foi chamado e nenhum Agent funcional foi declarado concluído. Após resposta, continuar a etapa 10; não reiniciar 1–9.

Governança: main protegida, PRs e sete checks obrigatórios, sem automerge/autofix. Scans de árvore/histórico/XLSX expandido sem achados. Um worker indisponível foi contornado por outro compatível; nenhum build, PostgreSQL completo ou smoke pesado executado no AGT.

Limitações atuais: Data é fixture DEMO explícita, ainda sem persistência da jornada; interface de cliente não tem autenticação bancária real; não existe vertical slice, runner funcional de 250 evals ou release. Integridade de 250 cenários não significa 250 PASS de comportamento. Voz e Tom continua SOURCE_PENDING_LOCAL_COPY, não bloqueante documental.
