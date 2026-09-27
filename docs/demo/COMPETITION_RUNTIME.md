# Executar a jornada com fonte da competição

Fluxo real: Web → API (sessão/cliente) → Agent → Policy → Tool Broker → Policy → Data (autentica Broker, reautoriza Policy, consulta BigQuery e normaliza) → Broker → Finance (avalia suficiência/contagens) → Broker → AgentResponse → Web. Finance não consulta BigQuery; Broker coordena Data e Finance como capacidades separadas.

O resultado esperado com o schema atual é `needs_data` / `INCOMPLETE_FINANCIAL_CONTEXT`, nunca uma projeção salarial inventada. Exemplo estrutural: observed contém extrato, calculated contém transaction_count/balance_observation_count, estimates/inferences vazios, missing inclui saldo atual confirmado, próxima renda e compromissos futuros. `financial_result` permanece null. A UI apresenta a resposta e as evidências; nenhum cálculo/autorização acontece no frontend.

## Configuração externa

`compose.bigquery.yaml` ativa competition na API/Policy e bigquery no Data. Não cria recursos GCP. Exige:

- GOOGLE_CLOUD_PROJECT, ITA_BIGQUERY_DATASET, ITA_BIGQUERY_TABLE, ITA_BIGQUERY_LOCATION;
- ITA_BIGQUERY_CURRENCY=BRL e ITA_BIGQUERY_MONEY_UNIT=major, confirmadas pelo operador;
- ITA_BIGQUERY_MAX_BYTES_BILLED, limite de custo escolhido externamente;
- ITA_IDENTITY_REGISTRY_FILE, caminho absoluto **fora do repositório**, com os vínculos autorizados;
- ADC/identidade no runtime Data, sem chave ou JSON de service account na imagem.

Formato do registry privado (estrutura, sem cliente ou credencial reais): objeto com `bindings`, lista de registros contendo `context` (CustomerContext COMPETITION, provenance VERIFIED_RUNTIME_IDENTITY), `source_user_id`, `session_hash` (SHA-256 da sessão opaca), `expires_at` UTC e `max_window_days` entre 1 e 366. Cliente e hash devem ser únicos. Consentimento/contexto são configurados pelo servidor; nenhum campo do navegador pode sobrescrevê-los para conceder autoridade. Revogação ocorre por remoção/expiração do vínculo ou retirada de consentimento. A sessão bruta deve ser entregue ao cliente por canal seguro externo e não gravada no Git/logs/imagem. O projeto não fabrica uma identidade bancária nem contém um IdP.

Em runtime autorizado, após prover esse arquivo e a identidade:

```sh
docker compose -f compose.yaml -f compose.bigquery.yaml config --quiet
docker compose -f compose.yaml -f compose.bigquery.yaml up -d --build --wait
```

Não executar build/subida no AGT. Os comandos destinam-se a worker/estação adequada ou runtime Google autorizado. Nenhuma implantação é executada por esta documentação. Para promover imagens já certificadas, usar os mesmos digests e `--no-build`; não inserir configuração de domínio no build. Vertex real continua selecionável por compose.vertex.yaml e suas variáveis externas, independentemente do modo de dados.

A sessão chega por Authorization Bearer ou cookie `ita_session` provisionado externamente. O cookie é o mecanismo para a UI do navegador; deve ter HttpOnly/Secure/SameSite sob TLS. API não aceita customer_id ou source_user_id no JSON público. A UI solicita início/fim UTC; limite superior é exclusivo. DEMO mantém sua seleção existente e fixtures PostgreSQL. Janela ausente em competition pede dados sem executar ferramentas.

## CI sem Google

O worker gera sessões, hashes e arquivos temporários fora do checkout, usa ITA_DATA_PROVIDER=bigquery_mock com ITA_BIGQUERY_MOCK_ROWS_FILE no Data e sobe as mesmas imagens da regressão DEMO. O mock filtra por cliente/janela e passa pelo mesmo BigQueryLedgerReader e normalizador. A proveniência de saída é COMPETITION_SYNTHETIC_BIGQUERY_MOCK. Não é evidência de consulta real ao GCP.

Executar a certificação distribuída pelo SHA como descrito em CONTAINERS.md. `infra/docker/verify.sh` inclui ambas as jornadas; `competition_slice.py` verifica HTTP ponta a ponta, autorização, nulos, inteiros, ausência de inferência, falhas/recuperação e shutdown. Testes curtos usam `scripts/check.sh unit-contract`; schema drift e ausência de campos críticos falham explicitamente.

## Próximo passo no Google

Prover identidades distintas: Agent somente Vertex; Data com leitura das fontes e jobs no projeto executor; nenhum acesso BigQuery para Agent/ModelProvider. Montar registry e chaves de serviço via secret store, configurar orçamento/região e conectividade privada entre os nomes de serviço atuais. O runtime escolhido deve suportar essa resolução/segmentação; mapeamento completo de endpoints/IAM para Cloud Run pertence à etapa 16. HMAC interno não substitui TLS, IAM e configuração de ingress entre serviços.

Depois executar smoke **real** com uma sessão vinculada a um cliente autorizado, registrar somente SHA/correlation/status/proveniência sanitizados e comprovar que BigQuery retorna contexto incompleto com o schema atual. Nenhuma credencial precisa ir ao AGT. Para habilitar projeção, é necessário contrato/fonte adicional de saldo atual, próxima renda e compromissos futuros; repetir Policy/Finance/Broker e regressão. Não extrair essas certezas de padrão histórico automaticamente.
