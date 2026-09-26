# Agent e provider substituível

Decisão do usuário, 2026-09-26: Vertex AI/Gemini via ADC/identidade, sem chave hardcoded. Mock explícito autorizado para certificação quando não houver credencial. Descoberta ADC no AGT retornou DefaultCredentialsError; nenhum projeto pago, chave ou infraestrutura externa foi criado. Ativação real permanece externa e **não bloqueia os gates estruturais**.

`ModelProvider` define interpret/compose; domínio, Policy e Broker não importam Google. O adaptador `VertexGeminiProvider` em `vertex.py` usa generateContent REST e google-auth ADC, com host derivado de projeto/região/modelo validados. Sem API key, ferramentas nativas do modelo, SQL ou execução arbitrária. Adapter de modelo fica somente na imagem Agent. Dependências HTTP/ADC pinadas em requirements-gcp.txt são consumidas pelas imagens Agent e Data; não entram no domínio.

Modelo produz ModelPlan validado: intenção e solicitação de ferramenta da allow-list. Não escolhe cliente, saldo, gasto proposto ou elegibilidade. Gasto vem da entrada estruturada. Agent consulta Policy; Broker reautoriza independentemente; somente resultados tipados voltam para AgentResponse. Contexto recebido pode restringir uma solicitação, nunca conceder permissão que Policy negou. Contexto de autorização é do servidor.

A composição inicial é limitada a NarrativePlan: o modelo escolhe introdução e fechamento dentro de vocabulário seguro. Renderer insere exclusivamente valores do Finance, identifica estimativas e mantém decisão com cliente. Essa restrição deliberada evita invenções em texto livre; não é uma implementação completa da fonte Voz e Tom ausente. Resposta inválida/falha do modelo gera erro, sem fallback para mock ou números.

`ITA_MODEL_PROVIDER=mock` é o default de DEMO e CI; AgentResponse identifica model_provider. Mock é um substituto determinístico de teste, não prova de qualidade Gemini. Não usar seus testes como evidência de certificação real de modelo.

Ativação externa: definir ITA_MODEL_PROVIDER=vertex, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION e ITA_VERTEX_MODEL; prover ADC por identidade/workload identity do ambiente autorizado. Em Compose, compose.vertex.yaml acrescenta egress exclusivo do Agent e exige as três configurações. O override não fornece credencial nem libera acesso ao banco. Não montar credenciais de outros projetos, não versionar credenciais e não expor portas internas. Ativação Vertex real requer smoke/evals próprios; sua ausência continua explícita nos relatórios.

Fontes técnicas consultadas em 2026-09-26:
- [ADC e descoberta de identidade](https://google-auth.readthedocs.io/en/latest/reference/google.auth.html).
- [generateContent](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference).
- [Saída estruturada](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output).

Não há memória persistente de conversa nesta fundação; apenas contexto validado da requisição, minimizando retenção. Outros frameworks podem implementar o mesmo port sem alterar Finance, Policy ou Broker.

## Ampliação autorizada: ambiente do hackathon

O usuário informou teste manual HTTP 200 / VERTEX_OK com a identidade do ambiente Google, Vertex API habilitada e acesso BigQuery. Essa evidência é **relatada pelo operador**, não uma chamada reproduzida nesta sessão do AGT. A inspeção local continua sem ADC. Não se cria chave nem se transfere identidade entre ambientes.

Provider oficial: Vertex AI/Gemini. O mock permanece exclusivamente como seleção explícita para CI/desenvolvimento. As mesmas camadas da imagem Agent já contêm as duas implementações; escolher projeto/região/modelo/provider em runtime não recompila domínio nem inclui segredos na imagem. A ativação real exige identidade e conectividade do runtime Google; o override de Compose, sozinho, não concede acesso.

O inventário e o gate de mapeamento BigQuery estão em [BIGQUERY_INVENTORY.md](BIGQUERY_INVENTORY.md). O Agent não recebe configuração de dataset e sua identidade futura deve ter somente a permissão de modelo necessária; Data Access recebe identidade separada para dados. A identidade ampla usada no teste manual não é o desenho de menor privilégio da aplicação.
