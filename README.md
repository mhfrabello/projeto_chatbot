# Assistente de TI (RAG + Azure GPT-5)

Chatbot interno em Streamlit que orienta colaboradores sobre problemas de TI:
indica um passo a passo de autoatendimento quando existe, ou o chamado
correto a abrir (categoria, link e informações necessárias) quando não.

> **As URLs de chamados usadas neste projeto (`https://chamados.paschoalotto.com.br/...`)
> são fictícias, para fins de demonstração.** Substitua pelas URLs reais do
> seu portal de chamados antes de usar em produção.

## Objetivo

Dado um relato livre do colaborador ("meu computador não liga", "esqueci
minha senha"), o assistente:

1. Diz se existe uma solução que o próprio colaborador pode executar.
2. Se não existir (ou se o autoatendimento não resolver), indica qual
   chamado abrir.
3. Informa a categoria/subcategoria correta.
4. Fornece o link direto para abertura do chamado.
5. Lista as informações que o colaborador deve ter em mãos.
6. Quando há ambiguidade entre duas situações parecidas, faz uma pergunta
   objetiva antes de responder, em vez de arriscar um chamado errado.

## Arquitetura

```
knowledge/base_conhecimento.md
        │  (um arquivo único, dividido em blocos "### ENTRADA: ...")
        ▼
document_service   →  interpreta cada bloco como uma KnowledgeEntry,
                       extraindo categoria, chamado, URL e palavras-chave
        │
        ▼
chunk_service       →  cada ENTRADA vira exatamente UM chunk — nunca é
                       cortada por tamanho, então a URL nunca se perde
        │
        ▼
embedding_service (Azure) → vector_store (FAISS)
        │
        ▼
rag_service         →  busca as entradas mais relevantes, detecta baixa
                       similaridade, monta o prompt com contexto estruturado
        │
        ▼
llm_service (GPT-5 Azure) → resposta final
        │
        ▼
app.py + components/ →  interface Streamlit
```

### Por que "uma entrada = um chunk"?

Um chunker tradicional corta texto a cada N caracteres, o que pode partir
uma entrada bem no meio da URL do chamado — o modelo então "perde" o link
e pode inventar um. Aqui, cada situação da base
(`### ENTRADA: Reset de senha`, por exemplo) é tratada como uma unidade
atômica: ela inteira vira um único chunk, com seus metadados (categoria,
chamado, URL, palavras-chave) sempre preservados juntos.

### Detecção de baixa similaridade

Se a pergunta do colaborador não tiver relação com nada na base (distância
vetorial acima de um limiar), o assistente não força uma resposta — ele
avisa que não encontrou um procedimento específico e orienta abrir um
chamado geral de TI, em vez de arriscar um chamado ou link errado.

## Setup

1. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copie `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```

3. Preencha o `.env` com os dados do seu recurso Azure OpenAI:

   | Variável | O que é |
   |---|---|
   | `AZURE_OPENAI_ENDPOINT` | Raiz do endpoint, ex: `https://meu-recurso.openai.azure.com` — **sem** `/openai/v1` no final |
   | `AZURE_OPENAI_KEY` | Chave de API (Azure AI Foundry → Keys and Endpoint) |
   | `AZURE_OPENAI_API_VERSION` | Versão da API (ex: `2024-10-21`) |
   | `AZURE_CHAT_DEPLOYMENT` | Nome do **deployment** do GPT-5 (o nome que você deu ao criar, não necessariamente "gpt-5") |
   | `AZURE_EMBEDDING_DEPLOYMENT` | Nome do **deployment** de embedding (ex: `text-embedding-3-small`) — precisa ser um deployment separado do de chat |

   ⚠️ Você precisa de **dois deployments** no Azure AI Foundry: um de chat
   (GPT-5) e um de embedding. Um modelo de chat não gera embeddings — usar
   o nome do deployment de chat em `AZURE_EMBEDDING_DEPLOYMENT` resulta em
   erro 404.

   ⚠️ O GPT-5 (modelo de raciocínio) só aceita o valor padrão de
   `temperature`. Por isso o projeto não envia esse parâmetro nas chamadas
   de chat — enviá-lo causa erro 400.

4. Rode o app:
   ```bash
   streamlit run app.py
   ```

## Estrutura do projeto

```
app.py                          # orquestra a página (Streamlit)
config/
  settings.py                    # variáveis de ambiente
components/
  styles.py                      # CSS customizado (visual corporativo)
  chat_ui.py                     # header + tela inicial com exemplos
  sidebar.py                     # indicadores da base + ações
services/
  azure_client.py                # cliente Azure OpenAI (chat + embedding)
  llm_service.py                 # chamada ao GPT-5, com tratamento de erro
  embedding_service.py           # geração de embeddings, com tratamento de erro
  document_service.py            # parser da base estruturada (### ENTRADA:)
  chunk_service.py                # monta chunks com metadados (1 entrada = 1 chunk)
  vector_store.py                # índice FAISS + distâncias de similaridade
  knowledge_base.py              # monta a base completa (arquivo → índice)
  rag_service.py                 # busca contexto + prompt + chama o LLM
knowledge/
  base_conhecimento.md           # toda a base de conhecimento, em um arquivo único
```

## Como editar a base de conhecimento

Toda a base vive em `knowledge/base_conhecimento.md`, organizada assim:

```markdown
## CATEGORIA: Nome da categoria

### ENTRADA: Nome curto do problema
Palavras-chave: termo 1, termo 2, termo 3

Autoatendimento:
1. Passo 1
2. Passo 2

Quando abrir chamado: condição que leva à abertura de chamado

Chamado: Nome do chamado
Categoria: Categoria > Subcategoria
URL: https://chamados.paschoalotto.com.br/abrir/slug-do-chamado
Informações obrigatórias: item 1, item 2
Prioridade: Normal

---
```

### Como adicionar um novo chamado/situação

1. Abra `knowledge/base_conhecimento.md`.
2. Copie o modelo que está comentado no final do arquivo.
3. Cole dentro da seção `## CATEGORIA:` que fizer sentido (ou crie uma nova
   seção de categoria, se necessário).
4. Preencha os campos — o campo `URL` é o que vira o link clicável na
   resposta do assistente, então confira que está correto.
5. Separe do próximo bloco com uma linha `---`.
6. Salve o arquivo e clique em **"🔄 Recarregar base de conhecimento"** na
   barra lateral do app (ou reinicie o `streamlit run`).

### Como adicionar novas URLs de chamado

Não há uma lista de URLs separada — cada `### ENTRADA` carrega sua própria
URL no campo `URL:`. Para trocar o domínio fictício pelo real do seu
portal, use busca e substituição em todo o arquivo
(`https://chamados.paschoalotto.com.br` → seu domínio real).

## Como o RAG funciona, na prática

Quando o colaborador envia uma pergunta:

1. A pergunta vira um vetor de embedding (Azure).
2. O FAISS busca as `TOP_K` entradas mais próximas na base (padrão: 4).
3. Se a distância da entrada mais próxima for alta demais (baixa
   similaridade), o assistente é instruído a admitir que não encontrou
   nada específico, em vez de improvisar.
4. As entradas encontradas (com seus metadados completos) são inseridas no
   prompt de sistema como contexto.
5. O GPT-5 responde seguindo regras estritas: nunca inventar chamado,
   categoria, URL ou procedimento fora do contexto fornecido; sempre
   apresentar o link em Markdown clicável; fazer no máximo uma pergunta de
   esclarecimento quando houver ambiguidade.

O prompt de sistema completo está em `services/rag_service.py`, na
constante `SYSTEM_PROMPT` — ajuste ali o tom, as regras ou o formato de
resposta.

## Como trocar o deployment Azure

Edite as variáveis no `.env`:
- `AZURE_CHAT_DEPLOYMENT` para trocar o modelo de chat.
- `AZURE_EMBEDDING_DEPLOYMENT` para trocar o modelo de embedding.

Se trocar o modelo de embedding, é necessário recarregar a base
(botão na barra lateral ou reiniciar o app), pois embeddings de modelos
diferentes não são compatíveis entre si no mesmo índice.

## Tratamento de erros

O app nunca expõe um traceback bruto ao colaborador. Cenários tratados:

- **Azure indisponível / timeout** → mensagem amigável, sugestão de tentar
  novamente.
- **Erro de autenticação** (chave errada) → mensagem indicando revisar o
  `.env` (mostrada apenas no card de erro da base, não em produção
  exposta ao colaborador final — ideal para ambiente de desenvolvimento).
- **Deployment de embedding errado** → mensagem específica orientando
  conferir `AZURE_EMBEDDING_DEPLOYMENT`.
- **Base de conhecimento vazia** → aviso orientando adicionar o arquivo.
- **Resposta vazia do modelo** → tratada como erro, com mensagem amigável.
- **Pergunta sem contexto relevante na base** → o modelo é instruído a
  admitir isso e orientar chamado geral, sem inventar.

## Exemplos de perguntas

- "Quero instalar um programa, o que eu faço?"
- "Esqueci minha senha, como faço para resetar?"
- "Meu computador não liga"
- "O Teams não abre"
- "Preciso de acesso a um sistema novo"
- "Minha internet está lenta"
- "A impressora não está imprimindo"

## Segurança

- `.env` está no `.gitignore` — nunca é versionado.
- A chave de API, o prompt de sistema e detalhes técnicos do RAG (chunks,
  embeddings, FAISS) nunca são expostos ao colaborador nas respostas —
  o prompt de sistema instrui explicitamente o modelo a não mencionar
  esses termos.
