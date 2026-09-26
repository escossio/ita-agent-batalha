# Recepção e congelamento das fontes

Nenhuma das quatro fontes foi incorporada. Não há arquivos fictícios substituindo originais.
O inventário está em `manifest.json`; valores nulos significam evidência ainda não obtida.

Em 2026-09-26, a pasta indicada pelo usuário continha `ITA_arvore_decisao_regras_produtos.xlsx` (12.624 bytes), mas o ZIP interno falhou na validação. Original preservado sem alterações e cópia privada conferida fora do Git; arquivo excluído localmente do staging automático até substituição por cópia íntegra e revisão. As demais três fontes continuam ausentes. Detalhes em [INTAKE_REVIEW.md](INTAKE_REVIEW.md).

Para concluir a etapa 1:

1. Obter os dois XLSX, o HTML e o documento Voz e Tom em origem confirmada.
2. Examinar conteúdo, metadados, comentários, planilhas ocultas, links e conteúdo incorporado antes de publicar.
3. Se houver informação sensível, preservar o original em armazenamento privado fora do Git e preparar uma cópia sanitizada explicitamente identificada. Não gravar a versão sensível no histórico.
4. Preservar os arquivos aprovados sem transformação silenciosa. Para Google Docs, exportar representação Markdown e registrar origem, data UTC e eventual limitação de fidelidade.
5. Registrar tamanho, SHA-256, origem e data de captura de cada arquivo. Confirmar os hashes após a cópia.
6. Atualizar README e STATUS, revisar árvore e histórico antes do push e criar checkpoint.

Conversão das regras, contagem/famílias dos 250 cenários e classificação de Voz e Tom pertencem à etapa 5. Não produzir essas representações enquanto as etapas anteriores não forem validadas.
