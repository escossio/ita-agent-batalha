# Regras permanentes

- Leia este arquivo e `STATUS.md` antes de agir; leia arquivos existentes antes de editar.
- Siga obrigatoriamente `docs/architecture/IMPLEMENTATION_ORDER.md`, na ordem especificada pelo usuário. Etapas 1–10 definidas; 11–18 aguardam especificação.
- Valide e registre evidência/checkpoint de cada etapa antes de iniciar a próxima.
- Se uma etapa bloquear, preserve o último estado válido; não antecipe etapas posteriores.
- Atualize `STATUS.md` ao terminar cada etapa relevante. Prefira alterações mínimas e reversíveis.
- Preserve os originais das fontes; nunca os sobrescreva silenciosamente. Dados sensíveis ficam fora do repositório público.
- Antes de cada push, examine árvore e histórico: segredos, credenciais, dados pessoais/bancários, dumps e detalhes privados de infraestrutura.
- AGT é control plane. Apenas inspeção, lint/diff-check e testes unitários curtos localmente.
- PostgreSQL completo, migrações, suítes full e validações longas usam workers distribuídos, associados ao SHA correto. Use o fluxo equivalente deste projeto quando implementado; não despache este repositório com um runner de outro projeto sem conferir compatibilidade.
- Indisponibilidade do pool bloqueia validação pesada; nunca faça fallback pesado local sem autorização explícita.
- Não use tmux, não altere configuração global e não toque ambientes live externos.
- CI certifica; não habilite autofix, automerge ou alteração automática do produto por agentes.
- Não inicie a vertical slice “Até o próximo salário dá?” sem concluir 1–10 e receber instrução posterior explícita.

- Voz e Tom ausente: `SOURCE_PENDING_LOCAL_COPY`, dependência documental não bloqueante para estrutura e preparação; não inventar conteúdo nem regras definitivas dessa fonte.
- Somente fontes locais e GitHub/repositório versionado; não tentar recuperar Drive nem adicioná-lo ao runtime.
