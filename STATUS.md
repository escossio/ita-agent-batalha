# Estado da implantação

Data: 2026-09-26. Repositório público: https://github.com/escossio/ita-agent-batalha.

## Instrução vigente

Somente artefatos locais; GitHub/repositório é a fonte versionada principal. Google Drive não é dependência, runtime ou bloqueio; não reconstruir integração.
Voz e Tom: **SOURCE_PENDING_LOCAL_COPY**, dependência documental não bloqueante para estrutura e preparação. Não inventar conteúdo; regras específicas só serão definitivas com fonte local versionada.

## Etapas

| Etapa | Estado | Evidência |
| --- | --- | --- |
| 1 | Gate estrutural aprovado com pendência documental | Três fontes congeladas; hashes/ZIP/XML/sanitização conferidos; manifesto atualizado conforme instrução do usuário |
| 2 | Em andamento | Proteção aplicada pela API; PR e seis checks obrigatórios; validação pública pendente |
| 3–10 | Não iniciadas | Aguardar gates anteriores; Voz e Tom não bloqueia partes independentes |
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
