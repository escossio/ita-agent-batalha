# Contratos 1.0

Modelos em `packages/contracts/models.py`; JSON Schema versionado em `packages/contracts/schemas/v1/`.
Modelos estritos: campos extras, coercion de strings/floats/bools para dinheiro e versões desconhecidas são rejeitados.
`schema_version` é obrigatório. Campos listados como `required` no JSON Schema são obrigatórios mesmo quando aceitam null.
Campos com default são opcionais. Dados críticos não usam dict livre. Nenhum contrato pressupõe APIs reais Itaú.

| Contrato | Autoridade e conteúdo |
| --- | --- |
| CustomerContext | Contexto DEMO com consentimento, proveniência, nível financeiro e sinal de segurança explícitos; entrada validada não equivale a autorização |
| FinancialSnapshot | Data Access é a fonte: saldo, próxima renda nullable, compromissos tipados e histórico nullable; ausência de dados nunca vira zero implícito |
| Eligibility | Elegibilidade por produto com estado eligible/ineligible/unknown e origem; não implica recomendação |
| PolicyDecision | Somente Policy pode emitir autoridade; deny/handoff não pode conceder actions/tools/produtos; digest vincula requisição; expiração UTC |
| ToolRequest | Tool e argumentos discriminados, IDs e customer; policy_decision_id é rastreabilidade, não permissão confiável do caller |
| ToolResult | Sucesso exige resultado correspondente à tool; falha exige erro e proíbe resultado financeiro |
| AgentResponse | Resultado financeiro exige evidência de ToolResult bem-sucedido e correlation ID consistente |
| AuditEvent | Evento/status/componente enumerados, IDs, tempos e digest; sem campo livre de payload privado |

Dinheiro em centavos inteiros BRL, limitado a magnitude de um trilhão de centavos. Saldo pode ser negativo;
valores de gasto/renda/compromisso são não negativos. Datas são ISO válidas; timestamps exigem UTC.
Próxima renda é posterior à data-base. Parcela precisa de número/total coerentes; IDs/meses duplicados rejeitados.
As duas tools iniciais são data.snapshot e finance.project. Novas capacidades exigem revisão explícita dos contratos/testes.

JSON Schema exprime estrutura; invariantes entre campos também exigem os validators executáveis (não confiar apenas em validação superficial de JSON).
Autenticidade, freshness, autorização e correção aritmética serão exercitadas pelos componentes responsáveis nas etapas seguintes.
O request_digest é SHA-256 do JSON de ToolRequest sem policy_decision_id, chaves ordenadas, sem espaços e UTF-8; inclui IDs, versão, customer, tool e argumentos. O Broker deve obter/verificar a decisão independentemente e rejeitar IDs/customer/resultados divergentes.
O LLM não é fonte de contexto, elegibilidade ou números autoritativos. Voz e Tom permanece SOURCE_PENDING_LOCAL_COPY.

```sh
python3 scripts/export_contracts.py --check
python3 -m unittest discover -s tests -v
```

Mudança incompatível exige nova versão explícita, migração/testes e atualização dos consumidores.
Regeneração intencional: `python3 scripts/export_contracts.py`; CI usa somente `--check` e falha em drift.
