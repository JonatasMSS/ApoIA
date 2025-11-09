from fastapi import FastAPI, UploadFile, File, Form
from pydub import AudioSegment
from openai import OpenAI
from datetime import datetime
import os
from libs.OpenAI import client

from dotenv import load_dotenv
load_dotenv()

# Cliente OpenAI (usa OPENAI_API_KEY do ambiente)
# client = OpenAI(api_key="sk-1vYexqLQgVrnQJIo-unIv7sjSYikU4rBeiNl_ao6zcT3BlbkFJuIcQZfH1ewSiEfEt3gklVIfAaaGhWH3tU8hsBoa20A")

app = FastAPI()

# Garante pastas
os.makedirs("storage/audios", exist_ok=True)
os.makedirs("storage/transcricoes", exist_ok=True)
os.makedirs("storage/respostas", exist_ok=True)

@app.post("/processar_audio/")
async def processar_audio(numero: str = Form(...), audio: UploadFile = File(...)):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    input_ogg = f"storage/audios/input_{timestamp}.ogg"
    input_wav = f"storage/audios/input_{timestamp}.wav"
    resposta_wav = f"storage/respostas/resposta_{timestamp}.wav"
    texto_path = f"storage/transcricoes/{timestamp}.txt"

    # Salva áudio recebido
    with open(input_ogg, "wb") as f:
        f.write(await audio.read())

    # Converte OGG → WAV
    AudioSegment.from_file(input_ogg).export(input_wav, format="wav")

    # 1) Transcrição
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=open(input_wav, "rb")
    )
    texto_usuario = transcription.text

    with open(texto_path, "w", encoding="utf-8") as f:
        f.write(texto_usuario)

    # 2) Resposta IA
    resposta_texto = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": texto_usuario}]
    ).choices[0].message.content

    # 3) Sintetiza voz
    sintetizado = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=resposta_texto
    )

    with open(resposta_wav, "wb") as f:
        f.write(sintetizado.read())

    return {
        "status": "ok",
        "usuario": numero,
        "texto_usuario": texto_usuario,
        "resposta_texto": resposta_texto,
        "resposta_audio": resposta_wav
    }

@app.post("/falar/")
async def falar(texto: str = Form(...)):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    resposta_wav = f"storage/respostas/teste_{timestamp}.wav"

    # Gera áudio pela TTS da OpenAI
    sintetizado = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=texto
    )

    with open(resposta_wav, "wb") as f:
        f.write(sintetizado.read())

    return {
        "status": "ok",
        "entrada_texto": texto,
        "arquivo_audio": resposta_wav
    }
