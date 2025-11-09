# AiHelper — mini projeto FastAPI

Pequeno projeto exemplar com FastAPI para testar endpoints e CORS, integrado com OpenAI e Supabase.

Arquivos importantes
- `main.py` — aplicação FastAPI com CORS, rota GET `/` e rotas organizadas em `routes/`.
- `routes/chat.py` — rota POST `/chat` para interagir com OpenAI.
- `routes/image.py` — rota POST `/generate-image` para gerar imagens com DALL-E 3 e retornar em base64.
- `routes/video.py` — rotas POST `/generate-video` (simulado) e `/download-video` para vídeos.
- `routes/audio.py` — rotas POST `/processar_audio` (transcrição + resposta + TTS) e `/falar` (TTS apenas).
- `lib/__init__.py` — inicialização do cliente Supabase.
- `services/user.py` — exemplo de serviço usando Supabase.
- `requirements.txt` — dependências necessárias (incluindo openai, python-dotenv, supabase, requests, pydub).

Como usar (PowerShell)

1. Instalar dependências:

```powershell
Set-Location 'C:\Users\gears\Desktop\Devs_impacto_16\AiHelper'
python -m pip install -r requirements.txt
```

2. Configurar variável de ambiente:
   - Crie um arquivo `.env` na raiz do projeto com:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     SUPABASE_URL=your_supabase_project_url_here
     SUPABASE_KEY=your_supabase_anon_key_here
     ```

3. Iniciar em modo de desenvolvimento (com reload):

```powershell
python main.py
# ou diretamente com uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Testes rápidos:

```powershell
# GET /
curl http://localhost:8000/

# POST /chat
curl -H "Content-Type: application/json" -d '{"message":"Hello, tell me a joke"}' http://localhost:8000/chat

# POST /generate-image
curl -H "Content-Type: application/json" -d '{"prompt":"A beautiful sunset over the ocean", "size":"1024x1024", "quality":"hd"}' http://localhost:8000/generate-image

# POST /generate-video (simulado)
curl -H "Content-Type: application/json" -d '{"prompt":"A cat playing in the garden", "duration":5, "resolution":"1920x1080"}' http://localhost:8000/generate-video

# POST /download-video
curl -X POST "http://localhost:8000/download-video?video_url=https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4&filename=my_video.mp4"

# POST /processar_audio (requer arquivo de áudio)
curl -X POST -F "numero=123456789" -F "audio=@caminho/para/audio.ogg" http://localhost:8000/processar_audio

# POST /falar
curl -H "Content-Type: application/json" -d '{"text":"Olá, como você está?"}' http://localhost:8000/falar
```

Notas
- A configuração de CORS permite todas as origens para simplificar o desenvolvimento (`allow_origins = ["*"]`). Em produção, restrinja para domínios confiáveis.
- Certifique-se de ter chaves válidas da OpenAI e Supabase no `.env`.
- A geração de vídeo usa uma simulação, pois a API do Sora não está disponível publicamente.
- Para as rotas de áudio, certifique-se de que o `ffmpeg` está instalado no sistema (necessário para pydub converter áudios).
- Adicione mais rotas em `routes/` e serviços em `services/` conforme necessário e registre-as no `main.py`.
