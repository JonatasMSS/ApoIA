from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import base64

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
    Gera vídeo usando Sora (simulado, pois a API não está disponível publicamente)
    
    - **prompt**: Descrição do vídeo desejado
    - **duration**: Duração do vídeo em segundos
    - **resolution**: Resolução do vídeo
    
    Nota: Como a API do Sora não está disponível, retorna um vídeo de exemplo.
    """
    try:
        # Simulação da resposta do Sora, pois a API não está disponível
        # Usando um vídeo de exemplo para demonstração
        sample_video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        
        # Simular download e codificação em base64 (para vídeos pequenos)
        # Nota: Para vídeos reais, isso pode ser muito grande
        try:
            video_response = requests.get(sample_video_url, stream=True)
            video_response.raise_for_status()
            
            # Para demonstração, limitar o tamanho (primeiros 1MB)
            video_data = b""
            for chunk in video_response.iter_content(chunk_size=1024):
                video_data += chunk
                if len(video_data) > 1024 * 1024:  # 1MB limit
                    break
            
            video_base64 = base64.b64encode(video_data).decode('utf-8')
            
        except requests.RequestException:
            # Fallback se não conseguir baixar
            video_base64 = "simulated_base64_data"
        
        return {
            "success": True,
            "video_url": sample_video_url,
            "video_base64": f"data:video/mp4;base64,{video_base64}",
            "prompt": req.prompt,
            "duration": req.duration,
            "resolution": req.resolution,
            "note": "Este é um vídeo de exemplo, pois a API do Sora não está disponível publicamente."
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar vídeo: {str(e)}"
        )

@router.post("/download-video")
async def download_video(video_url: str, filename: str = "generated_video.mp4"):
    """
    Baixa o vídeo da URL fornecida e salva no PC local
    
    - **video_url**: URL do vídeo a ser baixado
    - **filename**: Nome do arquivo para salvar (padrão: generated_video.mp4)
    """
    try:
        # Fazer download do vídeo
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        # Salvar no diretório atual do projeto
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return {
            "success": True,
            "message": f"Vídeo baixado com sucesso para {filepath}",
            "filepath": filepath,
            "filename": filename
        }
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao baixar vídeo: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao salvar vídeo: {str(e)}"
        )
