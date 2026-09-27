# Modelo de ameaças e certificação adversarial

Ativos: consentimento, contexto financeiro, decisões, fontes, secrets, números e audit trail. Fronteiras: browser/API, API/Agent, Agent/Policy/Broker, Broker/Finance/Data, Data/PostgreSQL. Tudo usa dados sintéticos DEMO; identidade bancária real não está implementada.

| Ameaça/caso | Controle e evidência |
| --- | --- |
| Prompt injection / modelo escolhendo tool indevida | ModelPlan fechado, ToolRequest allow-list, Policy independente e reautorização Broker; test_agent, test_broker, test_adversarial |
| Modelo revela configuração ou inventa taxa/limite/elegibilidade | Contexto enviado ao provider não contém secrets; NarrativePlan não aceita texto/valores livres; saída extra é rejeitada |
| Policy ignorada/decisão forjada/expirada/cliente trocado | Broker não aceita grants do chamador; verifica digest/identidade/validade e consulta contexto do servidor |
| Banco/Finance/Data acessado diretamente pelo Agent | Redes/imagens segmentadas; smoke testa DNS e IP real dos containers; architecture check bloqueia imports |
| Policy, Broker, Finance, Data ou PostgreSQL indisponível | infra/docker/adversarial.py para cada componente real, exige ausência de resultado e recuperação posterior; sem fallback |
| Falta próxima renda / entrada incompleta / valor inválido | Contratos estritos e MissingData; não executa ou devolve needs_data; test_finance/test_api/test_adversarial |
| Histórico ausente | Não inventa comparação; projeção só usa calendário completo conhecido |
| Saldo insuficiente / compromissos superiores / gasto excessivo | Finance preserva resultado negativo; não transforma em oferta automática |
| Dados incertos | Estimativas separadas, flag e linguagem explícitas; Projection valida coerência |
| Produto inelegível/bloqueado, estado financeiro crítico | Policy deny; testes de prova completa de necessidade/elegibilidade/custos e limites |
| Sofrimento emocional / pedido de humano | Handoff explícito, nenhuma ferramenta executada |
| Tool output/LLM inválido, timeout | Schemas na saída, vínculo da requisição, timeout e resultado sem número inventado; unit tests de providers/ports hostis |
| Vazamento em Git/histórico/planilhas | Gitleaks árvore/histórico/XML expandido e revisão de publicação |
| DOM injection no protótipo original | Fonte arquivada; UI nova usa textContent, CSP e nenhum HTML do modelo |
| Mudança sem certificação | PR, checks obrigatórios, main protegida, sem automerge/autofix |

Princípios verificados: autorização falhou → não executa; validação falhou → não executa; ferramenta falhou → informa falha; faltou dado → não inventa; dado incerto → sinaliza incerteza.

Limites honestos: ataques de linguagem são certificados com mock e providers hostis simulados; não certificam resistência de Gemini real sem ativação/avaliação externa. O contrato fechado e a autorização independente continuam determinísticos independentemente do modelo. Comprometimento do host/Docker, DoS sustentado e autenticação bancária real estão fora da demo local; não expor como produção multiusuário.

Voz e Tom permanece SOURCE_PENDING_LOCAL_COPY e não é autoridade ausente de segurança. Não há movimentação financeira ou tool de contratação. Logs não registram payloads, tokens ou dados bancários reais.

## Ampliação BigQuery

- Troca de cliente, janela, gasto ou sessão: prova API–Policy assinada, curta, vinculada à requisição; registry lido novamente permite revogação.
- Broker falsificado/chamada Data direta: HMAC por par de serviços, nonce/TTL/cache limitado e reautorização independente. Prova sem consentimento/grant é negada. Replay cache é local ao processo; não garante exactly-once entre réplicas.
- Histórico apresentado como salário futuro/saldo atual: contrato FinancialContext exige lacunas, proíbe estimativas/inferências nesta capacidade e não permite Projection sem dados.
- SQL injection: consulta fixa, identificadores somente de config validada, cliente/janela por parâmetros.
- Fonte truncada, schema drift, região/tabela errada, ADC/timeout: erro estruturado sem fixture fallback nem contexto parcial. Dados grandes falham antes do transporte interno.
- Descrição com prompt injection: permanece observação não confiável; não é enviada ao ModelProvider. UI usa textContent.
- Vazamento de inventário/sessões: bruto fica privado; CI usa registros sintéticos e sessões/chaves efêmeras, sem conteúdo nos logs.

Evidências: test_competition_runtime, test_bigquery_data, test_financial_context e competition_slice.py. GCP live, IdP externo e resiliência de Gemini real continuam exigindo certificação externa; não são simulados como aprovados.
