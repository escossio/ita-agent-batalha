# ITA — Batalha de Agentes Itaú

Fundação do agente financeiro ITA. Repositório público: <https://github.com/escossio/ita-agent-batalha>.

**Etapa 1: gate estrutural aprovado. Três fontes congeladas; Voz e Tom é `SOURCE_PENDING_LOCAL_COPY`, dependência documental não bloqueante.**

A sequência oficial está em [IMPLEMENTATION_ORDER.md](docs/architecture/IMPLEMENTATION_ORDER.md).
O estado verificável e as pendências estão em [STATUS.md](STATUS.md).
Avanço sequencial com gates e checkpoints. Ordem completa 1–18 registrada; vertical slice autorizada apenas na etapa 11, após os gates anteriores.

## Documentos-fonte

Os nomes abaixo foram fornecidos no briefing de implantação. Após uma cópia inicial inválida, o usuário disponibilizou as duas planilhas íntegras e o HTML no diretório local indicado nesta sessão. Proveniência anterior não informada. Os hashes, tamanhos e horários estão em `docs/source/manifest.json`.

| Fonte esperada | Origem confirmada | Função | Captura |
| --- | --- | --- | --- |
| `ITA_arvore_decisao_regras_produtos.xlsx` | Reenvio local pelo usuário | Regras, árvore decisória e restrições de produtos | 2026-09-26; original íntegro, sem alterações |
| `cenarios_treinamento_ITA_250.xlsx` | Arquivo local fornecido pelo usuário | Fonte de cenários de avaliação/regressão; não treinamento automático de modelo | 2026-09-26; original íntegro, sem alterações |
| `prototipo_IAI_ITA_jornada.html` | Arquivo local fornecido pelo usuário | Referência de jornada e interação | 2026-09-26; publicada cópia `prototipo_IAI_ITA_jornada.sanitized.html` |
| `Ita: Voz e Tom` | [Artefato Claude informado pelo usuário](https://claude.ai/artifact/YEMJ288EEVpnw1GgY4WE2e) | Diretrizes de linguagem e comportamento a classificar na etapa 5 | SOURCE_PENDING_LOCAL_COPY; não bloqueia estrutura |

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
  source/             # duas planilhas e HTML sanitizado; Voz e Tom pendente
  architecture/       # ordem oficial de implementação
  adr/                # reservado
  security/           # evidência da revisão antes da publicação
  demo/               # reservado
infra/
  docker/             # reservado
  gcp/                # reservado
tests/                # reservado
.github/workflows/    # certificação e CodeQL
```

`.env.example` e `compose.yaml` são marcadores sem credenciais nem serviços.
`docker compose up` ainda não levanta o projeto; containerização pertence à etapa 3.
Nenhuma dependência de runtime/modelo foi escolhida ou instalada nesta etapa.

O HTML arquivado é referência recebida, não uma implementação da vertical slice por este projeto.
Seu código usa valores fixos e insere entrada do usuário em `innerHTML`; não deve ser servido como aplicação pública nem reutilizado como runtime. A sanitização de privacidade está documentada em `docs/source/INTAKE_REVIEW.md`.

## Operação

Workspace isolado no padrão de projetos do AGT. Configuração Git local com identidade pública noreply.
AGT coordena; workers executam cargas pesadas e certificam o SHA solicitado. GitHub Actions certifica alterações via PR; veja `docs/security/GITHUB_GOVERNANCE.md`.
Não há deploy externo, migração GCP, API bancária, movimentação financeira ou vertical slice implementados.

Acesso ao Drive não é necessário nem será reconstruído. Trabalhar somente com artefatos locais; o GitHub/repositório público é a fonte versionada principal. Regras específicas de Voz e Tom dependem de sua futura cópia local.
