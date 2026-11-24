"""No cardiologista: avalia quadro cardiaco, consulta CID-10 e sugere conduta."""

from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.services.llm import modelo
from src.state import CidSugerido, State
from src.tools.cid10 import buscar_cid10

PROMPT_CARDIOLOGISTA = """Voce e um medico cardiologista analisando um prontuario
com queixa ou achado predominantemente cardiaco.

1. Separe todos os sintomas e sinais clinicos descritos no prontuario.
2. Para cada um, chame a ferramenta buscar_cid10 (um sintoma por chamada).
3. Para cada sintoma, escolha a categoria do CID-10 mais adequada entre as que a
   ferramenta devolveu.
4. Elabore uma avaliacao cardiologica: hipoteses (ex.: SCA, arritmia, insuficiencia
   cardiaca), gravidade e risco cardiovascular com base nos achados.
5. Sugira uma conduta inicial (exames, monitorizacao, encaminhamento).

Use somente codigos devolvidos pela ferramenta: nunca invente um codigo. Se nenhuma
categoria devolvida servir para um sintoma, nao sugira CID para ele."""


class ResultadoCardiologista(BaseModel):
    """Resultado do agente cardiologista."""

    sintomas: list[str] = Field(description="Sintomas e sinais clinicos separados do prontuario")
    cids_sugeridos: list[CidSugerido] = Field(
        description="Categoria do CID-10 sugerida para cada sintoma"
    )
    avaliacao_cardiologica: str = Field(description="Parecer clinico cardiologico")
    conduta_sugerida: str = Field(description="Conduta ou proximos passos sugeridos")


def cardiologista(state: State) -> dict:
    """Roda o agente cardiologista com RAG e devolve so os campos que altera no state."""
    agente = create_react_agent(
        modelo(),
        [buscar_cid10],
        prompt=PROMPT_CARDIOLOGISTA,
        response_format=ResultadoCardiologista,
    )
    saida = agente.invoke({"messages": [("human", state.prontuario)]})
    resultado: ResultadoCardiologista = saida["structured_response"]
    return {
        "sintomas": resultado.sintomas,
        "cids_sugeridos": resultado.cids_sugeridos,
        "avaliacao_cardiologica": resultado.avaliacao_cardiologica,
        "conduta_sugerida": resultado.conduta_sugerida,
    }
