# Dataset de avaliação/regressão

250 cenários originais, cinco famílias de 50, extraídos sem alteração de ID, pergunta/gatilho, contexto ou comportamento esperado.
Não são fine-tuning ou treinamento automático. `integrity.json` registra contagens comparadas à aba Resumo.
Cada linha de `scenarios.jsonl` aponta a arquivo, SHA-256, aba, linha e colunas originais.
`expectations/source_behaviors.json` conserva critérios descritivos; assertions contra runtime são NOT_IMPLEMENTED até a etapa 13.
Integridade aprovada não é uma taxa de sucesso funcional dos 250 cenários.

```sh
python3 scripts/derive_sources.py --check
```

Regeneração intencional: `python3 scripts/derive_sources.py`. Exige os XLSX locais com hashes congelados; CI apenas confere drift.
Runtime não lê Excel. O resumo fonte exige exatamente 50 casos por família; omissão, duplicação, alteração de ID ou divergência falha.
Voz e Tom está SOURCE_PENDING_LOCAL_COPY. Nenhuma avaliação de tom dessa fonte é considerada certificada.
