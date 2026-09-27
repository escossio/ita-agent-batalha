# Fronteiras obrigatórias

Browser é entrada não confiável. API valida identidade/contexto e limites; Agent não autoriza ações.
Policy é a autoridade independente, default deny; Broker revalida a autorização no servidor.
Somente Data Access pode receber credencial PostgreSQL. Finance produz cálculos determinísticos.
Agent não acessa DB, SQL, shell ou ferramentas diretamente. Resposta de LLM é dado não confiável.
Ausência/erro em autorização ou schema bloqueia execução; falha de cálculo/tool não produz números inventados.

Na etapa 2, essas fronteiras são exigências e checks estáticos; enforcement de rede será validado na etapa 3,
contratos na 4 e enforcement de execução nas etapas 7–10. Não confundir preparação com implementação concluída.

Segredos externos ao Git. Logs sem credenciais/conteúdo privado. Fixtures são DEMO e não contratos reais Itaú.
O repositório é público: revisão de árvore, histórico e XLSX expandido antes de cada push.

Etapa 9: enforcement estático e de rede certificado; Broker reautoriza com contexto DEMO do servidor e aplica schemas/timeout/auditoria. Tentativas de decisão forjada, acesso direto, cliente trocado e ferramenta não permitida têm testes. A semântica financeira do contrato rejeita resultados incoerentes. A identidade atual é exclusivamente DEMO; não representa autenticação bancária real.

Integração competition: API resolve sessão opaca em registry privado e assina prova vinculada a cliente/janela/valor/correlation. Agent/modelo não possuem a chave nem escolhem id_usuario. Policy verifica prova/revogação antes de conceder somente leitura/análise. Broker reautoriza cada tool; Data exige HMAC Broker–Data e reconsulta Policy. Data–Policy tem rede privada própria; egress BigQuery é exclusivo de Data. São identidades operacionais da competição, não autenticação bancária produtiva; GCP requer identidades de workload/TLS/ingress apropriados.
