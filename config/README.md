# Artefatos de fontes

`rules.json`: R001–R014, conjunções tipadas com igualdade (SIM/NÃO → booleanos), textos de prioridade/produto/cuidado e referências de célula.
`source_tables.json`: todas as abas das duas planilhas com coordenadas/textos preservados, incluindo árvore de decisão, mapa necessidade/produto, contrato técnico e exemplos.
`voice/source_status.json`: cinco categorias solicitadas, ainda vazias e não definitivas por SOURCE_PENDING_LOCAL_COPY.

Transformação reproduzível em `scripts/derive_sources.py`. Não executar strings de condições via eval e não carregar XLSX em runtime.
Os textos prescritivos continuam rastreáveis; sua aplicação será explícita no Policy Engine após os ADRs da etapa 6.
Nenhum conflito foi resolvido implicitamente pelo conversor.
