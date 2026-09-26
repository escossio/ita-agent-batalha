# Até o próximo salário dá?

Requer etapas 1–10 certificadas. Provider mock explícito é autorizado para certificação; Vertex real depende de configuração/ADC externa.

Entrada pela Web: “Até o próximo salário dá?”, gasto 500,00 e consentimento. API valida ChatInput, converte valor decimal exato para 50000 centavos e constrói CustomerContext DEMO; nenhum saldo, elegibilidade ou permissão vem do navegador.

Fluxo: Web `/api/chat` → API `/v1/chat` → Agent `/v1/respond` → Policy `/v1/authorize` → Broker `/v1/execute` → Policy (reautorização) → Data `/v1/snapshot` → PostgreSQL → Finance `/v1/project` → ToolResult → AgentResponse → Web.

Fixture sintética: saldo 200000, compromissos confirmados 75000 e estimados 15000, próxima renda em 2026-09-19. Projeção antes da renda: 200000 − 75000 − 15000 − 50000 = 60000 centavos. A renda não é adicionada antes da data. Resposta identifica DEMO, R$ 600,00, incerteza e decisão do cliente. Valores são exemplos de teste, não situação atual de pessoa real.

Policy aplica consentimento, segurança, allow-list e default deny; nenhuma oferta de produto ocorre. Finance.project e sua leitura dependente data.snapshot exigem decisões separadas. Agent compõe linguagem sem poder inventar números ou executar cálculo. A UI usa textContent e não executa cálculo financeiro.

Data inicializa tabela DEMO e faz seed somente para IDs ausentes; não sobrescreve registros existentes. Consultas parametrizadas e transações de leitura. Banco indisponível gera falha; nunca busca fixture como alternativa em runtime.

Mesmo correlation ID atravessa entrada, contratos e auditoria. A UI exibe intenção, decisão de Policy, ferramenta/status/duração e projeção. Logs JSON permitem seguir a execução sem registrar texto privado. Erros HTTP/dependência/schema são estruturados e a UI informa ausência de resultado, sem números fixos.

Certificação em worker: infra/docker/vertical_slice.py acessa a Web, valida resposta e altera o saldo no PostgreSQL para comprovar que a nova resposta vem da persistência, restaurando depois. Verifica também consentimento negado. Build/up/shutdown e isolamento continuam na regressão existente.

Limites: apenas dados DEMO; nenhuma autenticação bancária real, API Itaú ou movimentação. O protótipo original não é servido. Idioma limitado à composição segura enquanto Voz e Tom aguarda cópia local. Modelo mock não certifica comportamento Gemini real.
