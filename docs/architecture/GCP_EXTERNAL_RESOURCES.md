# Inventário sanitizado e isolamento do projeto compartilhado

Evidência: preflight real informado pelo operador na continuidade da main `39365558ec03a9a22c1730972ff38548847ea1bb`. Não reproduzido no AGT; inventários brutos, IAM completo e credenciais não são publicados. Projeto `batalha-time-01-97zr`, região `us-central1`.

## EXTERNAL_READ_ONLY

| Tipo | Identificação observada | Tratamento |
| --- | --- | --- |
| Cloud Run | `agente`, `ita-backend` | Nunca deploy/update/delete/IAM |
| Artifact Registry | `agentes`, `batalha-agentes` | Nunca usar como fallback, publicar package/tag ou alterar IAM |
| Service account | `squad-agent-sa` no projeto acima | Nunca reutilizar, atribuir ou alterar IAM |
| Service account | Default Compute SA do projeto | Nunca usar; número do projeto não foi fornecido e não é inferido |
| Secret | `ita-backend-gcp-credentials` | Nunca ler payload, montar, alterar ou reutilizar |
| Projeto | `batalha-time-01-97zr` | Leitura de metadata; nenhuma mutação de IAM/APIs no projeto pelos scripts |
| BigQuery | `hackathon_dados.extrato_sintetico` | Leitura/dry-run; nenhuma escrita de dados ou IAM |
| Vertex AI | API regional | Uso futuro de inferência com ADC próprio; nenhuma alteração de configuração/IAM |

Listar metadata para detectar colisões não autoriza mutações. Recursos auxiliares existentes também não são adotados. A criação de recursos filhos próprios não é uma autorização para editar IAM do projeto compartilhado.

## Fatos e gates

**CONFIRMADO pelo operador:** Cloud Run, Vertex AI, BigQuery, Artifact Registry, IAM/IAM Credentials, Secret Manager, Logging, Monitoring, Cloud Build, Pub/Sub e Model Armor disponíveis; leitura de metadata Run/AR/SA; dry-run BigQuery autorizado. `extrato_sintetico` tem 467585 registros, região us-central1 e schema já mapeado. Vertex teve HTTP 200 manual. Isto não certifica as futuras identidades/imagens desta solução.

**CONFIRMADO ausente:** Cloud SQL Admin e VPC Access não habilitados, fora do caminho crítico. PostgreSQL continua somente local. Cloud Build/PubSub/Model Armor disponíveis não os torna dependências do domínio; Agent Engine continua opcional e não adotado.

**PREPARADO:** guard central, mapa de nomes, ownership, comando de criação isolada de registry, scripts posteriores sujeitos a novos gates, testes sem credenciais.

**AINDA NÃO TESTADO:** criação do nosso registry e SAs, bindings IAM, actAs, push da nossa imagem, deploy dos nossos serviços, invocação autenticada entre eles, Gemini pela nossa imagem, BigQuery pela nossa Data SA e exposição final da Web. Também falta provisionar/verificar nosso IdentityRegistry e signJwt.

**BLOQUEADO por escopo:** alteração de qualquer recurso externo, IAM de projeto/tabela e operações GCP no AGT. Concessões necessárias ao runtime exigem decisão humana posterior sobre escopo/permissões; os scripts não tentam contornar esse limite.

Próximo gate: operador executar **somente criação do Artifact Registry `ita-escossio`** com [o comando exato](../../infra/gcp/cloudrun/README.md). Nenhum IAM, push ou deploy é autorizado pelo sucesso desse comando. Etapa 16 permanece aberta.
