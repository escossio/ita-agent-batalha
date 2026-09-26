# Policy Engine 1.0

Componente independente em `services/policy`, sem LLM, prompt ou cálculo financeiro. `PolicyInput` valida contexto, ação, requisição, fatos e elegibilidade; `PolicyLimits` é configuração exclusiva do serviço. Retorna `PolicyDecision` com vínculo SHA-256 da requisição e validade de 30 segundos. Entradas inválidas não geram permissões.

Apenas data.snapshot e finance.project podem ser autorizadas, individualmente por requisição. Produtos exigem elegibilidade recente, necessidade aderente e fatos/custos verificados. Perfil/horizonte/liquidez restringem investimento. R001–R014 são lidas do artefato JSON; fatos desconhecidos não satisfazem predicados. R009–R012 não concedem automaticamente produto. Estado crítico permite análise solicitada, mas bloqueia novas ofertas; sofrimento emocional encaminha para humano sem executar tools.

No fluxo de produção, **contexto, elegibilidade e fatos devem vir de configuração/Data confiáveis**, não da saída do modelo. A entrada Python é uma fronteira interna de confiança, não autenticação. O Broker da etapa 9 deverá obter esses dados e consultar Policy independentemente; um decision_id informado pelo Agent é somente rastreabilidade. POST /v1/evaluate existe apenas na rede interna; corpo e header devem compartilhar correlation ID. Não há porta pública de grants.

Restrições fixas: não julgar, não pressionar, não inventar números; são derivadas do briefing/ADRs, não da fonte de Voz e Tom ausente. Limites e precedência em ADR-0002. Recusa encerra abordagem; sem permissão proativa, não inicia contato. Cliente decide; não há ferramenta de movimentação.
