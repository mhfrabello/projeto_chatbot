"""
Teste isolado: grava do microfone automaticamente (para quando você
para de falar) e transcreve com faster-whisper.

Rode com: uv run python teste_stt.py
Fale algo em inglês e aguarde a transcrição aparecer.
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

# --- Configurações de áudio ---
SAMPLE_RATE = 16000  # Whisper espera 16kHz
SILENCE_THRESHOLD = 0.01  # volume abaixo disso é considerado silêncio
SILENCE_DURATION = 1.2  # segundos de silêncio para parar de gravar
MAX_DURATION = 30  # segundos máximos de gravação (segurança)

print("Carregando modelo Whisper (primeira vez pode demorar um pouco)...")
model = WhisperModel("small", device="cpu", compute_type="int8")
# model = WhisperModel("tiny", device="cpu", compute_type="int8")
print("Modelo carregado.\n")


def gravar_com_deteccao_de_silencio():
    """Grava do microfone até detectar silêncio prolongado."""
    print("🎙️  Fale agora... (a gravação para sozinha após você parar de falar)")

    blocos = []
    silencio_acumulado = 0.0
    bloco_duracao = 0.1  # segundos por bloco lido
    bloco_tamanho = int(SAMPLE_RATE * bloco_duracao)
    tempo_total = 0.0
    comecou_a_falar = False

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="float32"
    ) as stream:
        while tempo_total < MAX_DURATION:
            bloco, _ = stream.read(bloco_tamanho)
            volume = np.abs(bloco).mean()
            blocos.append(bloco.copy())
            tempo_total += bloco_duracao

            if volume > SILENCE_THRESHOLD:
                comecou_a_falar = True
                silencio_acumulado = 0.0
            elif comecou_a_falar:
                silencio_acumulado += bloco_duracao
                if silencio_acumulado >= SILENCE_DURATION:
                    break

    print("⏹️  Gravação finalizada. Transcrevendo...")
    audio = np.concatenate(blocos, axis=0).flatten()
    return audio


def transcrever(audio: np.ndarray) -> str:
    segments, info = model.transcribe(
        audio,
        language="en",  # fixo em inglês, já que é pra prática de idioma
        vad_filter=True,
    )
    texto = " ".join(segment.text.strip() for segment in segments)
    return texto


if __name__ == "__main__":
    audio = gravar_com_deteccao_de_silencio()
    texto = transcrever(audio)
    print(f"\n📝 Transcrição: {texto}\n")