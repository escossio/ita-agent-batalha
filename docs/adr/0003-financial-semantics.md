# ADR-0003 — semântica financeira da fundação

Data: 2026-09-26. Aceito como definição técnica local, não como API real do Itaú.

A projeção “até o próximo salário” mede o saldo imediatamente **antes** da próxima entrada. O saldo inicial é o valor disponível na data as_of. Compromissos pendentes até a véspera da renda são subtraídos, inclusive vencidos não liquidados presentes no snapshot; valores no dia da renda ficam fora desse horizonte. O gasto proposto é aplicado agora. A data de renda precisa ser conhecida e posterior a as_of; não extrapolar prazo arbitrário quando ausente.

Uma entrada pontual confirmada pode delimitar uma simulação explicitamente identificada; não serve como comprovação de renda recorrente. Valores estimados permanecem separados dos confirmados e tornam o resultado incerto. Snapshot incompleto não autoriza afirmar saldo projetado completo. Histórico ausente não impede projeção de compromissos completos, mas impede comparação histórica.

Centavos inteiros, sem ponto flutuante para dinheiro. Sem criação implícita de recorrências ou multiplicação de parcelas já materializadas no calendário. Comparações históricas exigem períodos completos. Juros/custos só com taxa, prazo e regime explícitos confiáveis; ausência nunca vira taxa zero. Não há contratação/movimentação financeira.

Essas escolhas resolvem ambiguidades temporais que as fontes não especificam integralmente. Alterá-las exige testes de regressão e nova decisão versionada.
