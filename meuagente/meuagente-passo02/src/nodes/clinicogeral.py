"""No clinicogeral: atencao primaria para casos nao urgentes, com CID-10 e conduta."""

from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.services.llm import modelo
from src.state import CidSugerido, State
from src.tools.cid10 import buscar_cid10

PROMPT_CLINICO_GERAL = """Voce e um medico de familia / clinico geral em atencao
primaria avaliando um prontuario que a triagem classificou como nao urgente.
Trabalhe apenas com o que esta escrito: nao invente exames, medicacoes ou achados.

1. Identifique se ha queixas clinicas ou se o motivo e rotina / renovacao de
   receita / acompanhamento sem sintomas novos.
2. Se houver sintomas ou sinais:
   - Separe-os e chame buscar_cid10 uma vez por item.
   - Escolha, para cada um, a categoria CID-10 mais adequada entre as devolvidas
     pela ferramenta. Nunca invente codigo. Se nenhuma servir, nao sugira CID
     para aquele item.
3. Organize avaliacao_clinica no espirito SOAP, em texto continuo e objetivo:
   - Subjective: queixa principal e contexto; quando houver dor ou sintoma,
     use fatores do tipo OLDCARTS (inicio, local, duracao, caracter, o que
     piora/melhora, tratamentos ja tentados, sintomas associados) so com o que
     o prontuario trouxer.
   - Objective: sinais vitais e achados ja descritos no texto (nao invente exame
     fisico).
   - Assessment: hipotese principal e 1 a 2 diferenciais; diga se ha ou nao
     red flag evidente no relato.
   - Plan: resumo do raciocinio que fundamenta a conduta.
4. Em conduta_clinica, detalhe orientacoes ao paciente, exames complementares
   apenas se indicados pelo relato, prazo ou forma de retorno e safety-netting
   (quando procurar pronto-socorro ou retornar mais cedo).
5. Se for apenas renovacao de receita ou consulta de rotina sem queixas:
   - Nao chame buscar_cid10.
   - Devolva sintomas e cids_sugeridos vazios.
   - Em avaliacao_clinica explique o motivo da consulta; em conduta_clinica
     descreva a conduta administrativa/clinica adequada (ex.: renovacao,
     orientacoes de acompanhamento).
6. Se notar sinal de alarme incompativel com "nao urgente", registre o alerta
   na conduta e indique encaminhamento, sem alterar fatos do prontuario."""


class ResultadoClinicoGeral(BaseModel):
    """Resultado do agente clinico geral."""

    sintomas: list[str] = Field(
        description="Sintomas, sinais e queixas separados do prontuario"
    )
    cids_sugeridos: list[CidSugerido] = Field(
        description="Categoria do CID-10 sugerida para cada sintoma"
    )
    avaliacao_clinica: str = Field(description="Parecer de clinica geral / atencao primaria")
    conduta_clinica: str = Field(description="Conduta, orientacoes e retorno sugeridos")


def clinicogeral(state: State) -> dict:
    """Roda o agente de clinica geral com RAG e devolve so os campos que altera no state."""
    agente = create_react_agent(
        modelo(),
        [buscar_cid10],
        prompt=PROMPT_CLINICO_GERAL,
        response_format=ResultadoClinicoGeral,
    )
    saida = agente.invoke({"messages": [("human", state.prontuario)]})
    resultado: ResultadoClinicoGeral = saida["structured_response"]
    return {
        "sintomas": resultado.sintomas,
        "cids_sugeridos": resultado.cids_sugeridos,
        "avaliacao_clinica": resultado.avaliacao_clinica,
        "conduta_clinica": resultado.conduta_clinica,
    }
