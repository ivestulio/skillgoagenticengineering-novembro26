"""No agente_pediatria: parecer pediatrico com apoio do RAG sobre o CID-10."""

from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.services.llm import modelo
from src.state import CidSugerido, ParecerPediatrico, State
from src.tools.cid10 import buscar_cid10

PROMPT_PEDIATRA = """Voce e um medico pediatra avaliando o prontuario de uma
crianca ou adolescente encaminhado pela triagem.

1. Identifique a idade e, se houver, o peso do paciente: toda a avaliacao depende
   da faixa etaria (recem-nascido, lactente, pre-escolar, escolar ou adolescente).
2. Separe todos os sintomas e sinais clinicos descritos no prontuario, com atencao
   a febre, sinais de desidratacao, desconforto respiratorio, alteracoes de
   alimentacao ou diurese, irritabilidade ou sonolencia, lesoes de pele e crises
   convulsivas.
3. Para cada um, chame a ferramenta buscar_cid10 (um sintoma por chamada).
4. Para cada sintoma, escolha a categoria do CID-10 mais adequada entre as que a
   ferramenta devolveu, considerando a idade do paciente. Para recem-nascidos,
   priorize afeccoes do periodo perinatal (codigos P) quando forem pertinentes.
5. Emita um parecer pediatrico: hipotese diagnostica principal, nivel de risco
   pediatrico imediato (alto, moderado ou baixo) e condutas e exames iniciais.
   Considere a classificacao de urgencia da triagem ao definir o risco. Sinais de
   alerta indicam risco alto: febre em menor de 3 meses, letargia ou dificuldade de
   despertar, desconforto respiratorio importante, desidratacao grave, convulsao,
   recusa alimentar total ou petequias com febre.
6. Ao sugerir medicamentos, indique a dose por peso (mg/kg). Se o peso nao constar
   no prontuario, inclua a pesagem como conduta em vez de supor um valor.

Use somente codigos devolvidos pela ferramenta: nunca invente um codigo. Se nenhuma
categoria devolvida servir para um sintoma, nao sugira CID para ele."""


class ResultadoPediatra(BaseModel):
    """Resultado do agente pediatra."""

    sintomas: list[str] = Field(description="Sintomas e sinais clinicos separados do prontuario")
    cids_sugeridos: list[CidSugerido] = Field(description="Categoria do CID-10 sugerida para cada sintoma")
    # Sem Field(description=...): em streaming a API exige schema estrito, e la um campo
    # que aponta para outro modelo ($ref) nao pode ter descricao propria. A descricao
    # vem da docstring de ParecerPediatrico.
    parecer: ParecerPediatrico


def agente_pediatria(state: State) -> dict:
    """Roda o agente com a ferramenta de RAG e devolve so os campos que altera no state."""
    agente = create_react_agent(
        modelo(),
        [buscar_cid10],
        prompt=PROMPT_PEDIATRA,
        response_format=ResultadoPediatra,
    )
    entrada = (
        f"Triagem: {state.urgencia} - {state.justificativa}\n\n"
        f"Prontuario:\n{state.prontuario}"
    )
    saida = agente.invoke({"messages": [("human", entrada)]})
    resultado: ResultadoPediatra = saida["structured_response"]
    return {
        "sintomas": resultado.sintomas,
        "cids_sugeridos": resultado.cids_sugeridos,
        "parecer_pediatrico": resultado.parecer,
    }
