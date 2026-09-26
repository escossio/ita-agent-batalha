# Recebimento de fontes — 2026-09-26

Origem imediata: pasta `docs/source/` indicada pelo usuário nesta sessão. Proveniência anterior não informada.
Captura/verificação: 2026-09-26T21:40:30Z.

## Primeiro recebimento: cópia inválida, não publicada (histórico)

- Nome: `ITA_arvore_decisao_regras_produtos.xlsx`.
- Tamanho observado em duas leituras: 12.624 bytes.
- SHA-256 estável: `31e653e975cd64d8cfa51a629d749e23eb2c08a777e35227594f9da65249c331`.
- `zipfile.ZipFile.testzip()` falhou com `OSError: [Errno 22] Invalid argument`.
- Diretório ZIP lista 19 entradas. A leitura individual de 11 falhou: quatro com offsets negativos e sete com `Bad magic number for file header`; oito entradas foram lidas.
- O registro de fim de ZIP informa offset 13.177 para o diretório central, além do tamanho total do arquivo. Não se trata de erro de regra de negócio ou falha em teste de produto.
- Não é possível certificar a integridade nem revisar todo o conteúdo/metadados. A causa da corrupção durante geração/cópia não foi determinada.
- Original não modificado; cópia preservada fora do repositório público com hash idêntico. Nenhum reparo ou transformação foi aplicado.
- Arquivo não adicionado ao índice/histórico; exclusão local em `.git/info/exclude` protege contra inclusão acidental. Essa exclusão precisa ser removida após receber e aprovar uma nova cópia.

## Reenvio — 2026-09-26T21:44:50Z

O usuário disponibilizou três arquivos no diretório local indicado nesta sessão. Originais e backups privados preservados; proveniência anterior não informada. A cópia inválida anterior já estava arquivada fora do repositório; durante esta revisão o exemplar no workspace foi atualizado externamente e conferido como idêntico ao reenvio íntegro.

- Regras: 14.505 bytes, seis abas; todas as 19 entradas ZIP legíveis, CRC válido e XML bem formado. Hash `c9db3d9970e23cdc2240cbdbbc4897867c92bde2fe6f859fe7b28191e61002f5`.
- Cenários: 24.017 bytes, duas abas; todas as 11 entradas ZIP legíveis, CRC válido e XML bem formado. Hash `8bdd28d94bce9b41e8f23ebdca4e628f794fbd9b9c990354931cccd5278a1e74`.
- Nenhuma aba oculta, macro, objeto incorporado, comentário, propriedade pessoal ou relacionamento externo encontrado nas duas planilhas. Conteúdo examinado: regras e situações exemplificativas, sem identificadores de clientes detectados.
- HTML original: 12.144 bytes; hash `a96d4fe3c9d2591dfb2945f171d7a18e329cfb233ddfdd6a4ccb7948624eab23`. Não publicado: contém iniciais e final de cartão associados a uma referência de captura de tela, cuja natureza real/sintética não foi confirmada.
- Publicada somente `prototipo_IAI_ITA_jornada.sanitized.html`: iniciais substituídas por DEMO, cartão substituído por marcador DEMO e aviso de referência ilustrativa inserido. Hash do resultado no manifesto; original intacto fora do Git.
- Gitleaks sobre os arquivos e todo o conteúdo ZIP expandido: zero achados. Busca por e-mail, CPF, telefone e URLs no conteúdo textual: zero achados. A inspeção manual identificou os elementos do HTML sanitizados acima.

Sanitização reproduzível (usar uma saída nova; o script recusa sobrescrever arquivos e exige o hash do original aprovado):

```sh
python3 docs/source/sanitize_prototype.py CAMINHO_ORIGINAL_PRIVADO SAIDA_NOVA.html
sha256sum SAIDA_NOVA.html
```

O script é exclusivamente para publicação segura da fonte na etapa 1. Não converte regras ou cenários para runtime/evals. O HTML preserva a lógica original como evidência: cálculos fixos e entrada inserida em `innerHTML`, com risco de injeção no DOM. Não servir como produto. Nenhum framework, cálculo financeiro ou vertical slice foi implementado nesta recepção.

O cenário CT-150 foi localizado em `Cenarios_Treino`, linha 151: “agora não” encerra a abordagem. A comparação com Voz e Tom depende do documento ausente e será tratada na etapa 6; nenhuma policy foi decidida agora.

## Fonte ainda não capturada

`Ita: Voz e Tom`: usuário informou `https://claude.ai/artifact/YEMJ288EEVpnw1GgY4WE2e`. Em 2026-09-26, a ferramenta web não conseguiu ler o endereço; tentativa HTTP direta retornou 403. Nenhum conteúdo foi obtido e não há hash/captura do documento. Necessário texto ou exportação acessível; não confundir o endereço com evidência do conteúdo.

Link posterior: `https://drive.google.com/drive/project/17pVdp0OtuAwK48QiFy2YS16FYxRCt-A6`. Metadados identificaram “Ita - Grupo 01”, MIME `application/vnd.google-apps.project`; não é um Google Doc. A consulta de filhos retornou vazia, a rota `/drive/project` foi rejeitada pelo fetch e o download pelo ID retornou 403. O navegador web também não leu a página. Não foi possível identificar/capturar Voz e Tom por esse agrupamento; solicitado link direto do documento ou texto.

## Gate da etapa 1 — atualização autorizada

Três fontes locais revisadas e congeladas. Gate estrutural aprovado com exceção documental explícita do usuário: Voz e Tom está `SOURCE_PENDING_LOCAL_COPY` e não bloqueia governança, containers, contratos, arquitetura ou preparação. Conteúdo e regras dessa fonte não são considerados definitivos sem cópia versionada. Não tentar acessar Drive novamente; relatos de acesso acima são somente histórico.
