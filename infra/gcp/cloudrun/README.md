# Pacote Cloud Shell — namespace isolado, sem deployment

Preflight real foi confirmado pelo operador. [Fatos sanitizados e recursos EXTERNAL_READ_ONLY](../../../docs/architecture/GCP_EXTERNAL_RESOURCES.md). Esta preparação não conclui a etapa 16. Nenhum comando GCP deve rodar no AGT.

## Próximo gate: criar apenas nosso Artifact Registry

No checkout atualizado do repositório, **dentro do Cloud Shell**, executar exatamente:

```sh
ITA_GCP_PROJECT=batalha-time-01-97zr \
ITA_GCP_REGION=us-central1 \
ITA_RESOURCE_PREFIX=ita-escossio \
ITA_ARTIFACT_REPOSITORY=ita-escossio \
bash infra/gcp/cloudrun/artifact_repository.sh --apply
```

O comando exige ambiente Cloud Shell e gcloud, confere o projeto ativo sem alterá-lo, valida região/prefixo, lista repositórios e mostra `OPERATION CREATE` com `projects/batalha-time-01-97zr/locations/us-central1/repositories/ita-escossio`. A flag `--apply` é a confirmação explícita. A única mutação possível é criar esse Docker repository, com labels de ownership e tags imutáveis. Não configura Docker, não cria IAM, não publica imagem, não faz deploy e não habilita APIs. Se já existir com nosso ownership/formato/tags imutáveis, retorna NO MUTATION; se houver colisão, bloqueia sem adotar/alterar.

PERMISSION_DENIED, organization policy ou qualquer erro encerra com código 2 e `BLOCKED`, operação, recurso, erro recebido e próxima ação humana. **Não há retry mutável nem fallback** para `agentes`/`batalha-agentes`. Guardar saída privadamente e devolver resultado sanitizado; somente depois decidir o próximo gate. Um erro de rede pode ocorrer após criação remota: nova execução primeiro consulta existência e nunca altera o recurso encontrado.

Caso ainda não tenha o checkout no Cloud Shell, `git clone https://github.com/escossio/ita-agent-batalha.git` e `cd ita-agent-batalha` são apenas preparação local. Confira o SHA da main entregue no PR antes de executar o comando acima.

## Guard e nomes

Todos os wrappers usam `set -euo pipefail` e delegam a `operator.py`. Seu único ponto de subprocesso aplica `namespace.py` **antes** de executar. Operações GCP não revisadas negam por padrão; testes substituem subprocesses, nunca executam gcloud no AGT/CI. Prefixo padrão e único autorizado: `ITA_RESOURCE_PREFIX=ita-escossio`. Override não amplia autorização. Não usar o antigo ITA_CLOUD_RUN_PREFIX/ita-preview.

| Serviço físico | Cloud Run e package | Service account ID |
| --- | --- | --- |
| web | ita-escossio-web | ita-escossio-web-sa |
| api | ita-escossio-api | ita-escossio-api-sa |
| agent | ita-escossio-agent | ita-escossio-agent-sa |
| policy | ita-escossio-policy | ita-escossio-policy-sa |
| tool-broker | ita-escossio-broker | ita-escossio-broker-sa |
| data | ita-escossio-data | ita-escossio-data-sa |
| finance | ita-escossio-finance | ita-escossio-finance-sa |

Todos os SA IDs têm 6–30 caracteres; não é necessária abreviação. Tool Broker mantém seu nome lógico/código/variáveis e muda somente o sufixo do recurso GCP para broker. Futuro secret exclusivo: `ita-escossio-identity-registry`. Labels: `ita-escossio-owner=ita-escossio`, `ita-escossio-managed=ita-agent-batalha`, mais `ita-escossio-sha` nas revisões. SA usa description `ita-escossio-managed:ita-agent-batalha` pois a API de SA não oferece labels. Nome, projeto e marcador devem coincidir antes de reutilizar qualquer recurso. Marcadores detectam colisões; não substituem IAM nem autorização. Não executar operadores concorrentes sobre este namespace.

Repository é exatamente `ita-escossio`. Packages permanecem isolados; tags aceitas apenas SHA Git completo, deploy somente digest. Mesmo eventual uso de registry compartilhado exigirá decisão humana e revisão explícita do guard, nunca seleção por variável nesta versão. Recursos auxiliares/roles ainda não implementados não recebem exceções de namespace.

## Scripts posteriores — não executar neste gate

- `preflight.sh`: somente leitura; projeto/conta/região/APIs, metadata BigQuery e query dry-run sem linhas, Vertex regional, listagens AR/Run/SA e Docker. Sucesso não autoriza escrita. Lista de modelos não equivale a generateContent. Saída bruta pode conter metadata privada; sanitizar antes de publicar.
- `identities.sh --apply`: prepara apenas sete SAs próprias, recusando colisões antes de criar qualquer uma. **Não concede IAM**. Permissões de projeto/BQ compartilhados permanecem bloqueadas até decisão humana posterior; nenhum custom role, key JSON ou credencial existente é reutilizado. Ver [IAM](../../../docs/security/GCP_IAM_BOUNDARIES.md).
- IdentityRegistry: provisionamento privado posterior, com contrato existente em [COMPETITION_RUNTIME.md](../../../docs/demo/COMPETITION_RUNTIME.md), recurso próprio/labels e versão numérica. Contém vínculo de sessão/cliente sintético, nunca credencial Google. Payload fora do Git; não há script de criação de secret nesta passada.
- `build_push.sh --apply`: exige checkout limpo e ITA_CERTIFIED_SHA com 40 caracteres, checks GitHub e distributed-foundation verdes para o SHA exato. Contexto público Git pinado pelo SHA exclui arquivos locais ignorados. Sete imagens linux/amd64 com labels OCI, tags SHA, manifesto de digest/horário/Dockerfile. Repository deve já existir, ser próprio e ter tags imutáveis. Sem latest, criação implícita ou alteração de código. Tags imutáveis impedem sobrescrever um SHA com digest diferente; reutilizar digest certificado, não retag. Manifesto parcial não é implantável nem sobrescrito.
- `deploy.sh --apply --phase bootstrap`: somente nossos sete serviços novos, privados e com rotas de negócio desabilitadas. Confere colisões, ownership de SAs/secret e configuração antes de mutações. Sem padrão Default Compute/squad SA, GOOGLE_APPLICATION_CREDENTIALS, arquivo JSON ou secret externo. IAM/actAs, acesso a imagens e ao secret precisam de gate próprio. Bootstrap interrompido exige inspeção/cleanup explícito dos nossos recursos; não escolher prefixo alternativo silenciosamente.
- `deploy.sh --apply --phase configure`: confere ownership dos sete serviços, obtém URLs canônicas/audiences, valida grants existentes e adiciona invokers apenas nas arestas revisadas. Depois configura URLs e ativa rotas. Duas fases evitam ciclo de URLs; não é rollout atômico. Sem tráfego público até concluir review/smoke.
- `publish_web.sh --apply`: somente Web pode receber allUsers invoker, se explicitamente autorizado e permitido por org policy. Serviços internos permanecem IAM-authenticated; nunca desabilitar IAM para contornar DRS.
- `smoke.sh`: gate posterior de chamada real Web/Vertex/BQ, com custo possível, sessão privada 0600 e janela UTC. Não concede permissões; verifica contexto incompleto, consent deny e recusa anônima dos serviços internos. Nenhuma linha financeira/token é impressa.
- `destroy_preview.sh --apply --confirm-preview ita-escossio`: nome histórico do wrapper preservado; agora só remove os sete serviços próprios do namespace fixo após verificar ownership de todos. Nunca remove SA/secret/registry/imagens ou recurso externo. Não executar neste gate.

`env.example` é configuração externa não secreta. Projeto/região/fonte são fornecidos por env, mas limitados pelo escopo autorizado do operador; domínio continua portátil. `ingress=all` permite transporte sem VPC com IAM obrigatório, não acesso anônimo. Nenhuma dependência Cloud SQL/VPC Access/Agent Engine. PostgreSQL é apenas DEMO local. Não há deploy automático neste pacote.

Referências: [IDs de service account](https://docs.cloud.google.com/iam/docs/service-accounts-create), [Artifact Registry create/immutable-tags](https://docs.cloud.google.com/sdk/gcloud/reference/artifacts/repositories/create), [contexto Git pinado](https://docs.docker.com/build/concepts/context/#url-fragments).
