'use strict';
const form = document.getElementById('chat');
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = document.getElementById('submit');
  button.disabled = true;
  document.getElementById('answer').textContent = 'Consultando seu planejamento…';
  document.getElementById('evidence').hidden = true;
  document.getElementById('provider').textContent = '';
  try {
    const correlationId = crypto.randomUUID();
    const response = await fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-Correlation-ID': correlationId},
      body: JSON.stringify({utterance: document.getElementById('question').value,
        amount_brl: document.getElementById('amount').value,
        consent_to_analysis: document.getElementById('consent').checked,
        demo_case: document.getElementById('case').value})
    });
    if (!response.ok) throw new Error('request failed');
    const result = await response.json();
    if (result.correlation_id !== correlationId || typeof result.message !== 'string') throw new Error('invalid response');
    document.getElementById('result-title').textContent = result.status === 'ok' ? 'Seu planejamento, com contexto.' : 'Precisamos respeitar este limite.';
    document.getElementById('answer').textContent = result.message;
    document.getElementById('provider').textContent = result.model_provider === 'mock' ? 'Demonstração com modelo simulado. Cálculo executado no backend.' : 'Provider: Vertex AI / Gemini.';
    document.getElementById('trace').textContent = JSON.stringify({correlation_id: result.correlation_id,
      intent: result.intent, policy_decision_id: result.policy_decision_id, status: result.status,
      tools: result.tool_results.map(tool => ({tool: tool.tool, status: tool.status, duration_ms: tool.duration_ms})),
      projection: result.financial_result}, null, 2);
    document.getElementById('evidence').hidden = false;
  } catch {
    document.getElementById('answer').textContent = 'Não foi possível concluir a consulta. Nenhum saldo foi presumido. Tente novamente.';
  } finally { button.disabled = false; }
});
