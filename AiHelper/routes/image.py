from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

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
        
        # Retorna as URLs das imagens geradas
        images = [{"url": image.url, "revised_prompt": image.revised_prompt} 
                  for image in response.data]
        
        return {
            "success": True,
            "images": images,
            "created": response.created
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar imagem: {str(e)}")
