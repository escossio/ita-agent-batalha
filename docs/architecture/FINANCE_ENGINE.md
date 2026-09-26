# Finance Engine determinístico

`services/finance/engine.py` não acessa rede, banco, LLM ou Policy. Valida entradas e devolve contratos tipados. POST interno `/v1/project` exige correlation ID igual no header/corpo; ausência de dados essenciais retorna MISSING_DATA. Valores inválidos não executam cálculo.

Projeção: saldo inicial − compromissos confirmados − estimativas − gasto proposto. Horizonte e vencidos conforme ADR-0003; próxima renda delimita prazo, sem somar o depósito ao saldo antes dele. O menor saldo equivale ao saldo final neste escopo, que só contém saídas antes da próxima renda. Não simula múltiplas entradas intermediárias inexistentes no contrato.

Breakdown separa contas, parcelas, assinaturas, recorrências e variáveis, materializadas em datas: não duplica parcelas/recorrências. Histórico compara períodos completos; committed inclui parcelas, variable é separado. Income recorrente não é inferido de entrada pontual. Histórico ausente não impede projeção quando calendário está completo.

Custos exigem taxa periódica verificada, prazo, regime simples/composto e tarifas explícitas. Decimal com arredondamento HALF_UP no centavo final; valores fora dos limites contratuais são rejeitados. Essa simulação não é CET, proposta ou condição real de produto. Não há valor presumido para taxas ausentes.

Fixtures em services/data/fixtures são sintéticas, DEMO. Não representam APIs Itaú nem fallback de infraestrutura. A execução ponta a ponta e persistência chegam na etapa 11, após Broker e Agent. Testes cobrem limites, incerteza, insuficiência, ausência de renda/histórico, fronteira temporal, categorias, comparações e custos.
