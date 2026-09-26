# Governança GitHub

Main exige PR e checks: lint, unit-contract, architecture, build, secret-scan e analyze (CodeQL Python).
Administradores também sujeitos à proteção; sem force push/delete, conversas resolvidas e branch atualizada.
CODEOWNERS aponta para o proprietário. Aprovações obrigatórias = 0 enquanto há apenas um mantenedor;
isso exige PR/checks mas não simula revisão independente inexistente.

Permissões padrão de Actions: contents read; somente CodeQL recebe security-events write.
Actions fixadas por SHA. Nenhum pull_request_target, autofix, auto-merge ou agente com escrita em CI.
Dependabot alerts habilitados; configuração com limite de PR zero e security updates automáticos desabilitados.
Isso fornece alertas sem modificação automática de código.

Na etapa 2, build certifica pacote fonte por round-trip; não finge build de containers inexistentes.
Architecture examina todo runtime existente e testa rejeição de imports proibidos, reportando contagem.
A etapa 3 acrescentará build/smoke de containers em worker; contracts entram na etapa 4.

Aplicação reproduzível da proteção pelo proprietário:

```sh
gh api --method PUT repos/escossio/ita-agent-batalha/branches/main/protection --input config/github-main-protection.json
gh api repos/escossio/ita-agent-batalha/branches/main/protection
gh api --method PUT repos/escossio/ita-agent-batalha/vulnerability-alerts
gh api --method DELETE repos/escossio/ita-agent-batalha/automated-security-fixes
```

O resultado efetivo da API e checks deve constar no STATUS; arquivo de configuração isolado não prova aplicação.
