# ADR-0001 — conflitos e limites das fontes

Data: 2026-09-26. Aceito para fontes locais; atribuições a Voz e Tom são provisórias.

| Caso | Evidência | Decisão verificável |
| --- | --- | --- |
| “Agora não” versus combinar retorno | CT-150, linha 151; contraparte informada pelo usuário, sem cópia de Voz e Tom | Recusa encerra abordagem atual, sem agendar/repetir. Retorno exige pedido explícito separado e consentimento vigente; não implementar agendamento nesta fundação. Não presumir data ou autorização. |
| Ignorar mensagem versus insistir | CT-148, CT-250; CT-200 revoga alertas semelhantes | Silêncio não é consentimento. Não repetir abordagem; opt-out impede nova iniciativa. |
| Elegível versus recomendar | R011, R013, R014; Visao_Geral | Elegibilidade é necessária, insuficiente. Exigir necessidade aderente, dados válidos e policy; disponibilidade desconhecida não permite oferta. |
| Crédito em dificuldade | R001–R004 | Dívida/segurança primeiro; crédito não é resposta automática. Na fundação, estado crítico bloqueia novos produtos de crédito. É limite conservador local, não proibição eterna atribuída à fonte. |
| Fim de parcela versus todo valor livre | Necessidade_Produto e R009 | Recalcular compromissos/novas despesas antes de afirmar folga; parcela encerrada não equivale a sobra líquida. |
| Renda maior versus base permanente | R010, R011; cenários da família renda | Entrada pontual/recorrência desconhecida não aumenta renda permanente. Perguntar/confirmar origem e recorrência. |
| Recuperação versus causalidade | R012; família recuperação | Não atribuir melhora ao ITA, não inferir estabilidade sem histórico suficiente ou com dados incompletos. |
| Valores do HTML versus cálculo | protótipo sanitizado; Contrato_Tecnico | Valores e margem do protótipo são exemplos. Não viram constante financeira, regra universal ou fallback. HTML arquivado não é servido. |

Rastreabilidade de regras: `config/rules.json`, com SHA, aba e linha. Cenários: `evals/scenarios.jsonl`, mesma rastreabilidade. Não há conflito confirmado com texto de Voz e Tom enquanto SOURCE_PENDING_LOCAL_COPY.

A cópia futura exige revisão deste ADR e das cinco categorias de Voice antes de tornar regras específicas definitivas. Não altera silenciosamente o comportamento certificado.
