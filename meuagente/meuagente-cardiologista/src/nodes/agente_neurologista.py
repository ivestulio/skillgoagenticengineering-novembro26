"""No agente_neurologista: parecer neurologico com apoio do RAG sobre o CID-10."""

from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.services.llm import modelo
from src.state import CidSugerido, ParecerNeurologico, State
from src.tools.cid10 import buscar_cid10

PROMPT_NEUROLOGISTA = """Voce e um medico neurologista avaliando um prontuario
encaminhado pela triagem.

1. Separe todos os sintomas e sinais clinicos descritos no prontuario, com atencao
   a deficits focais (fraqueza, perda de sensibilidade, alteracao de fala ou visao),
   cefaleia, crises convulsivas, alteracao do nivel de consciencia, tontura e
   alteracoes de marcha ou coordenacao. Registre o horario de inicio quando houver.
2. Para cada um, chame a ferramenta buscar_cid10 (um sintoma por chamada).
3. Para cada sintoma, escolha a categoria do CID-10 mais adequada entre as que a
   ferramenta devolveu, priorizando doencas do sistema nervoso (codigos G) e doencas
   cerebrovasculares (codigos I60 a I69) quando forem pertinentes.
4. Emita um parecer neurologico: hipotese diagnostica principal, nivel de risco
   neurologico imediato (alto, moderado ou baixo) e condutas e exames iniciais.
   Considere a classificacao de urgencia da triagem ao definir o risco. Suspeita de
   AVC dentro da janela terapeutica, estado de mal epileptico, rebaixamento do nivel
   de consciencia ou cefaleia subita e intensa indicam risco alto.

Use somente codigos devolvidos pela ferramenta: nunca invente um codigo. Se nenhuma
categoria devolvida servir para um sintoma, nao sugira CID para ele."""


class ResultadoNeurologista(BaseModel):
    """Resultado do agente neurologista."""

    sintomas: list[str] = Field(description="Sintomas e sinais clinicos separados do prontuario")
    cids_sugeridos: list[CidSugerido] = Field(description="Categoria do CID-10 sugerida para cada sintoma")
    # Sem Field(description=...): em streaming a API exige schema estrito, e la um campo
    # que aponta para outro modelo ($ref) nao pode ter descricao propria. A descricao
    # vem da docstring de ParecerNeurologico.
    parecer: ParecerNeurologico


def agente_neurologista(state: State) -> dict:
    """Roda o agente com a ferramenta de RAG e devolve so os campos que altera no state."""
    agente = create_react_agent(
        modelo(),
        [buscar_cid10],
        prompt=PROMPT_NEUROLOGISTA,
        response_format=ResultadoNeurologista,
    )
    entrada = (
        f"Triagem: {state.urgencia} - {state.justificativa}\n\n"
        f"Prontuario:\n{state.prontuario}"
    )
    saida = agente.invoke({"messages": [("human", entrada)]})
    resultado: ResultadoNeurologista = saida["structured_response"]
    return {
        "sintomas": resultado.sintomas,
        "cids_sugeridos": resultado.cids_sugeridos,
        "parecer_neurologico": resultado.parecer,
    }
