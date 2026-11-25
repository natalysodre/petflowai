"""PetFlow AI - API de triagem de mensagens para clínica veterinária.

Fluxo: interface (Next.js) -> esta API (Gemini) -> n8n (encaminhamento).
"""

from datetime import datetime, timezone
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from automacao import N8N_WEBHOOK_URL, enviar_para_n8n
from gemini_service import MODELO, MODO_SIMULADO, classificar_com_gemini
from roteamento import (
    ROTEAMENTO,
    aplicar_regra_seguranca,
    classificar_simulado,
    encaminhar,
    normalizar,
)
from schemas import ClassificacaoIA, MensagemEntrada, RespostaClassificacao

app = FastAPI(
    title="PetFlow AI",
    description="Assistente inteligente que classifica mensagens de tutores e indica o setor da clínica.",
    version="1.0.0",
)

TTL_SEGUNDOS = 300  # mensagens idênticas reaproveitam a classificação por 5 min

cache: dict[tuple[str, str], dict] = {}


@app.get("/")
def inicio():
    return {
        "mensagem": "PetFlow AI funcionando!",
        "modelo": MODELO,
        "modo_simulado": MODO_SIMULADO,
        "n8n_configurado": bool(N8N_WEBHOOK_URL),
        "docs": "/docs",
    }


@app.get("/categorias")
def listar_categorias():
    return [
        {"categoria": cat.value, "setor": setor, "fila": fila}
        for cat, (setor, fila) in ROTEAMENTO.items()
    ]


def _classificar(mensagem: str) -> tuple[ClassificacaoIA, str, str]:
    """Retorna (classificação, origem, status do cache)."""
    origem = "simulado" if MODO_SIMULADO else "gemini"
    chave = (MODELO if not MODO_SIMULADO else "simulado", normalizar(mensagem))
    agora = monotonic()

    registro = cache.get(chave)
    if registro and agora < registro["expira_em"]:
        return registro["classificacao"], origem, "HIT"
    cache.pop(chave, None)

    if MODO_SIMULADO:
        classificacao = classificar_simulado(mensagem)
    else:
        try:
            classificacao = classificar_com_gemini(mensagem)
        except Exception as erro:
            raise HTTPException(
                status_code=502,
                detail=f"Não foi possível classificar a mensagem com o Gemini: {type(erro).__name__}",
            )

    cache[chave] = {"classificacao": classificacao, "expira_em": monotonic() + TTL_SEGUNDOS}
    return classificacao, origem, "MISS"


@app.post("/classificar", response_model=RespostaClassificacao)
def classificar(dados: MensagemEntrada):
    mensagem = dados.mensagem.strip()
    if len(mensagem) < 3:
        raise HTTPException(status_code=422, detail="Mensagem vazia ou muito curta.")

    classificacao, origem, status_cache = _classificar(mensagem)

    # Garante a faixa 0-1 mesmo que o modelo extrapole
    classificacao = classificacao.model_copy(
        update={"confianca": round(min(max(classificacao.confianca, 0.0), 1.0), 2)}
    )
    classificacao, regra_acionada = aplicar_regra_seguranca(mensagem, classificacao)

    resultado = RespostaClassificacao(
        id=str(uuid4()),
        recebido_em=datetime.now(timezone.utc),
        canal=dados.canal,
        remetente=dados.remetente,
        mensagem_original=mensagem,
        classificacao=classificacao,
        encaminhamento=encaminhar(classificacao, regra_acionada),
        origem=origem,
        cache=status_cache,
    )

    # Fluxo: front -> API (classifica) -> n8n (encaminha). Se o n8n falhar,
    # a classificação continua sendo devolvida, com o motivo em "automacao".
    resultado.automacao = enviar_para_n8n(resultado.model_dump(mode="json", exclude={"automacao"}))
    return resultado


@app.delete("/cache")
def limpar_cache():
    cache.clear()
    return {"mensagem": "Cache limpo com sucesso."}
