# AiHelper — mini projeto FastAPI

Pequeno projeto exemplar com FastAPI para testar endpoints e CORS, integrado com OpenAI.

Arquivos importantes
- `main.py` — aplicação FastAPI com CORS, rota GET `/` e rotas organizadas em `routes/`.
- `routes/chat.py` — rota POST `/chat` para interagir com OpenAI.
- `requirements.txt` — dependências necessárias (incluindo openai e python-dotenv).

Como usar (PowerShell)

1. Instalar dependências:

```powershell
Set-Location 'C:\Users\gears\Desktop\Devs_impacto_16\AiHelper'
python -m pip install -r requirements.txt
```

2. Configurar variável de ambiente:
   - Crie um arquivo `.env` na raiz do projeto com: `OPENAI_API_KEY=your_api_key_here`

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
```

Notas
- A configuração de CORS permite todas as origens para simplificar o desenvolvimento (`allow_origins = ["*"]`). Em produção, restrinja para domínios confiáveis.
- Certifique-se de ter uma chave válida da OpenAI no `.env`.
- Adicione mais rotas em `routes/` conforme necessário e registre-as no `main.py`.
