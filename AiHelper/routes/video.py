from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class VideoRequest(BaseModel):
    prompt: str
    duration: int = 5  # Duração em segundos (tipicamente 5-10s para Sora)
    resolution: str = "1920x1080"  # Resolução do vídeo

@router.post("/generate-video")
async def generate_video(req: VideoRequest):
    """
    Gera vídeo usando Sora 2
    
    - **prompt**: Descrição do vídeo desejado
    - **duration**: Duração do vídeo em segundos
    - **resolution**: Resolução do vídeo
    
    Nota: A API do Sora pode estar em preview/beta.
    Verifique a documentação oficial da OpenAI para os parâmetros corretos.
    """
    try:
        # NOTA: A API do Sora ainda pode estar em desenvolvimento/beta
        # Este é um exemplo de implementação baseado no padrão da OpenAI
        # Ajuste conforme a documentação oficial quando disponível
        
        response = client.videos.generate(
            model="sora-2",
            prompt=req.prompt,
            duration=req.duration,
            resolution=req.resolution
        )
        
        return {
            "success": True,
            "video_url": response.url if hasattr(response, 'url') else response.data[0].url,
            "prompt": req.prompt,
            "duration": req.duration,
            "resolution": req.resolution,
            "created": response.created if hasattr(response, 'created') else None
        }
    
    except AttributeError as e:
        # Caso a API do Sora não esteja disponível ou tenha estrutura diferente
        raise HTTPException(
            status_code=501, 
            detail=f"API do Sora não implementada ou não disponível. Erro: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar vídeo: {str(e)}"
        )

@router.get("/video-status/{video_id}")
async def get_video_status(video_id: str):
    """
    Verifica o status de geração de um vídeo (útil para processos assíncronos)
    
    - **video_id**: ID do vídeo sendo gerado
    """
    try:
        # Exemplo de como pode funcionar a verificação de status
        # Ajuste conforme a API real do Sora
        response = client.videos.retrieve(video_id)
        
        return {
            "video_id": video_id,
            "status": response.status,
            "url": response.url if hasattr(response, 'url') else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao verificar status do vídeo: {str(e)}"
        )
