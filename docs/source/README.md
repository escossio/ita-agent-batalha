# Recepção e congelamento das fontes

Duas planilhas originais íntegras e uma cópia sanitizada do protótipo foram incorporadas. Voz e Tom está `SOURCE_PENDING_LOCAL_COPY`, pendência documental não bloqueante para estrutura, por instrução posterior do usuário.
O inventário está em `manifest.json`; valores nulos significam evidência ainda não obtida.

Em 2026-09-26, a primeira cópia da planilha de regras falhou na validação ZIP e foi preservada fora do Git. O reenvio trouxe uma cópia íntegra, a planilha de cenários e o protótipo HTML. As duas planilhas foram copiadas sem alteração; o HTML original permanece privado por conter identificadores de uma captura de tela. Detalhes e procedimento reproduzível de sanitização em [INTAKE_REVIEW.md](INTAKE_REVIEW.md).

Procedimento de recepção (gate estrutural liberado com três fontes; aplicar também à futura cópia de Voz e Tom):

1. Obter os dois XLSX, o HTML e o documento Voz e Tom em origem confirmada.
2. Examinar conteúdo, metadados, comentários, planilhas ocultas, links e conteúdo incorporado antes de publicar.
3. Se houver informação sensível, preservar o original em armazenamento privado fora do Git e preparar uma cópia sanitizada explicitamente identificada. Não gravar a versão sensível no histórico.
4. Preservar os arquivos aprovados sem transformação silenciosa. Para Google Docs, exportar representação Markdown e registrar origem, data UTC e eventual limitação de fidelidade.
5. Registrar tamanho, SHA-256, origem e data de captura de cada arquivo. Confirmar os hashes após a cópia.
6. Atualizar README e STATUS, revisar árvore e histórico antes do push e criar checkpoint.

Conversão das regras, contagem/famílias dos 250 cenários e classificação de Voz e Tom pertencem à etapa 5. Não produzir essas representações enquanto as etapas anteriores não forem validadas.
