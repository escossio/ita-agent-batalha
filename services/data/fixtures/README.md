# Fixtures sintéticas DEMO

Arquivos criados para testes deste projeto, sem vínculo com pessoa/conta real e sem contrato presumido de API Itaú. Datas e IDs explícitos; centavos inteiros. Não são fallback para falha de Data/PostgreSQL. Persistência na vertical slice deverá carregar as fixtures explicitamente e falhar se o banco estiver indisponível.

`demo-snapshot.json`: saldo R$ 2.000,00; compromissos confirmados R$ 750,00 e estimados R$ 150,00 antes da próxima renda. Gasto simulado R$ 500,00 resulta em R$ 600,00, com incerteza explícita. Receita no dia 19 não entra no saldo antes dessa data.
