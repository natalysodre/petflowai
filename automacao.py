"""Envia o atendimento já classificado para o fluxo do n8n (webhook)."""

import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

from schemas import Automacao

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()
TIMEOUT_SEGUNDOS = 15


def enviar_para_n8n(payload: dict) -> Automacao:
    if not N8N_WEBHOOK_URL:
        return Automacao(
            enviado=False, status_http=None, resposta=None,
            detalhe="N8N_WEBHOOK_URL não configurada no .env da API.",
        )

    requisicao = urllib.request.Request(
        N8N_WEBHOOK_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(requisicao, timeout=TIMEOUT_SEGUNDOS) as resposta:
            status = resposta.status
            corpo = resposta.read().decode("utf-8")
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            detalhe = ("Webhook do n8n não encontrado (404): ative o fluxo ou, no modo teste, "
                       "clique em Execute workflow antes de enviar.")
        else:
            detalhe = f"O n8n respondeu com erro {erro.code}."
        return Automacao(enviado=False, status_http=erro.code, resposta=None, detalhe=detalhe)
    except (urllib.error.URLError, TimeoutError, OSError):
        return Automacao(
            enviado=False, status_http=None, resposta=None,
            detalhe="Não foi possível conectar ao n8n. Ele está rodando na porta 5678?",
        )

    try:
        dados = json.loads(corpo) if corpo else None
    except json.JSONDecodeError:
        dados = {"texto": corpo}
    if isinstance(dados, list):
        dados = dados[0] if dados else None
    if dados is not None and not isinstance(dados, dict):
        dados = {"valor": dados}

    return Automacao(enviado=True, status_http=status, resposta=dados, detalhe="Encaminhado pelo n8n.")
