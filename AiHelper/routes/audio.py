from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime
import os
import base64
import io
# from libs.OpenAI import client
from dotenv import load_dotenv

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cria o router (não uma nova instância de FastAPI)
router = APIRouter(prefix="/audio", tags=["Áudio"])

# Garante pastas
os.makedirs("storage/audios", exist_ok=True)
os.makedirs("storage/transcricoes", exist_ok=True)
os.makedirs("storage/respostas", exist_ok=True)


@router.post("/processar/")
async def processar_audio(numero: str = Form(...), audio: UploadFile = File(...)):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    input_ogg = f"storage/audios/input_{timestamp}.ogg"
    texto_path = f"storage/transcricoes/{timestamp}.txt"

    # Salva áudio recebido
    with open(input_ogg, "wb") as f:
        f.write(await audio.read())

    # 1) Transcrição (Whisper suporta OGG diretamente)
    with open(input_ogg, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    texto_usuario = transcription.text

    with open(texto_path, "w", encoding="utf-8") as f:
        f.write(texto_usuario)

    # 2) Resposta IA
    resposta_texto = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": texto_usuario}]
    ).choices[0].message.content

    # 3) Sintetiza voz
    sintetizado = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=resposta_texto
    )

    # Codifica o áudio em base64 para envio na resposta
    audio_content = sintetizado.read()
    audio_base64 = base64.b64encode(audio_content).decode('utf-8')

    # Limpa arquivos temporários
    try:
        os.remove(input_ogg)
        # os.remove(texto_path)  # Manter transcrição para logs/debug
    except OSError:
        pass

    return {
        "status": "ok",
        "usuario": numero,
        "texto_usuario": texto_usuario,
        "resposta_texto": resposta_texto,
        "resposta_audio_base64": f"data:audio/wav;base64,{audio_base64}"
    }


@router.post("/falar")
async def falar(texto: str = Form(...)):
    print("Geração de áudio iniciada...")
    # Gera áudio pela TTS da OpenAI
    sintetizado = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=texto
    )
    print("Geração de áudio finalizada.")

    # Codifica o áudio em base64 para envio na resposta
    audio_content = sintetizado.read()
    audio_base64 = base64.b64encode(audio_content).decode('utf-8')

    return {
        "status": "ok",
        "entrada_texto": texto,
        "resposta_audio_base64": f"data:audio/wav;base64,{audio_base64}"
    }




class AudioBase64Request(BaseModel):
    audio: str
    numero: str = "unknown"

@router.post("/processar_base64")
async def processar_audio_base64(data: AudioBase64Request):
    try:
        print("Iniciando processamento de áudio base64...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        texto_path = f"storage/transcricoes/{timestamp}.txt"

        # Decodifica o áudio base64
        print("Decodificando áudio base64...")
        audio_bytes = base64.b64decode(data.audio)

        # 1) Transcrição (Whisper suporta áudio em bytes via io.BytesIO)
        print("Iniciando transcrição com Whisper...")
        audio_file_like = io.BytesIO(audio_bytes)
        audio_file_like.name = "input_audio.ogg"  # Nomear para ajudar o Whisper a identificar o formato
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file_like
        )
        texto_usuario = transcription.text
        print(f"Transcrição concluída: {texto_usuario}")

        with open(texto_path, "w", encoding="utf-8") as f:
            f.write(texto_usuario)
        print(f"Transcrição salva em {texto_path}")

        # 2) Resposta IA
        print("Gerando resposta com GPT-4o-mini...")
        resposta_texto = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": texto_usuario}]
        ).choices[0].message.content
        print(f"Resposta gerada: {resposta_texto}")

        # 3) Sintetiza voz
        print("Sintetizando voz com TTS...")
        sintetizado = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=resposta_texto
        )
        print("Síntese de voz concluída.")

        # Codifica o áudio em base64 para envio na resposta
        print("Codificando áudio em base64...")
        audio_content = sintetizado.read()
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')

        # Limpa arquivos temporários (não há arquivo de áudio salvo)
        try:
            # os.remove(texto_path)  # Manter transcrição para logs/debug
            pass
        except OSError:
            pass

        print("Processamento concluído com sucesso.")
        return {
            "status": "ok",
            "usuario": data.numero,
            "texto_usuario": texto_usuario,
            "resposta_texto": resposta_texto,
            "resposta_audio_base64": f"data:audio/wav;base64,{audio_base64}"
        }
    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
