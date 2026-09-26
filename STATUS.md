# Estado da implantação

Data: 2026-09-26. Repositório: <https://github.com/escossio/ita-agent-batalha>.
Branch local: `main`. Para o SHA exato deste checkpoint, executar `git rev-parse HEAD`.

**Etapa 1 parcial: três fontes incorporadas após revisão; falta “Ita: Voz e Tom”.**
O repositório público foi criado vazio e conferido pela API. Workspace isolado e identidade Git local noreply preparados.
Estrutura inicial, inventário e sequência oficial 1 → 10 registrados. Nenhum arquivo preexistente de outro projeto foi alterado.

| Etapa | Estado | Evidência / impedimento |
| --- | --- | --- |
| 1 — Repositório e fontes | Parcial / bloqueada | 3/4 incorporadas: duas planilhas íntegras e HTML sanitizado; falta Voz e Tom |
| 2 — Governança | Bloqueada, não iniciada | Gate da etapa 1 não aprovado |
| 3 — Containers | Bloqueada, não iniciada | Depende da etapa 2 |
| 4 — Contratos | Bloqueada, não iniciada | Depende da etapa 3 |
| 5 — Transformações | Bloqueada, não iniciada | Depende da etapa 4 e das fontes |
| 6 — Conflitos e hierarquia | Bloqueada, não iniciada | Depende da etapa 5 |
| 7 — Policy Engine | Bloqueada, não iniciada | Depende da etapa 6 |
| 8 — Finance Engine | Bloqueada, não iniciada | Depende da etapa 7 |
| 9 — Tool Broker | Bloqueada, não iniciada | Depende da etapa 8 |
| 10 — Agent | Bloqueada, não iniciada | Depende da etapa 9 |

## Reenvio atual — fontes íntegras

- Recebidas duas planilhas válidas e o HTML no diretório indicado pelo usuário. ZIP/CRC/XML das planilhas aprovados; cópias originais idênticas por SHA-256. A planilha inválida anterior permanece arquivada privadamente.
- Gitleaks nos arquivos e XML expandido: zero achados. HTML contém identificadores de uma captura de tela; publicado somente exemplar sanitizado, reproduzível e marcado DEMO, com original preservado fora do Git.
- Manifesto atualizado: 3/4 fontes incorporadas; `voice_and_tone` está `inaccessible`. Link Claude informado pelo usuário retornou HTTP 403; conteúdo não capturado. Origem, data, tamanhos e hashes dos demais arquivos registrados. Nenhuma conversão para runtime/evals, implementação de etapa posterior ou execução do HTML.
- Risco no código-fonte do protótipo registrado: entrada livre em `innerHTML`. Fonte arquivada não deve ser servida como aplicação pública.

## Primeiro recebimento após o bootstrap (histórico)

- Usuário indicou `docs/source/`; encontrada somente a planilha de regras, com 12.624 bytes e hash estável.
- Validação ZIP falhou: 11 das 19 entradas ilegíveis; offsets negativos e cabeçalhos inválidos. Registro em `docs/source/INTAKE_REVIEW.md`.
- Arquivo original preservado, backup privado com hash conferido e exclusão local em `.git/info/exclude`; fonte inválida não será publicada.
- Manifesto atualizado para `received_invalid`; três fontes permanecem `missing`. Não houve transformação, reparo ou avanço de etapa.

## Validações do bootstrap anterior (histórico)

- Conta GitHub confirmada: `escossio`; nome preferencial inexistente antes da criação; repositório criado PUBLIC.
- Git local 2.47.3, GitHub CLI 2.46.0 e Docker Compose 2.26.1 disponíveis; coordenador `andy-ci-distributed` localizado, não executado.
- Inventário JSON válido, quatro IDs de fonte distintos, todos com estado `missing` e hashes/origens nulos.
- `git diff --cached --check`: aprovado para a estrutura inicial.
- Gitleaks 8.30.1 na árvore: zero achados. Auditoria complementar de arquivos rastreados: zero achados de IP privado, e-mail pessoal, CPF/CNPJ formatado, URL inesperada ou arquivo proibido.
- Revisão manual do conteúdo novo: somente documentação, inventário, marcadores e exclusões Git; nenhum original/dado bancário recebido. Auditoria de segurança detalhada em `docs/security/PUBLICATION_REVIEW.md`.
- Checkpoint inicial `8c1100d`: `git fsck --full` aprovado, histórico completo examinado pelo Gitleaks sem achados e autoria noreply conferida. A revisão será repetida sobre o checkpoint documental final antes do push.
- Checkpoint documental `3cf7d84`: Gitleaks aprovou árvore e os dois commits; auditoria complementar de todo o histórico examinou 13 blobs, sem achados; manifesto confirmou quatro IDs únicos e 0/4 fontes recebidas.
- Push HTTPS recusado por falta do escopo OAuth `workflow`, inclusive para `.github/workflows/.gitkeep`. Chave SSH já existente autenticada como `escossio`; transporte de push configurado somente neste repositório para SSH. Nenhum escopo/token/global alterado.

## O que não foi validado nem implementado

- Nenhum required check/workflow, proteção de main, CodeQL, CODEOWNERS ou Dependabot configurado por esta execução: pertencem à etapa 2.
- Testes de produto: não executados; código de produto ainda não existe.
- Containers do ITA: nenhum criado. Compose é marcador com `services: {}`.
- `docker compose config`: não executado; validar a stack pertence à etapa 3. Não considerar o marcador aprovado como runtime.
- Subida/smoke: não executados. Nenhuma suíte pesada local ou distribuída iniciada.
- `ARCHITECTURE.md`, `CONTAINERS.md`, `THREAT_MODEL.md` e `SECURITY_BOUNDARIES.md` ainda pendentes nas etapas correspondentes.
- Nenhuma integração LLM, deploy GCP, API real Itaú ou vertical slice iniciada.

## Pendência para retomar

Obter conteúdo acessível de `Ita: Voz e Tom`. O usuário informou `https://claude.ai/artifact/YEMJ288EEVpnw1GgY4WE2e`; tentativa de leitura pela ferramenta web falhou e requisição HTTP retornou 403. Solicitado texto ou link de exportação acessível. Não foi capturado conteúdo nem atribuído hash ao documento.

O link posterior de projeto Drive foi identificado como “Ita - Grupo 01”, MIME `application/vnd.google-apps.project`. Metadados acessíveis, mas busca por filhos retornou vazia; fetch de `/drive/project` não é suportado pelo conector e tentativa de download pelo ID retornou 403. Solicitado o link direto de Voz e Tom dentro do projeto; acesso aos metadados não comprova acesso aos documentos.

Retomar a etapa 1: revisar dados/metadados, preservar originais, sanitizar cópias se necessário, registrar proveniência/hash,
incorporar as quatro fontes, atualizar README/STATUS, validar e fazer checkpoint. Só então iniciar a etapa 2.

## Divergências e riscos

CT-150, aba `Cenarios_Treino`, linha 151, confirma encerramento da abordagem para “agora não”. Falta Voz e Tom para verificar a outra parte do conflito informado; nenhuma decisão de policy foi tomada.
O problema de integridade da primeira planilha foi resolvido pelo reenvio. Os identificadores do HTML foram removidos apenas da cópia pública; original preservado privadamente. Entrada livre em `innerHTML` permanece como risco documentado da fonte, que não está implantada.
A proteção de main ainda não foi aplicada, pois a etapa 2 está bloqueada. Este checkpoint é bootstrap documental, não fundação concluída.
