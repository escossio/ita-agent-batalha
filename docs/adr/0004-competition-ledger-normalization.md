# ADR 0004 — FLOAT externo, centavos e limites semânticos do extrato

Estado: aceito para o mapeamento/adapter; ativação da jornada externa ainda não certificada.

## Evidência e decisão

Inventário local fornecido pelo operador, captura 2026-09-26T23:33:13Z: uma tabela visível, onze campos NULLABLE, dois campos monetários FLOAT (`vlr`, `saldo_apos`) e dois campos de parcela FLOAT. O usuário determinou normalização monetária para centavos inteiros em Data Access, antes de Finance.

Decisão local explícita: interpretar unidade major BRL apenas com configuração confirmada pelo operador. Converter representação decimal textual do número via `Decimal(str(value))`, multiplicar por 100 em precisão controlada e aplicar `ROUND_HALF_UP` por valor antes de agregação. Empates afastam de zero: 1.005 → 101, -1.005 → -101; 2.675 → 268. Nunca `int(float * 100)`, `round` binário ou soma FLOAT como valor financeiro autoritativo. A normalização não recupera precisão já perdida no FLOAT original; registrar `FLOAT64_APPROXIMATE` e flags de arredondamento. Não converter novamente valores já em centavos.

Limite de saída monetária: ±10^12 centavos, coerente com os contratos existentes. Fonte acima de ±10^10 unidades monetárias é rejeitada. Texto numérico limitado a 128 caracteres e expoente absoluto 128; sem formatos locais, NaN/Infinity, bool ou coerção de objetos. Null permanece null, não zero. Arredondamento identificado não transforma incerteza da fonte em exatidão histórica.

`parcela_atual`/`parcela_total` são tratados como contagens candidatas: número finito, inteiro exato e não negativo até 2^31−1. Não multiplicar por 100, truncar ou arredondar. Null/zero são preservados sem presumir inexistência de dívida. Dados insuficientes não geram compromissos futuros ou produto automaticamente. Número atual superior ao total é inconsistente e falha.

Timestamp REST é convertido de segundos decimais para micros inteiros UTC. `anomes` é preservado: o metadata não define timezone contábil nem garante equivalência com o mês UTC. Não escolher último saldo em empate de timestamp, deduplicar lançamentos sem chave ou classificar débito/crédito a partir de descrição. `tipo` e categorias continuam valores opacos até catálogo/regras explícitas.

## Contratos e consequências

Adicionar contrato de extrato da competição separado do FinancialSnapshot DEMO mantém proveniência e não inventa completude. Campos monetários de saída são somente int/null; modelos estritos rejeitam float, string e bool. Finance mantém os oito contratos existentes e seus cálculos determinísticos, sem dependência de BigQuery. Fonte externa não é fixture.

Schema permite ausência dos campos, mas leitura exige cliente igual ao escopo solicitado e data dentro da janela. Linhas sem cliente/data não podem entrar nessa consulta; a janela não representa conta completa. Mais de mil resultados, paginação pendente, erro ou timeout não produzem extrato parcial declarado completo. Adapter não calcula saldo atual, próxima renda, taxas, elegibilidade ou custos.

O schema não contém identidade autenticada/consentimento. Não expor nova rota ou tool antes de vínculo de cliente no servidor, Policy, Broker, auditoria e testes de bypass. Preparação do adapter não significa ativação em produção. Nenhum atalho por Agent/LLM ou frontend foi criado.

## Validação

Testes determinísticos usam somente dados sintéticos criados para CI: sinais/empates, artefato 0.1+0.2, nulos, NaN/Infinity, overflow, precisão subcentavo, parcelas fracionárias, schema drift, cliente/região errados, janela/limite/truncamento, parâmetros e erro sem fallback. Regressão da jornada existente permanece exigida nos workers, sem GCP. Bruto do inventário não participa dos testes ou imagens públicas.
