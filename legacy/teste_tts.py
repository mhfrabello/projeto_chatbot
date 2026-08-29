import asyncio
import os
import edge_tts
import pygame

TEXTO_EXEMPLO = "Hello! I am your local AI conversational partner. How can I help you practice your English today?"
ARQUIVO_AUDIO = "resposta.mp3"

async def gerar_audio(texto, arquivo_saida):
    voz = "en-US-AriaNeural" 
    comunicador = edge_tts.Communicate(texto, voz)
    await comunicador.save(arquivo_saida)

def tocar_audio(arquivo):
    pygame.mixer.init()
    pygame.mixer.music.load(arquivo)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
        
    pygame.mixer.quit()

if __name__ == "__main__":
    print("Gerando áudio com Edge-TTS...")
    asyncio.run(gerar_audio(TEXTO_EXEMPLO, ARQUIVO_AUDIO))
    
    print("Reproduzindo áudio...")
    tocar_audio(ARQUIVO_AUDIO)
    print("Reprodução concluída!")