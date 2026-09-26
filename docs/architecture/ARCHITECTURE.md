# Arquitetura ITA

Estado da etapa 3: serviços isolados com saúde/logs/correlation ID; fluxos de negócio ainda não implementados.
Contratos entram na etapa 4; Policy, Finance, Broker e Agent nas etapas 7–10. O desenho abaixo é a direção de comunicação autorizada, não afirma jornadas prontas.

```mermaid
flowchart TD
  browser[Browser] --> web[web]
  web --> api[api]
  api --> agent[agent]
  agent --> policy[policy: default deny]
  agent --> broker[tool-broker]
  broker --> policy
  broker --> finance[finance: determinístico]
  broker --> data[data: acesso a dados]
  data --> postgres[(postgres: rede interna)]
  policy -. deny / humano .-> broker
  broker -. resultado estruturado .-> agent
  agent -. AgentResponse .-> api
```

Cada seta de infraestrutura é uma rede privada de par de serviços. Não há rede interna comum a todos.
Agent não compartilha rede com Finance, Data ou PostgreSQL e não recebe seus arquivos/segredos.
Broker também não compartilha rede com PostgreSQL; Data é a única porta para o banco.
Policy independente impede a autorização pelo Agent; enforcement funcional será certificado nas etapas respectivas.

HTTP apenas interno, sem exposição de portas ao host salvo web em loopback. mTLS/identidade forte ficam para implantação externa;
não considerar rede Docker como autenticação de usuário final. Host/Docker daemon são parte da base confiável.
Observability é uma fronteira reservada com healthcheck; logs estruturados já existem, tracing/métricas completos na etapa 15.

O domínio será desacoplado do modelo, do framework e do provedor cloud. Nenhuma API real Itaú é presumida.
Google Drive não pertence à arquitetura. Voz e Tom pendente não gera conteúdo ou permissões por inferência.
