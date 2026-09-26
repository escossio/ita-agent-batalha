# ITA — Batalha de Agentes Itaú

Fundação do agente financeiro ITA. Repositório público: <https://github.com/escossio/ita-agent-batalha>.

**Estado: etapa 1 parcial, bloqueada pela ausência das quatro fontes. Não há aplicação executável.**

A sequência oficial está em [IMPLEMENTATION_ORDER.md](docs/architecture/IMPLEMENTATION_ORDER.md).
O estado verificável e as pendências estão em [STATUS.md](STATUS.md).
As etapas 2–10 não foram iniciadas: sua execução depende da validação da etapa anterior.

## Documentos-fonte

Os nomes abaixo foram fornecidos no briefing de implantação. Os arquivos e links de origem ainda não foram disponibilizados/localizados. Esta tabela é um inventário pendente, não comprovação de incorporação.

| Fonte esperada | Origem confirmada | Função | Captura |
| --- | --- | --- | --- |
| `ITA_arvore_decisao_regras_produtos.xlsx` | Pendente | Regras, árvore decisória e restrições de produtos | Pendente |
| `cenarios_treinamento_ITA_250.xlsx` | Pendente | Fonte de 250 cenários de avaliação/regressão; não treinamento automático de modelo | Pendente |
| `prototipo_IAI_ITA_jornada.html` | Pendente | Referência de jornada e interação | Pendente |
| `Ita: Voz e Tom` | Pendente; pode ser Google Docs | Diretrizes de linguagem e comportamento a classificar na etapa 5 | Pendente |

Na incorporação, registrar proveniência, data UTC, tamanho e SHA-256 em `docs/source/manifest.json`.
Se Voz e Tom estiver no Google Docs, capturar Markdown com origem e data explícitas.
Originais sensíveis devem ser preservados fora do Git; publicar somente cópia sanitizada identificada e revisada.
Fontes ficam em `docs/source/`; derivados reproduzíveis ficam em `config/` e `evals/` a partir da etapa 5.

## Estrutura inicial

```text
apps/                 # reservado
services/             # reservado
packages/             # reservado
config/               # reservado
evals/                # reservado
docs/
  source/             # inventário; fontes ainda ausentes
  architecture/       # ordem oficial de implementação
  adr/                # reservado
  security/           # evidência da revisão antes da publicação
  demo/               # reservado
infra/
  docker/             # reservado
  gcp/                # reservado
tests/                # reservado
.github/workflows/    # reservado; nenhum check configurado
```

`.env.example` e `compose.yaml` são marcadores sem credenciais nem serviços.
`docker compose up` ainda não levanta o projeto; containerização pertence à etapa 3.
Nenhuma dependência de runtime/modelo foi escolhida ou instalada nesta etapa.

## Operação

Workspace isolado no padrão de projetos do AGT. Configuração Git local com identidade pública noreply.
AGT coordena; workers executam cargas pesadas e certificam o SHA solicitado. GitHub Actions será a certificação pública na etapa 2.
Não há deploy externo, migração GCP, API bancária, movimentação financeira ou vertical slice implementados.
