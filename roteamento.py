"""Regras de negócio determinísticas: setor de destino, prioridade e segurança.

A IA classifica; o código decide o destino. Assim o roteamento é previsível
e não depende do modelo "acertar" o nome do setor.
"""

import unicodedata

from schemas import Categoria, ClassificacaoIA, Encaminhamento, Urgencia

ROTEAMENTO: dict[Categoria, tuple[str, str]] = {
    Categoria.AGENDAMENTO: ("Recepção", "recepcao"),
    Categoria.SINTOMAS_URGENCIA: ("Equipe veterinária", "equipe_veterinaria"),
    Categoria.DUVIDAS_SERVICOS: ("Atendimento", "atendimento"),
    Categoria.VACINACAO_EXAMES: ("Recepção / Equipe veterinária", "recepcao_veterinaria"),
    Categoria.RECLAMACOES: ("Gerência", "gerencia"),
    Categoria.FINANCEIRO: ("Administrativo", "administrativo"),
}

PRIORIDADES = {
    Urgencia.EMERGENCIA: "P1 - imediata",
    Urgencia.ALTA: "P2 - alta",
    Urgencia.MEDIA: "P3 - mesmo dia",
    Urgencia.BAIXA: "P4 - normal",
}

LIMIAR_CONFIANCA = 0.6

# Rede de segurança: se aparecer um destes termos, a mensagem vira emergência
# mesmo que a IA tenha subestimado a urgência.
TERMOS_EMERGENCIA = [
    "convuls", "nao respira", "nao consegue respirar", "falta de ar",
    "sangrando muito", "sangramento", "hemorragia", "atropelad", "envenen",
    "veneno", "chumbinho", "desmaiou", "desmaio", "inconsciente",
    "engasgad", "parto", "nao acorda",
]


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def contem_termo_emergencia(mensagem: str) -> bool:
    texto = normalizar(mensagem)
    return any(termo in texto for termo in TERMOS_EMERGENCIA)


def aplicar_regra_seguranca(mensagem: str, c: ClassificacaoIA) -> tuple[ClassificacaoIA, bool]:
    if contem_termo_emergencia(mensagem) and c.urgencia != Urgencia.EMERGENCIA:
        ajustada = c.model_copy(update={
            "categoria": Categoria.SINTOMAS_URGENCIA,
            "urgencia": Urgencia.EMERGENCIA,
        })
        return ajustada, True
    return c, False


def encaminhar(c: ClassificacaoIA, regra_seguranca: bool) -> Encaminhamento:
    setor, fila = ROTEAMENTO[c.categoria]
    urgente = c.urgencia in (Urgencia.ALTA, Urgencia.EMERGENCIA)
    return Encaminhamento(
        setor=setor,
        fila=fila,
        prioridade=PRIORIDADES[c.urgencia],
        # Ex.: pedido de agendamento que cita animal com dor -> avisa veterinário também
        alerta_veterinario=urgente and c.categoria in (
            Categoria.SINTOMAS_URGENCIA, Categoria.AGENDAMENTO, Categoria.VACINACAO_EXAMES
        ),
        revisao_humana=c.confianca < LIMIAR_CONFIANCA,
        regra_seguranca_acionada=regra_seguranca,
    )


# ---------------------------------------------------------------------------
# Classificador simulado (MODO_SIMULADO=true): palavras-chave, sem IA.
# Serve só para testar a integração com o n8n sem gastar cota da API.
# ---------------------------------------------------------------------------
PALAVRAS_CHAVE = [
    (Categoria.RECLAMACOES, ["reclama", "absurdo", "pessim", "insatisf", "descaso", "demora", "gerente", "responsavel", "satisfacao"]),
    (Categoria.SINTOMAS_URGENCIA, ["vomit", "diarreia", "dor", "sangr", "nao come", "mancando",
                                   "febre", "tosse", "convuls", "machuc", "ferid", "comeu", "envenen"]),
    (Categoria.VACINACAO_EXAMES, ["vacin", "vermif", "exame", "hemograma", "raio", "ultrass", "resultado"]),
    (Categoria.FINANCEIRO, ["preco", "valor", "quanto custa", "pagamento", "parcel", "pix", "boleto", "nota fiscal", "orcamento"]),
    (Categoria.AGENDAMENTO, ["agendar", "marcar", "remarcar", "cancelar", "horario", "consulta", "banho", "tosa"]),
]


def classificar_simulado(mensagem: str) -> ClassificacaoIA:
    texto = normalizar(mensagem)
    categoria, confianca = Categoria.DUVIDAS_SERVICOS, 0.5
    for cat, termos in PALAVRAS_CHAVE:
        if any(t in texto for t in termos):
            categoria, confianca = cat, 0.75
            break

    urgencia = Urgencia.ALTA if categoria == Categoria.SINTOMAS_URGENCIA else Urgencia.BAIXA
    if contem_termo_emergencia(mensagem):
        urgencia = Urgencia.EMERGENCIA

    return ClassificacaoIA(
        categoria=categoria,
        urgencia=urgencia,
        confianca=confianca,
        resumo=mensagem[:120],
        nome_tutor=None,
        nome_pet=None,
        especie=None,
        sintomas=[],
        acao_sugerida="Classificação simulada: revisar a mensagem antes de responder.",
        resposta_sugerida="Recebemos sua mensagem e o setor responsável vai te responder em breve.",
    )
