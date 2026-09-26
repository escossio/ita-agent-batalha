# Tool Broker 1.0

POST interno `/v1/execute` recebe apenas ToolRequest validado. Allow-list: data.snapshot e finance.project. Não aceita contexto, grants, SQL, shell, URLs ou caminho de arquivo. PolicyDecision informado pelo chamador não é usado como autoridade: `/v1/authorize` no Policy recebe ToolRequest e carrega contexto DEMO do servidor.

Broker verifica schema, cliente, correlation ID, digest, validade, outcome, ação e ferramenta autorizada. Finance.project autoriza também a leitura dependente data.snapshot com nova requisição. Deny, ausência de grants ou falha de Policy impedem ferramentas; falha de output ou dependência remove todos os dados da resposta.

Finance e Data estão em redes acessíveis apenas ao Broker. Agent não possui acesso por DNS/IP, segredo ou código de banco. Transporte usa destinos fixos, recusa redirects e proxies herdados, limita tamanho de resposta, aplica timeout de socket de dois segundos e orçamento assíncrono de cinco segundos por chamada Broker. Cancelamento de thread de I/O não interrompe o socket imediatamente: seu timeout limita o encerramento. Somente operações de leitura/cálculo, sem efeitos financeiros.

Auditoria tipada: tool solicitada, Policy solicitada/decidida, autorização, bloqueio e conclusão; inclui correlation, ferramenta, duração, status e razão. Sem payload completo, saldo ou texto de usuário. Falha de auditoria antes da execução impede a chamada. ToolResult registra resultado validado ao chamador.

Fixtures/contextos são sintéticos DEMO e explícitos. Desde a etapa 11, Data consulta exclusivamente PostgreSQL; fixtures são seed explícito de inicialização, nunca fallback após falha. A integração modifica o banco e verifica a mudança da resposta pela Web. Não existe autenticação de cliente bancário real; não publicar essa interface como serviço multiusuário antes de identidade apropriada.

A interface interna `/v1/evaluate` é diagnóstico de regras com entradas confiáveis, não canal de execução. Mesmo que alguém consiga obter um allow ali, o Broker chama `/v1/authorize` independentemente e não aceita essa decisão. Consentimento mutável e identidade da jornada devem ser integrados explicitamente na etapa 11.
