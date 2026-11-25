// Rota do servidor Next: repassa a mensagem para a API FastAPI.
// Fluxo completo: interface -> esta rota -> API (classifica com Gemini) -> n8n (encaminha).

const PETFLOW_API_URL = process.env.PETFLOW_API_URL ?? "http://localhost:8000";

export async function POST(request) {
  const corpo = await request.json();

  try {
    const resposta = await fetch(`${PETFLOW_API_URL}/classificar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
      cache: "no-store",
    });

    const texto = await resposta.text();
    let dados;
    try {
      dados = JSON.parse(texto);
    } catch {
      dados = { detail: texto || `erro ${resposta.status}` };
    }

    return Response.json(dados, { status: resposta.status });
  } catch {
    return Response.json(
      { detail: "Não consegui falar com a API. Ela está rodando na porta 8000?" },
      { status: 503 }
    );
  }
}
