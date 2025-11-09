from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os
from openai import OpenAI
from services.user import insert_user_service
from routes.chat import router as chat_router
from routes.image import router as image_router
from routes.audio import router as audio_router



app = FastAPI(title="AiHelper", version="0.1.0")

# CORS - permitir requisições de outras origens durante desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # no desenvolvimento permite todas as origens; em produção restrinja
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"ok": True, "message": "AiHelper FastAPI está funcionando!"}

# Incluir os routers
app.include_router(chat_router)
app.include_router(image_router)
app.include_router(audio_router)

if __name__ == "__main__":
    # Executa com reload para desenvolvimento
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
   


