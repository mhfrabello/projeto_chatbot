# AI Language Tutor

Aplicação simples em Streamlit para praticar conversação com IA local usando voz, transcrição automática e resposta em áudio.

## O que o projeto faz

- recebe texto ou gravação de voz;
- transcreve a fala com Whisper;
- envia o contexto ao modelo do Ollama, mantendo o histórico da conversa;
- responde naturalmente, no idioma que o usuário usar (livre, sem seletor de idioma/modo);
- gera áudio da resposta com Edge TTS, com 3 vozes à escolha.

## Estrutura do projeto

- app.py: versão final e completa da aplicação;
- legacy/: versões antigas e arquivos de referência;
- pyproject.toml: dependências e metadados do projeto;
- uv.lock: lockfile usado pelo uv;

## Requisitos

- Python 3.10+
- Ollama instalado e em execução
- Modelo do Ollama disponível: qwen2.5:3b
- Microfone para gravação de voz

## Instalação

1. Instale as dependências com uv:

   uv sync

2. Rode a aplicação com uv:

   uv run streamlit run app.py

Alternativa com pip puro a partir do pyproject:

pip install -e .

## Preparando o Ollama

Antes de abrir a aplicação, baixe o modelo necessário:

ollama pull qwen2.5:3b

E confirme que o serviço está rodando:

ollama list

## Executando a aplicação

Com uv:

uv run streamlit run app.py

Ou, se estiver em um ambiente já ativado com as dependências instaladas:

streamlit run app.py

## Observações importantes

- A aplicação depende do Ollama local para o modelo de linguagem.
- A transcrição usa faster-whisper e trabalha melhor em máquinas com CPU razoável.
- O áudio da resposta é gerado por Edge TTS e pode demorar um pouco conforme o texto.
- O app não tem seletor de idioma nem "modo de conversa": a IA responde livremente no idioma que você usar, misturando português e inglês naturalmente se for o caso.
- O projeto foi reorganizado com a versão final em app.py e arquivos anteriores em legacy/ para manter a estrutura mais limpa.

## Solução de problemas comuns

### Modelo não encontrado

Se a aplicação mostrar que o modelo não foi encontrado, rode:

ollama pull qwen2.5:3b

### Ollama não está funcionando

Verifique se o Ollama está iniciado localmente e se o daemon está ativo.

### Erro ao gerar áudio

O TTS pode falhar dependendo da rede ou do ambiente. A aplicação mostra aviso, mas a conversa continua em texto.

## Licença

Projeto pessoal para estudo e aprendizagem de IA, Streamlit, voz e processamento de linguagem.
