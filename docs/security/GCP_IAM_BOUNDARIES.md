# IAM mínimo planejado — ainda não aplicado

Sete service accounts distintas, nenhuma Owner/Editor, chave JSON, API key ou token estático. O operador de deploy é separado do runtime. Data não recebe Vertex, Agent não recebe BigQuery; ter google-auth instalado não concede privilégios.

| Caller / service account | Callee | IAM necessário no destino |
| --- | --- | --- |
| web / ita-web-sa | api | roles/run.invoker somente no serviço api |
| api / ita-api-sa | agent | roles/run.invoker somente no agent |
| agent / ita-agent-sa | policy, tool-broker | roles/run.invoker em cada um |
| tool-broker / ita-broker-sa | policy, data, finance | roles/run.invoker em cada um |
| data / ita-data-sa | policy | roles/run.invoker somente no policy |
| policy / ita-policy-sa | nenhum serviço | nenhum invoker |
| finance / ita-finance-sa | nenhum serviço | nenhum invoker |

Permissões adicionais preparadas:

- Agent: custom role `itaVertexPredict` com apenas `aiplatform.endpoints.predict` no projeto; não Vertex Admin/User amplo. Necessidades adicionais, se comprovadas pela API/modelo, exigem revisão, não fallback de privilégios.
- Data: custom role `itaBigQueryJobs` com `bigquery.jobs.create` no projeto executor; `roles/bigquery.dataViewer` **somente na tabela configurada** (mais restrito que dataset). Acesso a novas tabelas não é implícito. Nenhuma escrita. Configuração de moeda/unidade/budget explícita; consulta parametrizada e timeout/fail closed preservados.
- API: custom role `itaCustomerProofSigner`, somente `iam.serviceAccounts.signJwt`, binding exclusivamente na própria SA API. Não conceder Service Account Token Creator amplo nem impersonation de outras SAs. Prova assinada não substitui grants de Policy ou IAM invoker.
- API, Policy, Data: `roles/secretmanager.secretAccessor` somente no secret do IdentityRegistry, montado pelo Cloud Run; sem listagem/acesso a outros secrets. Registry não é credencial GCP.
- Web, Broker, Finance: nenhuma permissão adicional de APIs GCP. Policy apenas o secret citado; certificados de assinatura são públicos.
- Todos: stdout coletado pelo runtime; não precisam de Logging Admin/Writer para esse caminho. Exporter futuro terá revisão própria.

Ingress inicial `all` não significa allUsers: endpoints internos exigem IAM e verificação adicional do token/caller. Web também nasce privado; grant allUsers somente por publish_web.sh explícito, se org policy permitir. Org policy/DRS pode impedir entrada pública: reportar BLOCKED, sem desabilitar IAM. Sem VPC Connector/Cloud SQL/Agent Engine.

Permissões do operador (não concedidas automaticamente): visualizar projeto/APIs/Run/AR/IAM, query dry-run na tabela, acesso à API Vertex regional; depois da aprovação, criar custom roles/SAs se permitido, setIamPolicy nos recursos revisados, usar cada SA via iam.serviceAccounts.actAs, publicar imagens no repositório selecionado, administrar somente serviços preview e referenciar o secret. O service agent do Cloud Run precisa conseguir obter as imagens do Artifact Registry; restrições cross-project/org podem exigir ação do time Google. Estes acessos precisam ser comprovados no GCP real.

O script adiciona grants mínimos, mas não audita/remove automaticamente permissões herdadas. O operador deve revisar IAM efetivo (projeto/pasta/organização), service agents, org policies, região/modelo e políticas de compartilhamento. A API IAM de administração de SAs pode também exigir habilitação/permissão não comprovada pelo inventário de IAM Credentials; não habilitar automaticamente.

Referências: [Cloud Run service-to-service](https://docs.cloud.google.com/run/docs/authenticating/service-to-service), [BigQuery jobs.query](https://docs.cloud.google.com/bigquery/docs/reference/rest/v2/jobs/query), [signJwt](https://docs.cloud.google.com/iam/docs/reference/credentials/rest/v1/projects.serviceAccounts/signJwt).
