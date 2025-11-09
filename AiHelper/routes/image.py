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

class ImageRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"  # Tamanhos: 1024x1024, 1792x1024, 1024x1792
    quality: str = "hd"  # "standard" ou "hd"
    n: int = 1  # Número de imagens (1-10)

@router.post("/generate-image")
async def generate_image(req: ImageRequest):
    """
    Gera imagem usando DALL-E 3
    
    - **prompt**: Descrição da imagem desejada
    - **size**: Tamanho da imagem (1024x1024, 1792x1024, 1024x1792)
    - **quality**: Qualidade da imagem (standard ou hd)
    - **n**: Número de imagens a gerar (1-10)
    """
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=req.prompt,
            size=req.size,
            quality=req.quality,
            n=req.n
        )
        
        # Buscar e codificar imagens em base64
        images = []
        for image in response.data:
            try:
                # Fazer download da imagem
                img_response = requests.get(image.url)
                img_response.raise_for_status()
                
                # Codificar em base64
                img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                
                images.append({
                    "base64": f"data:image/png;base64,{img_base64}",
                    "revised_prompt": image.revised_prompt
                })
            except requests.RequestException as e:
                raise HTTPException(status_code=500, detail=f"Erro ao baixar imagem: {str(e)}")
        
        return {
            "success": True,
            "images": images,
            "created": response.created
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar imagem: {str(e)}")
