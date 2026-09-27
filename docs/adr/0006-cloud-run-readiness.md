# ADR 0006 — Cloud Run, IAM por serviço e preparação sem deployment

Decisão solicitada pelo usuário após main 98444dc: Cloud Run é o target final. Esta passada prepara readiness/tooling sem completar a etapa 16 nem antecipar gates funcionais 13–18. Próximo gate: preflight somente-leitura executado pelo operador Cloud Shell. Nenhuma operação GCP no AGT.

Mapear os sete serviços HTTP de negócio existentes individualmente; observability atual é placeholder de saúde, PostgreSQL/secrets-init ficam no desenvolvimento local. Competição usa BigQuery, portanto não requer persistência relacional. Cloud SQL/VPC Access não foram confirmados como habilitados e não serão dependências. Agent Engine não é adotado.

No cloud: PORT configurável, URLs canônicas por env, ID tokens com audience do destino, IAM invoker por aresta e verificação adicional do caller. API é única emissora de prova de cliente, por IAM signJwt na própria SA; Policy verifica certificados Google e os vínculos estritos existentes. Nenhuma chave compartilhada substitui IAM. O modo Compose preserva sua autenticação HMAC para testes isolados.

Registry externo é configuração privada versionada em Secret Manager (API/Policy/Data), não banco de sessão persistente no container. Revogação no cloud requer rollout coordenado/drenagem das versões anteriores. Política financeira e cálculo não dependem de SDK Cloud Run. Dados incompletos continuam incompletos; falta de autenticação falha fechada.

Deployment preparado em duas fases: bootstrap com POSTs desativados e saúde disponível, depois URLs/grants/configuração. Preview novo e isolado; scripts recusam sobrescrever serviços existentes no bootstrap, desvio de permissões e deleção de recursos sem label de ownership. Ingress roteável com autenticação IAM, sem VPC; Web pública somente por operação separada após autorização/org policy.

Build usa checkout limpo no SHA certificado, tags SHA e digests registrados. Scripts só executam em Cloud Shell e mutations exigem --apply. Nenhum recurso é criado no preflight. Limitação: local/CI simula SDK e certifica containers; somente o operador pode comprovar IAM/ADC/serviços Google reais. Detalhes, matrizes e estados em CLOUD_RUN_TARGET.md e GCP_IAM_BOUNDARIES.md.
