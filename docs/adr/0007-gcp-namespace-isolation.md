# ADR 0007 — Namespace exclusivo em projeto GCP compartilhado

Status: aceito para tooling/preparação; nenhum recurso criado. Complementa ADR 0006 e substitui a seleção livre de registry/ita-preview e IAM automático nele previstos. Etapa 16 permanece aberta.

## Contexto

Preflight real informado pelo operador confirmou recursos de outras implementações. Todos são EXTERNAL_READ_ONLY. Disponibilidade de uma API e leitura de metadata não autorizam criar recursos, actAs ou modificar IAM. Nomes observados e fatos sanitizados estão em GCP_EXTERNAL_RESOURCES.md.

## Decisão

Prefixo fixo autorizado `ita-escossio`; nomes de serviços/packages/SAs em services.json, secret próprio de identidade, labels próprias. IDs completos de SA cabem no limite Google; não abreviar. Operações não allow-listed negam por padrão na fronteira de subprocesso compartilhada por todos os wrappers. Validar cada target, service account, package/digest e mount; nenhuma conta Compute/squad, JSON de credencial ou secret alheio. ADC nativo preservado.

Consultar existência/ownership antes de mutar. Colisão bloqueia sem relabel/adoption. Primeiro gate mutável exclusivamente `artifact_repository.sh --apply`: projeto ativo/região conferidos, listagem, operação exibida, criação apenas do repository ita-escossio com tags imutáveis. Registry próprio ausente/negado nunca seleciona registry compartilhado. Criação concorrente resulta em erro, sem retry/update. Execute operadores serialmente; labels/descriptions não são prova criptográfica de propriedade nem substituto de IAM.

**Não existe exceção mutável implícita para IAM de projeto/tabela.** A versão anterior adicionava roles no projeto e grant BigQuery na tabela compartilhada: esses comandos foram removidos. identities.sh só cria nossas SAs; permissões adicionais são desenho pendente, não aplicadas. O time Google/operador precisa decidir posteriormente como conceder acesso mínimo preservando a regra de não interferência; um novo escopo explícito será necessário para qualquer futura automação desses bindings. Não resolver permissão ausente com credenciais/SA existentes, Owner/Editor ou bypass.

## Consequências e validação

Não alteramos contratos, fronteiras runtime, Finance ou cálculos monetários. Primeiro deploy permanece bloqueado por gates de IAM, secret próprio, imagens e smoke real; isso não impede preparar/testar scripts offline. Unit tests mockam subprocesses e exercitam guard real, rejeições de nomes externos, região/projeto/ownership, único create, erro IAM/org policy sem fallback, tags/digests e arestas IAM. Regressão completa pública/distribuída associada ao SHA antes de merge. Sem GCP no AGT, sem conclusão da etapa 16.
