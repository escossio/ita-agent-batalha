# Containers e coordenação

| Serviço | Papel nesta etapa | Redes de acesso |
| --- | --- | --- |
| web | UI DEMO e proxy para API | entrada e api |
| api | Validação de entrada/contexto DEMO | web e agent |
| agent | Orquestrador com provider mock/Vertex | api, policy, broker |
| policy | Policy Engine independente | agent e broker |
| tool-broker | Execução autorizada e auditada | agent, policy, finance, data |
| finance | Cálculos determinísticos | broker |
| data | PostgreSQL com seed DEMO explícito | broker e postgres |
| postgres | Banco DEMO, usuário de aplicação sem superuser | somente data |
| observability | Saúde; reserva para telemetria | rede isolada |
| secrets-init | Job de inicialização de secrets | sem rede |

Imagens base pinadas por digest OCI; imagens de serviço contêm apenas o próprio componente e runtime HTTP comum.
Serviços Python executam como UID/GID 10001, filesystem readonly, capabilities removidas, no-new-privileges e limites de recursos.
PostgreSQL usa volume próprio. Credenciais aleatórias geradas no primeiro startup em dois volumes de secrets;
Data monta apenas o secret da aplicação. O secret administrativo só chega ao bootstrap/PostgreSQL.
Nenhuma senha é impressa, hardcoded ou versionada. Não alterar secrets após inicializar o DB sem rotação coordenada.

Em um worker ou estação de desenvolvimento adequada, a partir de checkout limpo:

```sh
docker compose config --quiet
docker compose up -d --build --wait
curl http://localhost:8080/healthz
docker compose down
```

Não precisa criar `.env`. `ITA_PORT` opcional altera a porta loopback; `ITA_PORT=0` escolhe porta efêmera para CI.
`docker compose down` preserva dados e secrets. `down --volumes` só é usado nos projetos efêmeros de certificação.
Startup depende de saúde/conclusão do bootstrap; SIGTERM produz shutdown limpo com log JSON.
X-Correlation-ID aceita UUID, é devolvido e registrado; não há log do conteúdo de requisições.

## AGT coordena; workers executam

Não executar build/subida/PostgreSQL completo no AGT. Ali, apenas config, lint, análise estática e unit curtos.
O scheduler global existente pertence a outro repositório; este projeto usa equivalente isolado:

```sh
# ITA_CI_WORKERS: lista de aliases SSH fornecida externamente pelo operador.
bash scripts/ci-distributed.sh SHA_COMPLETO_JA_PUBLICADO
```

O script verifica workers sequencialmente, ignora indisponíveis, faz checkout do SHA exato em diretório efêmero,
cria projeto Compose exclusivo, testa saúde/correlation/isolamento por DNS e IP/shutdown e remove somente seus recursos.
Falha real de teste não é mascarada por retry; falha de transporte permite outro worker. Pool indisponível bloqueia sem fallback local.
Saída local em `.artifacts/` (ignorada no Git); evidência pública registra SHA/status, sem hosts/IPs privados.
GitHub Actions também executa a certificação em runner hospedado; o status `distributed-foundation` comprova o worker coordenado pelo AGT.

O HTML original arquivado não é servido. Vertical slice pela Web disponível desde a etapa 11; não existe autenticação bancária real. Agent, Policy, Broker e Finance possuem interfaces internas certificadas com mock explícito.
