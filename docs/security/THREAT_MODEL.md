# Modelo de ameaças — fundação

| Ameaça | Controle exigido | Estado inicial |
| --- | --- | --- |
| Vazamento em Git/histórico/planilhas | Scanner de árvore, histórico e XML expandido; revisão de publicação | Implementado na governança |
| Mudança sem certificação | PR, checks obrigatórios, main protegida | Verificação pela API da etapa 2 |
| Prompt injection e autorização própria | Policy independente, Broker revalida e allow-list | Implementação posterior, não certificado |
| Bypass Agent → DB/tool | Imagens/rede segmentadas, imports bloqueados | Check estático; rede na etapa 3 |
| Números/eligibilidade inventados | Contracts, Finance determinístico, fontes confiáveis | Implementação posterior |
| Falha permissiva | Default deny e testes adversariais | Certificação na etapa 12 |
| HTML fonte com DOM injection | Não servir como produto; sanitizar identificadores | Fonte isolada e documentada |
| Dependência vulnerável | Manifestos pinados, alertas Dependabot, revisão humana | Sem autofix/updates automáticos |

Ativos: contexto financeiro, consentimento, decisões, dados, segredos, fontes e audit trail.
Fronteiras: browser/API, API/Agent, Agent/Policy/Broker, Broker/Finance/Data, Data/PostgreSQL.
Voz e Tom permanece SOURCE_PENDING_LOCAL_COPY; não constitui autoridade ausente de segurança.
