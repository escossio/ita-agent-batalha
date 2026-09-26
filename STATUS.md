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
| 5 | Em validação | 14 regras e 250 cenários derivados; 21 testes curtos aprovados; aguarda CI/worker |
| 6–10 | Não iniciadas | Aguardar gates anteriores |
| 11–18 | Planejadas, não iniciadas | Definições recebidas e registradas no plano oficial |

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
