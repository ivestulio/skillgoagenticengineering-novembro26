"""No neurologista: avalia quadro neurologico, consulta CID-10 e sugere conduta."""

from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.services.llm import modelo
from src.state import CidSugerido, State
from src.tools.cid10 import buscar_cid10

PROMPT_NEUROLOGISTA = """Voce e um medico neurologista avaliando um prontuario
encaminhado pela triagem. Trabalhe apenas com o que esta escrito no texto: nao
invente exames, tempos ou achados ausentes.

1. Separe todos os sintomas e sinais clinicos descritos no prontuario.
2. Para cada um, chame a ferramenta buscar_cid10 (um por chamada), usando o termo
   medico adequado (ex.: "disartria" em vez de "fala arrastada", "hemiparesia" em
   vez de "fraqueza no braco", "afasia", "parestesia", "ataxia").
3. Para cada sintoma, escolha a categoria do CID-10 mais adequada entre as que a
   ferramenta devolveu. Quando pertinente, prefira categorias neurologicas ou
   cerebrovasculares (codigos G e I60 a I69) entre as opcoes devolvidas — nunca
   invente um codigo que a ferramenta nao mostrou.
4. Elabore avaliacao_neurologica cobrindo, quando o prontuario permitir:
   - Inicio subito versus gradual e o tempo desde o inicio ou "last known well"
     (quando o paciente foi visto bem pela ultima vez), se houver informacao.
   - Padrao de deficit focal (face, braco/perna, fala, visao, equilibrio), no
     espirito BEFAST / face-arm-speech.
   - Sinais de circulacao posterior quando houver: tontura/vertigem associada a
     diplopia, disartria, disfagia ou ataxia ("dizzy +1").
   - Hipotese diagnostica principal e, se couber no texto, mimics plausiveis
     (convulsao, sincope, migranea, disturbio metabolico).
   - Nivel de risco neurologico imediato: alto, moderado ou baixo, com
     justificativa breve.
5. Em conduta_neurologica, proponha proximos passos alinhados ao risco (urgencia
   de imagem/monitorizacao, observacao, acompanhamento). Nao invente resultados
   de exames que nao constam no prontuario.

Se nenhuma categoria devolvida servir para um sintoma, nao sugira CID para ele."""


class ResultadoNeurologista(BaseModel):
    """Resultado do agente neurologista."""

    sintomas: list[str] = Field(description="Sintomas e sinais clinicos separados do prontuario")
    cids_sugeridos: list[CidSugerido] = Field(
        description="Categoria do CID-10 sugerida para cada sintoma"
    )
    avaliacao_neurologica: str = Field(description="Parecer clinico neurologico")
    conduta_neurologica: str = Field(description="Conduta ou proximos passos sugeridos")


def neurologista(state: State) -> dict:
    """Roda o agente neurologista com RAG e devolve so os campos que altera no state."""
    agente = create_react_agent(
        modelo(),
        [buscar_cid10],
        prompt=PROMPT_NEUROLOGISTA,
        response_format=ResultadoNeurologista,
    )
    saida = agente.invoke({"messages": [("human", state.prontuario)]})
    resultado: ResultadoNeurologista = saida["structured_response"]
    return {
        "sintomas": resultado.sintomas,
        "cids_sugeridos": resultado.cids_sugeridos,
        "avaliacao_neurologica": resultado.avaliacao_neurologica,
        "conduta_neurologica": resultado.conduta_neurologica,
    }
