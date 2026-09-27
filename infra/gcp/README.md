# Target Cloud Run — preparação, sem implantação

Runtime final confirmado: Cloud Run. Pacote do operador em [cloudrun/README.md](cloudrun/README.md).
O próximo gate é preflight somente-leitura no Cloud Shell; nenhuma operação GCP no AGT.

Competição: sete serviços HTTP, BigQuery, Vertex, ADC por serviço, IAM invoker e configuração privada via Secret Manager. PostgreSQL é exclusivo de desenvolvimento/teste DEMO; não há dependência Cloud SQL/AlloyDB/VPC Access. Agent Engine permanece opcional, fora do caminho crítico.

[Readiness e limites](../../docs/architecture/CLOUD_RUN_TARGET.md), [IAM](../../docs/security/GCP_IAM_BOUNDARIES.md), [smoke posterior](../../docs/demo/GCP_SMOKE.md). Etapa 16 permanece aberta; este pacote não declara portabilidade certificada no Google nem cria infraestrutura.
