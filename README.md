# Assistente de Chamados (RAG + Azure GPT-5)

Chatbot em Streamlit que orienta colaboradores sobre qual chamado abrir
(ou como resolver sozinho, quando existe um passo a passo) — com base numa
base de conhecimento de documentos que você mantém na pasta `knowledge/`.

## Como funciona

```
knowledge/*.md, *.txt, *.pdf
        │
        ▼
document_service  →  chunk_service  →  embedding_service (Azure) → vector_store (FAISS)
                                                                          │
                                                                          ▼
                        rag_service (busca contexto + monta prompt) → llm_service (GPT-5 Azure)
                                                                          │
                                                                          ▼
                                                                    app.py (Streamlit)
```

A base é reprocessada (lida, chunkada, embedada e indexada) toda vez que o
app inicia — não há cache em disco. Isso é intencional, pra manter simples:
edite os arquivos em `knowledge/`, reinicie o app (ou clique em "Recarregar
base de conhecimento" na barra lateral) e pronto.

## Setup

1. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # no Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copie `.env.example` para `.env` e preencha com os dados do seu recurso
   Azure OpenAI:
   ```bash
   cp .env.example .env
   ```
   Você vai precisar de:
   - `AZURE_OPENAI_ENDPOINT` — endpoint do recurso (ex: `https://meu-recurso.openai.azure.com`)
   - `AZURE_OPENAI_KEY` — chave de API (Azure AI Foundry / Azure OpenAI Studio > Keys and Endpoint)
   - `AZURE_CHAT_DEPLOYMENT` — nome do **deployment** do GPT-5 (não é "gpt-5" necessariamente,
     é o nome que você deu ao deployment ao criá-lo)
   - `AZURE_EMBEDDING_DEPLOYMENT` — nome do deployment de um modelo de embedding
     (ex: `text-embedding-3-small`). Você precisa criar esse deployment separadamente
     no Azure, mesmo usando a mesma chave/endpoint do chat.

3. Coloque seus documentos de procedimentos em `knowledge/` (já tem 3 exemplos
   lá: instalação de programas, reset de senha e problema de equipamento —
   edite ou substitua pelos seus).

4. Rode o app:
   ```bash
   streamlit run app.py
   ```

## Estrutura

```
app.py                          # página única de chat (Streamlit)
config/
  settings.py                   # variáveis de ambiente
services/
  azure_client.py                # cliente Azure OpenAI (chat + embedding)
  llm_service.py                 # chamada ao GPT-5
  embedding_service.py           # geração de embeddings
  document_service.py            # leitura de .md/.txt/.pdf da pasta knowledge/
  chunk_service.py               # quebra de texto em chunks (com overlap)
  vector_store.py                # índice FAISS em memória
  knowledge_base.py              # monta a base completa (documentos → índice)
  rag_service.py                 # busca contexto + monta prompt + chama o LLM
knowledge/                      # seus documentos de procedimentos (.md/.txt/.pdf)
```

## Escrevendo bons documentos de conhecimento

Cada arquivo em `knowledge/` deve ser focado num tipo de solicitação. Sugestão
de estrutura (veja os exemplos já incluídos):

```markdown
# Título do problema/solicitação

## Você pode resolver sozinho (se aplicável)
Passo a passo numerado.

## Quando abrir chamado
Categoria do chamado, link, quais informações incluir.
```

Isso ajuda o modelo a responder de forma consistente: "dá pra resolver
sozinho, aqui está o passo a passo" ou "abra o chamado X, aqui está o link".

## Ajustando o comportamento do bot

O prompt de sistema que define o tom e as regras de resposta está em
`services/rag_service.py`, na constante `SYSTEM_PROMPT_TEMPLATE`. Ajuste
ali se quiser mudar o estilo das respostas, adicionar regras, etc.
