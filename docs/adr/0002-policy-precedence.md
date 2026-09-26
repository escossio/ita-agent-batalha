# ADR-0002 — hierarquia e default deny

Data: 2026-09-26. Aceito. Origem: briefing do usuário e fontes locais R001–R014.

Ordem: segurança da pessoa → restrições obrigatórias/compliance → autorização → regra financeira → elegibilidade → política conversacional → voz e tom.

`config/policy_hierarchy.json` registra a ordem; `packages/governance/hierarchy.py` arbitra achados estruturados. Toda restrição sobrevive a sugestões de permissão de qualquer nível. A prioridade determina a razão/resposta principal, nunca cancela deny. Handoff também não concede ferramenta. Ausência de decisão é deny; desconhecido não equivale a falso, elegível ou autorizado. Mesma prioridade: deny precede handoff.

O motor da etapa 7 deverá produzir PolicyDecision e decidir cada capacidade explicitamente, sem interpretar textos de prompt como permissão. Restrições obrigatórias são entradas de configuração controladas pelo serviço, não uma alegação de certificação jurídica ou campo modificável pelo LLM.

Limite inicial: até três opções aderentes em estado estável, uma em estado apertado, zero em handoff/deny/estado crítico. É escolha local conservadora, rastreável e revisável, **não conteúdo atribuído a Voz e Tom**. Sem custos/perfil/horizonte/necessidade comprovados, produto permanece bloqueado.

Contato proativo exige consentimento vigente; “agora não” encerra a abordagem. Nenhum temporizador/agendamento nasce dessa frase. Linguagem não pode reabrir autorização nem fabricar números.
