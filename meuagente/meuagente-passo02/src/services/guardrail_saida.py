"""Guardrail de saida: remascara PII/segredos nos textos de resposta (sem LLM)."""

from src.services.guardrail_padroes import mascarar_segredos_e_pii
from src.state import AchadoGuardrail, CidSugerido, ResultadoGuardrail, State

CAMPOS_TEXTO = (
    "justificativa",
    "avaliacao_cardiologica",
    "conduta_sugerida",
    "avaliacao_dermatologica",
    "conduta_dermatologica",
    "avaliacao_neurologica",
    "conduta_neurologica",
    "avaliacao_clinica",
    "conduta_clinica",
)


def sanitizar_state_resposta(state: State) -> dict:
    """Mascara PII/segredos nos campos de saida e devolve o patch do state."""
    contagem_total: dict[tuple[str, str], int] = {}
    patch: dict = {}

    def acumular(contagem) -> None:
        for chave, n in contagem.items():
            contagem_total[chave] = contagem_total.get(chave, 0) + n

    for campo in CAMPOS_TEXTO:
        valor = getattr(state, campo, None)
        if isinstance(valor, str) and valor:
            limpo, contagem = mascarar_segredos_e_pii(valor)
            acumular(contagem)
            if limpo != valor:
                patch[campo] = limpo

    if state.sintomas:
        sintomas_limpos = []
        mudou = False
        for item in state.sintomas:
            limpo, contagem = mascarar_segredos_e_pii(item)
            acumular(contagem)
            sintomas_limpos.append(limpo)
            if limpo != item:
                mudou = True
        if mudou:
            patch["sintomas"] = sintomas_limpos

    if state.cids_sugeridos:
        cids_limpos: list[CidSugerido] = []
        mudou = False
        for cid in state.cids_sugeridos:
            sintoma, c1 = mascarar_segredos_e_pii(cid.sintoma)
            descricao, c2 = mascarar_segredos_e_pii(cid.descricao)
            acumular(c1)
            acumular(c2)
            if sintoma != cid.sintoma or descricao != cid.descricao:
                mudou = True
            cids_limpos.append(
                CidSugerido(sintoma=sintoma, codigo=cid.codigo, descricao=descricao)
            )
        if mudou:
            patch["cids_sugeridos"] = cids_limpos

    achados = [
        AchadoGuardrail(tipo=tipo, regra=regra, quantidade=n)
        for (tipo, regra), n in contagem_total.items()
    ]
    patch["guardrail_saida"] = ResultadoGuardrail(
        bloqueado=False,
        motivo=None,
        achados=achados,
    )
    return patch
