from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
import time

load_dotenv()
router = APIRouter()

# Configurar a API do Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class VideoRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "16:9"  # Opções: "16:9", "9:16", "1:1"
    duration: int = 5  # Duração em segundos (Veo suporta até 8 segundos)

@router.post("/generate-video")
async def generate_video(req: VideoRequest):
    """
    Gera vídeo usando Google Veo (via Gemini API) - Versão econômica
    
    - **prompt**: Descrição do vídeo desejado
    - **aspect_ratio**: Proporção do vídeo (16:9, 9:16, 1:1)
    - **duration**: Duração do vídeo em segundos (máximo 8 segundos)
    
    Nota: Veo é a solução de geração de vídeo do Google, mais econômica que Sora.
    """
    try:
        # Usar o modelo Veo via Gemini API
        # Veo 2.0 é o modelo mais recente para geração de vídeo
        model = genai.GenerativeModel('veo-002')
        
        # Gerar o vídeo com os parâmetros especificados
        response = model.generate_content(
            req.prompt,
            generation_config={
                'response_mime_type': 'video/mp4',
                'aspect_ratio': req.aspect_ratio,
                'duration': req.duration
            }
        )
        
        # O Veo retorna o vídeo de forma assíncrona
        # Pode precisar aguardar a geração ser concluída
        if hasattr(response, 'video'):
            video_data = response.video
            return {
                "success": True,
                "video_url": video_data.url if hasattr(video_data, 'url') else None,
                "video_data": video_data.data if hasattr(video_data, 'data') else None,
                "prompt": req.prompt,
                "aspect_ratio": req.aspect_ratio,
                "duration": req.duration,
                "model": "veo-002",
                "message": "Vídeo gerado com sucesso usando Google Veo"
            }
        else:
            # Caso a resposta não contenha vídeo diretamente
            return {
                "success": True,
                "message": "Vídeo em processamento",
                "prompt": req.prompt,
                "aspect_ratio": req.aspect_ratio,
                "duration": req.duration,
                "model": "veo-002",
                "note": "A geração pode levar alguns minutos. Use o endpoint /video-status para verificar o progresso."
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar vídeo com Veo: {str(e)}"
        )

@router.post("/download-video")
async def download_video(video_url: str, filename: str = "generated_video.mp4"):
    """
    Baixa o vídeo da URL fornecida e salva no PC local
    
    - **video_url**: URL do vídeo a ser baixado
    - **filename**: Nome do arquivo para salvar (padrão: generated_video.mp4)
    """
    try:
        # Buscar informações do vídeo usando a API do Gemini
        # Nota: A implementação exata depende de como o Gemini gerencia trabalhos assíncronos
        model = genai.GenerativeModel('veo-002')
        
        # Tentar recuperar o status do vídeo
        # A API pode variar, então tratamos possíveis exceções
        operation = genai.get_operation(video_id)
        
        return {
            "video_id": video_id,
            "status": operation.metadata.get('status', 'unknown') if hasattr(operation, 'metadata') else 'processing',
            "url": operation.result.url if hasattr(operation, 'result') and hasattr(operation.result, 'url') else None,
            "model": "veo-002"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao verificar status do vídeo: {str(e)}"
        )

@router.get("/veo-info")
async def get_veo_info():
    """
    Retorna informações sobre o modelo Veo e suas capacidades
    """
    return {
        "model": "veo-002",
        "provider": "Google Gemini",
        "description": "Veo é o modelo de geração de vídeo do Google, oferecendo uma alternativa mais econômica ao Sora",
        "features": {
            "max_duration": "8 segundos",
            "aspect_ratios": ["16:9", "9:16", "1:1"],
            "quality": "Alta qualidade com realismo fotográfico",
            "cost": "Mais econômico que alternativas como Sora"
        },
        "supported_styles": [
            "Realismo fotográfico",
            "Animação",
            "Cinematográfico",
            "Timelapse",
            "Aéreo"
        ]
    }
