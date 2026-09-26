# Recebimento de fontes — 2026-09-26

Origem imediata: pasta `docs/source/` indicada pelo usuário nesta sessão. Proveniência anterior não informada.
Captura/verificação: 2026-09-26T21:40:30Z.

## Planilha de regras: recebida, inválida e não publicada

- Nome: `ITA_arvore_decisao_regras_produtos.xlsx`.
- Tamanho observado em duas leituras: 12.624 bytes.
- SHA-256 estável: `31e653e975cd64d8cfa51a629d749e23eb2c08a777e35227594f9da65249c331`.
- `zipfile.ZipFile.testzip()` falhou com `OSError: [Errno 22] Invalid argument`.
- Diretório ZIP lista 19 entradas. A leitura individual de 11 falhou: quatro com offsets negativos e sete com `Bad magic number for file header`; oito entradas foram lidas.
- O registro de fim de ZIP informa offset 13.177 para o diretório central, além do tamanho total do arquivo. Não se trata de erro de regra de negócio ou falha em teste de produto.
- Não é possível certificar a integridade nem revisar todo o conteúdo/metadados. A causa da corrupção durante geração/cópia não foi determinada.
- Original não modificado; cópia preservada fora do repositório público com hash idêntico. Nenhum reparo ou transformação foi aplicado.
- Arquivo não adicionado ao índice/histórico; exclusão local em `.git/info/exclude` protege contra inclusão acidental. Essa exclusão precisa ser removida após receber e aprovar uma nova cópia.

## Fontes ainda ausentes

- `cenarios_treinamento_ITA_250.xlsx`.
- `prototipo_IAI_ITA_jornada.html`.
- `Ita: Voz e Tom` (arquivo ou link/exportação de Google Docs).

## Gate da etapa 1

Recebidas: 1/4. Aprovadas/incorporadas: 0/4. Etapa 1 permanece bloqueada; etapas 2–10 não iniciadas.
Próxima ação: receber cópia íntegra da planilha de regras e as três fontes restantes, repetir revisão de integridade/segurança e então congelar os originais aprovados.
