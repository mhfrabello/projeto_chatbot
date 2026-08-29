# config/settings.py
"""
Configurações do app, lidas do arquivo .env (veja .env.example).
"""
from dotenv import load_dotenv
import os

load_dotenv()

# --- Azure OpenAI ---
AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://<seu-recurso>.openai.azure.com"
)
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "SUA_CHAVE_AQUI")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# Nome do "deployment" do modelo de chat no Azure (não é o nome do modelo em si,
# é o nome que você deu ao deployment no Azure AI Foundry / Azure OpenAI Studio)
AZURE_CHAT_DEPLOYMENT = os.getenv("AZURE_CHAT_DEPLOYMENT", "gpt-5")
AZURE_CHAT_TEMPERATURE = float(os.getenv("AZURE_CHAT_TEMPERATURE", "0.3"))

# Nome do deployment do modelo de embedding no Azure
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

# --- RAG ---
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "knowledge")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
TOP_K = int(os.getenv("TOP_K", "4"))

# --- App ---
APP_TITLE = os.getenv("APP_TITLE", "Assistente de Chamados")
