# susia

Sistema multiagente, construído com [LangGraph](https://langchain-ai.github.io/langgraph/), que recebe um prontuário médico e faz a triagem do atendimento.

> Projeto didático. Use apenas prontuários fictícios: ele não substitui avaliação clínica e não deve ser usado com dados reais de pacientes.

## Como funciona

O objetivo final é encaminhar cada prontuário para o agente certo:

- **pediátrico** (menor de 18 anos, urgente ou não) → agente pediatra
- **neurológico** (urgente ou não) → agente neurologista
- **cardiológico** (urgente ou não) → agente cardiologista
- **urgente** → agente de emergência
- **não urgente** → agente clínico geral

### Etapa atual

```mermaid
graph LR
    START([START]) --> atendimento
    atendimento -. cardiologico .-> agente_cardiologista
    atendimento -. neurologico .-> agente_neurologista
    atendimento -. pediatrico .-> agente_pediatria
    atendimento -. urgente .-> agente_urgencia
    atendimento -. nao_urgente .-> FIM([END])
    agente_cardiologista --> FIM
    agente_neurologista --> FIM
    agente_pediatria --> FIM
    agente_urgencia --> FIM
```

- **`atendimento`**: lê o prontuário e pede ao modelo uma resposta estruturada com `urgencia`, `especialidade` (`pediatria`, `neurologia`, `cardiologia` ou `geral`) e `justificativa`. A especialidade é avaliada nessa ordem, e vale a primeira que se aplicar: paciente com menos de 18 anos é sempre `pediatria`, mesmo com queixa cardíaca ou neurológica. Na dúvida, o prompt orienta a classificar como urgente e, se houver dor torácica, como cardiologia. Desmaio com palpitação, dor no peito ou esforço vai para cardiologia; com convulsão, confusão prolongada ou déficit de um lado do corpo, para neurologia. O prompt também considera apresentações cardíacas atípicas (idosos, diabéticos e mulheres) e manda ignorar instruções escritas dentro do prontuário.
- **`rotear_triagem`** (aresta condicional, sem LLM): casos de `cardiologia`, `neurologia` e `pediatria` vão para o agente da especialidade, mesmo quando urgentes; os demais vão para `agente_urgencia`, exceto os `nao_urgente`, que encerram o fluxo. Sem classificação, o caso é tratado como urgente.
- **`agente_urgencia`**: roda para prontuários urgentes sem especialidade definida (`geral`). É um agente com tool calling: separa os sintomas e sinais do prontuário, consulta o CID-10 com a ferramenta `buscar_cid10` (uma chamada por sintoma) e devolve `sintomas` e `cids_sugeridos`. O prompt proíbe sugerir código que a ferramenta não devolveu.
- **`agente_cardiologista`**: roda para os casos cardiológicos. Usa a mesma ferramenta e as mesmas regras do agente de urgência, prioriza categorias cardiovasculares (códigos I) e recebe também o resultado da triagem. Além de `sintomas` e `cids_sugeridos`, devolve um `parecer_cardiologico` com hipótese diagnóstica, risco cardiovascular imediato (`alto`, `moderado` ou `baixo`) e condutas e exames iniciais.
- **`agente_neurologista`**: roda para os casos neurológicos, com a mesma ferramenta e as mesmas regras. Dá atenção a déficits focais, cefaleia, crises convulsivas, nível de consciência e horário de início dos sintomas, e prioriza doenças do sistema nervoso (códigos G) e cerebrovasculares (I60 a I69). Devolve um `parecer_neurologico`; suspeita de AVC na janela terapêutica, estado de mal epiléptico, rebaixamento de consciência ou cefaleia súbita e intensa indicam risco alto.
- **`agente_pediatria`**: roda para pacientes com menos de 18 anos, com a mesma ferramenta e as mesmas regras. Avalia o caso pela faixa etária e pelo peso, prioriza afecções perinatais (códigos P) em recém-nascidos e indica doses de medicamento por peso (mg/kg); sem o peso no prontuário, inclui a pesagem como conduta. Devolve um `parecer_pediatrico`; sinais como febre em menor de 3 meses, letargia, desconforto respiratório importante, desidratação grave, convulsão, recusa alimentar total ou petéquias com febre indicam risco alto.

### RAG sobre o CID-10

A base de conhecimento é o arquivo `CID-10.pdf`, na raiz do projeto: a lista de categorias de 3 caracteres do CID-10 (versão 2008 do Ministério da Saúde), no formato `código + descrição`.

- Cada categoria vira um documento (2.045 no total); não há divisão por tamanho de texto.
- Na primeira busca, os embeddings são gerados e o índice é salvo em `.cache/cid10_index.json` (cerca de 80 MB, fora do git). Essa primeira vez pode levar alguns minutos, conforme o limite de requisições do deployment. Nas seguintes, o índice é só lido do disco. Para refazer o índice, apague esse arquivo.
- A busca é por similaridade semântica, com `InMemoryVectorStore`.

Limitação: o PDF traz só o nome de cada categoria, sem descrição de sintomas por doença. A busca casa o sintoma com nomes de categorias, e funciona melhor para os códigos do capítulo R (sintomas e sinais).

### Próximas etapas

- Nó de clínico geral para os prontuários não urgentes.

## State

Definido em [src/state.py](src/state.py):

| Campo | Origem | Descrição |
|---|---|---|
| `paciente_id` | entrada | ID do paciente |
| `prontuario` | entrada | Texto do prontuário médico |
| `data_atualizacao` | entrada | Data da última atualização do prontuário |
| `urgencia` | atendimento | `"urgente"` ou `"nao_urgente"` |
| `especialidade` | atendimento | `"cardiologia"`, `"neurologia"`, `"pediatria"` ou `"geral"` |
| `justificativa` | atendimento | Motivo da classificação |
| `sintomas` | agente que atendeu o caso | Sintomas e sinais separados do prontuário |
| `cids_sugeridos` | agente que atendeu o caso | Lista de `sintoma`, `codigo` e `descricao` do CID-10 |
| `parecer_cardiologico` | agente_cardiologista | `hipotese_diagnostica`, `risco` (`"alto"`, `"moderado"` ou `"baixo"`) e `condutas` |
| `parecer_neurologico` | agente_neurologista | Mesmos campos, com risco neurológico imediato |
| `parecer_pediatrico` | agente_pediatria | Mesmos campos, com risco pediátrico imediato |

## Estrutura

```
susia/
├── CID-10.pdf            # base de conhecimento do RAG
├── langgraph.json        # registra o grafo para o LangGraph Studio
├── requirements.txt
├── .env.example          # modelo das variáveis de ambiente
└── src/
    ├── state.py          # state compartilhado entre os nós
    ├── graph.py          # montagem do grafo (exporta `grafo`)
    ├── nodes/
    │   ├── atendimento.py      # agente de triagem
    │   ├── agente_urgencia.py       # agente que separa sintomas e consulta o CID-10
    │   ├── agente_cardiologista.py  # agente que consulta o CID-10 e emite parecer cardiológico
    │   ├── agente_neurologista.py   # agente que consulta o CID-10 e emite parecer neurológico
    │   └── agente_pediatria.py      # agente que consulta o CID-10 e emite parecer pediátrico
    ├── edges/
    │   └── roteamento.py       # aresta condicional por especialidade e urgência
    ├── tools/
    │   └── cid10.py            # ferramenta `buscar_cid10`
    └── services/
        ├── llm.py        # clientes do modelo de chat e de embeddings, configurações
        └── cid10.py      # leitura do PDF, índice vetorial e busca
```

`src/services/llm.py` é o único ponto do projeto que conhece o provedor do modelo; os nós só chamam `modelo()`.

## Instalação

Requer Python 3.12 e [uv](https://docs.astral.sh/uv/).

```bash
uv venv --python 3.12
```

```bash
uv pip install -r requirements.txt
```

## Configuração

Copie o modelo e preencha os valores:

```bash
cp .env.example .env
```

Os modelos são acessados pela API v1 do Microsoft Foundry. São usadas quatro variáveis:

| Variável | Valor |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Endpoint v1 do recurso, terminando em `/openai/v1/`. Exemplo: `https://<recurso>.services.ai.azure.com/openai/v1/` |
| `AZURE_OPENAI_API_KEY` | Chave do recurso |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Nome do deployment do modelo de chat no Foundry (nem sempre igual ao nome do modelo) |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Nome do deployment de embeddings. Se omitida, vale `text-embedding-3-small` |

Observações:

- O endpoint não deve incluir `/responses` nem `/chat/completions` no final.
- O cliente usa a Responses API, exigida pelos modelos da família gpt-5/codex.
- As demais variáveis do `.env.example` (`AZURE_OPENAI_API_VERSION`, OpenAI, Gemini, Azure AI Search, MLflow) ainda não são usadas pelo código.

## Como rodar

### Pelo Python

```bash
.venv/bin/python -c "from src.graph import grafo; print(grafo.invoke({'paciente_id': 'PAC-001', 'prontuario': 'Homem, 58 anos. Dor toracica em aperto ha 40 min, sudorese, PA 90x60, SpO2 91%.', 'data_atualizacao': '2026-11-15'}))"
```

A saída é o state final, com `urgencia`, `especialidade` e `justificativa` preenchidos. Se o caso for cardiológico, neurológico ou pediátrico, vêm também `sintomas`, `cids_sugeridos` e o parecer da especialidade (`parecer_cardiologico`, `parecer_neurologico` ou `parecer_pediatrico`); se for urgente e sem especialidade, só `sintomas` e `cids_sugeridos`.

### Pelo LangGraph Studio

```bash
.venv/bin/langgraph dev
```

O comando sobe a API local em `http://127.0.0.1:2024` e abre o Studio no navegador (pede login em uma conta LangSmith). Selecione o grafo `atendimento`, preencha a entrada e clique em **Submit**.

Exemplo de entrada:

```json
{
  "paciente_id": "PAC-004",
  "prontuario": "Mulher, 34 anos. Retorno para renovação de receita de anticoncepcional oral. Sem queixas. PA 110x70 mmHg, FC 72 bpm, afebril.",
  "data_atualizacao": "2026-11-15"
}
```

## Visualizar o grafo

```bash
.venv/bin/python -c "from src.graph import grafo; print(grafo.get_graph().draw_mermaid())"
```

O comando imprime o diagrama em Mermaid, que pode ser colado em qualquer visualizador Mermaid.
