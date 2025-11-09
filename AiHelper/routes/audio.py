from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime
import os
import base64
import io
import traceback
import requests
# from libs.OpenAI import client
from dotenv import load_dotenv
from services.conversation_manager import conversation_manager
import re

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cria o router (não uma nova instância de FastAPI)
router = APIRouter(prefix="/audio", tags=["Áudio"])

# Garante pastas
os.makedirs("storage/audios", exist_ok=True)
os.makedirs("storage/transcricoes", exist_ok=True)
os.makedirs("storage/respostas", exist_ok=True)


def _sanitize_ptbr(texto: str) -> str:
    """
    Sanitiza termos estrangeiros comuns para equivalentes em PT-BR simples.
    Mantém o restante do texto intacto.
    """
    if not isinstance(texto, str):
        return texto

    substitutions = {
        r"\bfeedback\b": "retorno",
        r"\bok\b": "certo",
        r"\bokay\b": "certo",
        r"\bsetup\b": "configuração",
        r"\bapp\b": "aplicativo",
        r"\blogin\b": "entrar",
        r"\blogout\b": "sair",
        r"\bcoach\b": "treinador",
        r"\bchallenge\b": "desafio",
        r"\bscore\b": "pontuação",
        r"\btask\b": "tarefa",
        r"\btrainer\b": "treinador",
        r"\bprint\b": "imagem",
        r"\bscan\b": "digitalizar",
    }

    result = texto
    for pattern, repl in substitutions.items():
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
    return result


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

    # 2) Resposta IA (sempre em PT-BR simples, sem estrangeirismos)
    resposta_texto = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é a Apo.IA. Responda SEMPRE em português do Brasil, com frases curtas,"
                    " palavras simples e tom acolhedor. NUNCA use palavras estrangeiras (como 'feedback',"
                    " 'ok', 'setup', 'coach'). Sempre substitua por termos comuns em PT-BR."
                ),
            },
            {"role": "user", "content": texto_usuario},
        ],
        temperature=0.6,
    ).choices[0].message.content or ""

    resposta_texto = _sanitize_ptbr(resposta_texto)

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
    texto_direto: str | None = None  # Para mensagens de texto sem áudio

@router.post("/processar_base64")
async def processar_audio_base64(data: AudioBase64Request):
    try:
        print("Iniciando processamento...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        texto_path = f"storage/transcricoes/{timestamp}.txt"

        # Verifica se é mensagem de texto direto ou áudio
        if data.texto_direto:
            print(f"📝 Processando mensagem de texto: {data.texto_direto}")
            texto_usuario = data.texto_direto
        else:
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

        # 2) Resposta da Apo.IA usando RAG com contexto
        print("Gerando resposta com Apo.IA usando RAG...")
        resposta_texto = conversation_manager.generate_response(data.numero, texto_usuario)
        resposta_texto = _sanitize_ptbr(resposta_texto)
        print(f"Resposta gerada: {resposta_texto}")
        
        # 3) Verifica se deve gerar imagem de teste de leitura
        test_info = conversation_manager.should_generate_test_image(data.numero)
        
        if test_info["should_generate"]:
            print("🎨 Gerando imagem de teste de leitura...")
            
            # Gerar a imagem usando PIL (texto perfeito, sem alucinações)
            from services.literacy_evaluator import generate_test_image
            img_base64 = generate_test_image(test_info["words"])
            
            print("✅ Imagem de teste gerada com sucesso.")
            
            # Gera TAMBÉM um áudio explicativo para acompanhar a imagem
            print("🔊 Gerando áudio explicativo para o teste...")
            sintetizado = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=resposta_texto
            )
            audio_content = sintetizado.read()
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            print("✅ Áudio explicativo gerado.")
            
            # Retorna com imagem de teste E áudio explicativo
            return {
                "status": "ok",
                "tipo": "imagem_com_audio",
                "usuario": data.numero,
                "texto_usuario": texto_usuario,
                "resposta_texto": resposta_texto,
                "resposta_audio_base64": f"data:audio/wav;base64,{audio_base64}",
                "imagem_base64": f"data:image/png;base64,{img_base64}",
                "is_test_image": True
            }
        
        # 3.5) Verifica se deve gerar texto de exercício de leitura
        reading_info = conversation_manager.should_generate_reading_text(data.numero)
        
        if reading_info["should_generate"]:
            print(f"📖 Gerando exercício de leitura #{reading_info['exercicio_num']}...")
            
            # Gerar imagem com o texto
            from services.literacy_evaluator import generate_reading_text_image
            img_base64 = generate_reading_text_image(reading_info["titulo"], reading_info["texto"])
            
            print("✅ Imagem do texto gerada com sucesso.")
            
            # Gera áudio da IA lendo o texto
            print("🔊 Gerando áudio da IA lendo o texto...")
            sintetizado_texto = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=reading_info["audio_text"],
                speed=0.9  # Mais devagar para facilitar acompanhamento
            )
            audio_texto = sintetizado_texto.read()
            audio_texto_base64 = base64.b64encode(audio_texto).decode('utf-8')
            
            # Gera também o áudio da resposta explicativa
            sintetizado_resposta = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=resposta_texto
            )
            audio_resposta = sintetizado_resposta.read()
            audio_resposta_base64 = base64.b64encode(audio_resposta).decode('utf-8')
            
            print("✅ Áudios gerados.")
            
            # Retorna com imagem do texto, áudio da IA lendo E áudio da explicação
            return {
                "status": "ok",
                "tipo": "exercicio_leitura",
                "usuario": data.numero,
                "texto_usuario": texto_usuario,
                "resposta_texto": resposta_texto,
                "resposta_audio_base64": f"data:audio/wav;base64,{audio_resposta_base64}",
                "imagem_base64": f"data:image/png;base64,{img_base64}",
                "texto_audio_base64": f"data:audio/wav;base64,{audio_texto_base64}",
                "is_reading_exercise": True,
                "texto_titulo": reading_info["titulo"]
            }

        # 4) Sintetiza voz
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
            "tipo": "audio",
            "usuario": data.numero,
            "texto_usuario": texto_usuario,
            "resposta_texto": resposta_texto,
            "resposta_audio_base64": f"data:audio/wav;base64,{audio_base64}"
        }
    except Exception as e:
        print(f": {str(e)}")
        print(f"Stack trace completo:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Novas rotas para gerenciar contexto da conversa

@router.get("/historico/{numero}")
async def obter_historico(numero: str, limit: int = 10):
    """
    Obtém o histórico de conversa de um usuário
    """
    try:
        historico = conversation_manager.get_conversation_summary(numero, limit)
        return {
            "status": "ok",
            "numero": numero,
            "total_mensagens": len(historico),
            "historico": historico
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info_usuario/{numero}")
async def info_usuario(numero: str):
    """
    Obtém informações do usuário (fase, nome, nível, etc)
    """
    try:
        info = conversation_manager.get_user_info(numero)
        return {
            "status": "ok",
            "info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/limpar_contexto/{numero}")
async def limpar_contexto(numero: str):
    """
    Limpa o contexto e histórico de um usuário
    """
    try:
        conversation_manager.clear_user_context(numero)
        return {
            "status": "ok",
            "message": f"Contexto do usuário {numero} limpo com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reiniciar_conversa/{numero}")
async def reiniciar_conversa(numero: str):
    """
    Reinicia a conversa do usuário (reseta para fase inicial mas mantém histórico)
    """
    try:
        user_id = conversation_manager._get_user_id(numero)
        state = conversation_manager._get_user_state(user_id)
        
        # Reseta estado para inicial
        state["fase"] = "inicial"
        state["nome"] = None
        state["idade"] = None
        state["nivel_alfabetizacao"] = None
        state["palavras_teste"] = []
        state["acertos"] = 0
        state["total_testes"] = 0
        
        conversation_manager._save_user_state(user_id)
        
        return {
            "status": "ok",
            "message": f"Conversa do usuário {numero} reiniciada com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
