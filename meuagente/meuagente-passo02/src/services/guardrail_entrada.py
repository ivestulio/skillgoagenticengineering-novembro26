"""Guardrail de entrada: mascara PII/segredos e bloqueia injecao de prompt (sem LLM)."""

from src.services.guardrail_padroes import (
    PADROES_INJECAO,
    mascarar_segredos_e_pii,
    normalizar,
)
from src.state import AchadoGuardrail, ResultadoGuardrail

TAMANHO_MAXIMO = 20_000


def verificar_entrada(prontuario: str) -> tuple[str, ResultadoGuardrail]:
    """Devolve o prontuario sanitizado e o resultado da verificacao de entrada."""
    if not prontuario or not prontuario.strip():
        return prontuario, ResultadoGuardrail(
            bloqueado=True,
            motivo="Prontuario vazio",
            achados=[AchadoGuardrail(tipo="tamanho", regra="vazio", quantidade=1)],
        )
    if len(prontuario) > TAMANHO_MAXIMO:
        return "", ResultadoGuardrail(
            bloqueado=True,
            motivo=f"Prontuario com mais de {TAMANHO_MAXIMO} caracteres",
            achados=[AchadoGuardrail(tipo="tamanho", regra="tamanho_maximo", quantidade=1)],
        )

    sanitizado, contagem = mascarar_segredos_e_pii(prontuario)

    normalizado = normalizar(prontuario)
    for regra, padrao in PADROES_INJECAO:
        n = len(padrao.findall(normalizado))
        if n:
            contagem[("injecao", regra)] += n

    achados = [
        AchadoGuardrail(tipo=tipo, regra=regra, quantidade=n)
        for (tipo, regra), n in contagem.items()
    ]
    injecoes = sorted(a.regra for a in achados if a.tipo == "injecao")
    if injecoes:
        return "", ResultadoGuardrail(
            bloqueado=True,
            motivo="Possivel injecao de prompt: " + ", ".join(injecoes),
            achados=achados,
        )
    return sanitizado, ResultadoGuardrail(bloqueado=False, motivo=None, achados=achados)
