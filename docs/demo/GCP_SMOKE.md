# Gate de smoke real no Google — ainda não executado

1. Preflight real já confirmado pelo operador. Próximo gate: criar apenas o registry ita-escossio pelo comando em infra/gcp/cloudrun/README.md e devolver saída sanitizada. Nenhum deploy/IAM/push é autorizado por esse gate.
2. Após revisão/ autorização posterior, seguir infra/gcp/cloudrun/README.md: identidades mínimas, secret privado, imagens SHA/digest, bootstrap/configure e eventual publicação somente de Web.
3. Prover sessão de usuário vinculada a cliente sintético autorizado; guardar token em arquivo privado 0600, nunca no Git/chat/argumento de comando. O schema do registry é o mesmo da jornada local. Não é autenticação bancária.
4. Definir ITA_SMOKE_SESSION_FILE, ITA_SMOKE_FROM e ITA_SMOKE_TO (UTC ISO8601, janela máxima do vínculo/366 dias), configuração de projeto/região/prefix e rodar `bash infra/gcp/cloudrun/smoke.sh`.
5. Esperado: Web → API → Agent Vertex → Policy → Broker → Data BigQuery/normalização → Finance → AgentResponse. Resultado needs_data/INCOMPLETE_FINANCIAL_CONTEXT, proveniência COMPETITION_SYNTHETIC_BIGQUERY, sem projeção/estimativa/inferência. Consentimento retirado é denied. Sem ID token, todos os endpoints internos negam acesso.
6. Registrar Git SHA, digests do manifesto, revisões Cloud Run, correlation ID/status e latências sanitizadas. Não capturar linhas do extrato, token, ADC, Authorization, conteúdo do secret ou metadata IAM bruto em artefatos públicos.

O smoke faz chamadas reais de modelo/consulta e pode ter custo; só será executado pelo operador após autorização. A listagem de modelos no preflight não certifica Gemini generateContent. Zero registros de extrato é contexto ausente na janela, não prova de cliente inexistente; projeção salarial permanece bloqueada mesmo com registros.

Falha de IAM/ADC, schema, região, fonte, assinatura, timeout ou cold start não pode produzir fallback de fixture. Reportar BLOCKED/falha com operação/recurso/erro sanitizado e ação necessária. Não afrouxar policies para demonstrar sucesso. Investigar 401/403 considerando separadamente identidade do serviço e sessão do cliente; tokens completos jamais entram em logs.

Pendências reais: criação do nosso registry, IAM efetivo, publicação de imagens, revisões/secret mounts, audiência ID token/signJwt, conectividade sem VPC, Vertex real no fluxo, BigQuery real no fluxo e latência sob cold start. Tudo isso é AINDA NÃO TESTADO pelo projeto; HTTP 200 manual anterior foi confirmado pelo operador.
