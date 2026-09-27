# ITA — Batalha de Agentes Itaú

Fundação do agente financeiro ITA. Repositório público: <https://github.com/escossio/ita-agent-batalha>.

**Etapas 1–12 certificadas com mock explícito. Integração Vertex AI/Gemini implementada; BigQuery conectado à jornada por identidade/Policy/Broker, com contexto incompleto explícito e testes sem GCP. Voz e Tom: `SOURCE_PENDING_LOCAL_COPY`.**

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
apps/                 # reservado para apresentação
services/             # fronteiras HTTP isoladas
packages/             # runtime HTTP comum
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

A jornada DEMO percorre Web → API → Agent → Policy/Broker → Finance/Data → PostgreSQL.
Execução e coordenação em [CONTAINERS.md](docs/architecture/CONTAINERS.md). AGT coordena; builds/PostgreSQL/smoke usam workers.
Vertex AI/Gemini é o provider oficial; CI usa mock explícito. Veja [provider](docs/architecture/AGENT_PROVIDER.md) e [mapeamento BigQuery](docs/architecture/BIGQUERY_INVENTORY.md).

O HTML arquivado é referência recebida, não uma implementação da vertical slice por este projeto.
Seu código usa valores fixos e insere entrada do usuário em `innerHTML`; não deve ser servido como aplicação pública nem reutilizado como runtime. A sanitização de privacidade está documentada em `docs/source/INTAKE_REVIEW.md`.

## Operação

Workspace isolado no padrão de projetos do AGT. Configuração Git local com identidade pública noreply.
AGT coordena; workers executam cargas pesadas e certificam o SHA solicitado. GitHub Actions certifica alterações via PR; veja `docs/security/GITHUB_GOVERNANCE.md`.
A vertical slice DEMO e os testes adversariais foram certificados; não houve deploy externo, migração GCP, integração bancária ou movimentação financeira. O modo da competição usa o adapter BigQuery e retorna contexto incompleto quando faltam dados de projeção. CI usa transporte sintético identificado. Veja [operação e limites](docs/demo/COMPETITION_RUNTIME.md).

Acesso ao Drive não é necessário nem será reconstruído. Trabalhar somente com artefatos locais; o GitHub/repositório público é a fonte versionada principal. Regras específicas de Voz e Tom dependem de sua futura cópia local.

## Target final: Cloud Run

Readiness e pacote Cloud Shell preparados, sem deployment e sem concluir a etapa 16. Sete serviços de negócio usam identidade nativa/IAM; PostgreSQL fica no desenvolvimento/teste local. Preflight real confirmado pelo operador. Próximo gate: criar **somente nosso Artifact Registry `ita-escossio`** no Cloud Shell e fornecer saída sanitizada. Recursos existentes são EXTERNAL_READ_ONLY; nenhum deploy/push/IAM neste gate. Veja [pacote Cloud Shell](infra/gcp/cloudrun/README.md), [readiness](docs/architecture/CLOUD_RUN_TARGET.md) e [fronteiras IAM](docs/security/GCP_IAM_BOUNDARIES.md). Nenhuma credencial GCP é necessária no AGT/CI.
