"""No dermatologista: avalia quadro cutaneo, consulta CID-10 e sugere conduta."""

from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.services.llm import modelo
from src.state import CidSugerido, State
from src.tools.cid10 import buscar_cid10

PROMPT_DERMATOLOGISTA = """Voce e um medico dermatologista analisando um prontuario
com queixa ou achado predominantemente de pele ou anexos.

1. Separe todos os sintomas e sinais clinicos descritos no prontuario.
2. Para cada um, chame a ferramenta buscar_cid10 (um sintoma por chamada).
3. Para cada sintoma, escolha a categoria do CID-10 mais adequada entre as que a
   ferramenta devolveu.
4. Elabore uma avaliacao dermatologica: hipoteses (ex.: dermatite, urticaria,
   infeccao cutanea, queimadura), gravidade e risco com base nos achados.
5. Sugira uma conduta inicial (cuidados locais, exames, tratamento, encaminhamento).

Use somente codigos devolvidos pela ferramenta: nunca invente um codigo. Se nenhuma
categoria devolvida servir para um sintoma, nao sugira CID para ele."""


class ResultadoDermatologista(BaseModel):
    """Resultado do agente dermatologista."""

    sintomas: list[str] = Field(description="Sintomas e sinais clinicos separados do prontuario")
    cids_sugeridos: list[CidSugerido] = Field(
        description="Categoria do CID-10 sugerida para cada sintoma"
    )
    avaliacao_dermatologica: str = Field(description="Parecer clinico dermatologico")
    conduta_dermatologica: str = Field(description="Conduta ou proximos passos sugeridos")


def dermatologista(state: State) -> dict:
    """Roda o agente dermatologista com RAG e devolve so os campos que altera no state."""
    agente = create_react_agent(
        modelo(),
        [buscar_cid10],
        prompt=PROMPT_DERMATOLOGISTA,
        response_format=ResultadoDermatologista,
    )
    saida = agente.invoke({"messages": [("human", state.prontuario)]})
    resultado: ResultadoDermatologista = saida["structured_response"]
    return {
        "sintomas": resultado.sintomas,
        "cids_sugeridos": resultado.cids_sugeridos,
        "avaliacao_dermatologica": resultado.avaliacao_dermatologica,
        "conduta_dermatologica": resultado.conduta_dermatologica,
    }
