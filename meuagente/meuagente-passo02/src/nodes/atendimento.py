"""No de atendimento: faz a triagem do prontuario e escolhe o destino."""

from typing import Literal

from pydantic import BaseModel, Field

from src.services.llm import modelo
from src.state import State

PROMPT_TRIAGEM = """Voce e um profissional de triagem em um servico de saude.
Leia o prontuario e classifique o destino do atendimento:

- "dermatologico": queixa ou achado predominantemente de pele ou anexos.
  Exemplos: rash, prurido, lesoes cutaneas, urticaria, queimadura cutanea,
  infeccao de pele, erupcao, eczema, psoriasis.
- "cardiologico": queixa ou achado predominantemente cardiaco. Exemplos: dor
  toracica, palpitacao, sincope suspeita cardiaca, edema com dispneia sugestiva
  de insuficiencia cardiaca, sinais de sindrome coronariana aguda.
- "neurologico": queixa ou achado predominantemente neurologico, mesmo quando
  urgente. Exemplos: deficit motor ou sensitivo focal, desvio de rima, alteracao
  aguda da fala, suspeita de AVC, crise convulsiva, cefaleia subita e intensa
  ("em trovao"), rebaixamento de consciencia de causa neurologica, vertigem com
  sinais focais (diplopia, disartria, ataxia).
- "urgente": risco imediato a vida ou de agravamento rapido, sem predominancia
  cardiaca, neurologica nem dermatologica. Exemplos: sangramento ativo, trauma
  grave, reacao alergica grave sistemica, dor intensa e subita nao toracica,
  sinais vitais instaveis por causa nao tipicamente cardiologica, neurologica
  nem cutanea.
- "clinicogeral": quadro estavel, queixas leves ou cronicas, rotina, renovacao
  de receita, acompanhamento em atencao primaria — nao urgente.

Prioridade na duvida: cardiologico > neurologico > dermatologico > urgente >
clinicogeral.
Tambem informe se o caso e "urgente" ou "nao_urgente" no nivel de urgencia geral
(especialidades com risco clinico imediato contam como urgente).
Justifique em uma ou duas frases, citando os achados do prontuario."""


class Classificacao(BaseModel):
    """Resultado da triagem."""

    destino: Literal[
        "dermatologico", "cardiologico", "neurologico", "urgente", "clinicogeral"
    ] = Field(description="Destino do atendimento apos a triagem")
    urgencia: Literal["urgente", "nao_urgente"] = Field(
        description="Nivel de urgencia geral"
    )
    justificativa: str = Field(description="Motivo da classificacao")


def atendimento(state: State) -> dict:
    """Classifica o prontuario e devolve so os campos que altera no state."""
    triador = modelo().with_structured_output(Classificacao)
    resultado = triador.invoke(
        [
            ("system", PROMPT_TRIAGEM),
            ("human", state.prontuario),
        ]
    )
    return {
        "destino": resultado.destino,
        "urgencia": resultado.urgencia,
        "justificativa": resultado.justificativa,
    }
