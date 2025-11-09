# 🎓 Apo.IA - Sistema de Alfabetização Inteligente

Sistema completo de alfabetização via WhatsApp utilizando IA, desenvolvido com FastAPI (backend) e TypeScript (bot WhatsApp). O projeto combina processamento de áudio, análise de leitura, geração de imagens e chatbot conversacional para ensinar adultos a ler e escrever de forma personalizada.

## Integrantes

- Jonatas Miguel de Sousa Soares -> jonatas.miguelss@gmail.com
- Samuel Ismael ->samuel.ismael@academico.ufpb.br
- Cauã Lacerda -> lacerdacaua1010@gmail.com

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [API Endpoints](#api-endpoints)
- [Contribuindo](#contribuindo)

## 📖 Sobre o Projeto

**Apo.IA** é um sistema de alfabetização assistido por IA que utiliza WhatsApp como interface principal. O sistema guia o usuário através de 6 fases de aprendizado:

1. **Saudação Inicial** - Apresentação e coleta de dados
2. **Coleta de Informações** - Nome e idade do aluno
3. **Teste de Leitura** - Avaliação inicial do nível
4. **Exercícios de Leitura** - Prática com textos adaptados
5. **Avaliação de Leitura** - Feedback personalizado
6. **Conversação Livre** - Ensino adaptativo com RAG

### Diferenciais

- 🎤 **Processamento de Áudio**: Transcrição automática com Whisper
- 🖼️ **Geração de Imagens**: Criação de material didático com PIL
- 🧠 **IA Personalizada**: Respostas contextualizadas com GPT-4o-mini
- 📊 **Avaliação Inteligente**: Análise de progresso com LangChain
- 💾 **Persistência**: Estado do usuário e histórico com FAISS
- 🗣️ **Text-to-Speech**: Áudios de resposta com OpenAI TTS

## 🏗️ Arquitetura

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  WhatsApp   │────────▶│   Whatsbot   │────────▶│  AiHelper   │
│   (User)    │         │ (TypeScript) │         │   (FastAPI) │
└─────────────┘         └──────────────┘         └─────────────┘
                              │                         │
                              │                         │
                              ▼                         ▼
                        ┌──────────┐            ┌──────────┐
                        │  Redis   │            │ OpenAI   │
                        │  Cache   │            │   API    │
                        └──────────┘            └──────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │  Supabase    │
                                              │  Database    │
                                              └──────────────┘
```

## ✨ Funcionalidades

### Backend (AiHelper)

- ✅ **Chat Inteligente** - Conversação com GPT-4o-mini
- ✅ **Geração de Imagens** - DALL-E 3 com retorno em base64
- ✅ **Processamento de Áudio** - Transcrição + IA + TTS
- ✅ **Avaliação de Alfabetização** - Análise de nível com IA
- ✅ **Exercícios de Leitura** - Textos adaptados ao nível
- ✅ **Sistema RAG** - Busca vetorial com FAISS
- ✅ **Histórico de Conversas** - Persistência local

### Bot WhatsApp (Whatsbot)

- ✅ **Integração WhatsApp Web** - whatsapp-web.js
- ✅ **Envio de Áudios** - Base64 para API
- ✅ **API REST** - Fastify com TypeScript

## 🛠️ Tecnologias

### Backend (Python)

| Tecnologia | Versão | Descrição |
|-----------|--------|-----------|
| FastAPI | 0.115.6 | Framework web assíncrono |
| OpenAI | 2.7.1 | GPT-4, Whisper, DALL-E, TTS |
| LangChain | 1.0.0+ | Framework de IA |
| FAISS | 1.12.0 | Busca vetorial |
| Pillow | 12.0.0 | Processamento de imagens |
| Pydantic | 2.12.4 | Validação de dados |
| Uvicorn | 0.32.1 | Servidor ASGI |

### Bot (TypeScript)

| Tecnologia | Versão | Descrição |
|-----------|--------|-----------|
| Fastify | 5.6.1 | Framework web |
| whatsapp-web.js | 1.34.2 | Cliente WhatsApp |
| Axios | 1.13.2 | Cliente HTTP |
| TypeScript | 5.9.3 | Linguagem tipada |

## 📦 Requisitos

- **Python** 3.10+
- **Node.js** 18+
- **Redis** (opcional, para cache)
- **Conta OpenAI** com acesso às APIs
- **Projeto Supabase** configurado

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/JonatasMSS/ApoIA.git
cd ApoIA
```

### 2. Backend (AiHelper)

```powershell
# Navegue até a pasta
cd AiHelper

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente
.\venv\Scripts\Activate.ps1

# Instale dependências
pip install -r requirements.txt
```

### 3. Bot WhatsApp (Whatsbot)

```powershell
# Navegue até a pasta
cd ..\Whatsbot

# Instale dependências
npm install
```

## ⚙️ Configuração

### 1. Backend (.env)

Crie o arquivo `.env` na pasta `AiHelper/`:

```env
# OpenAI API
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxxxxxxxxxxxx

# Opcional: Configurações do servidor
HOST=0.0.0.0
PORT=8000
```

### 2. Bot WhatsApp (opcional: .env)

Crie o arquivo `.env` na pasta `Whatsbot/` (se necessário):

```env
# Redis (opcional)
REDIS_HOST=localhost
REDIS_PORT=6379

# API Backend
API_BASE_URL=http://localhost:8000
```

## 🎯 Uso

### Iniciar Backend

```powershell
cd AiHelper
python main.py

# Ou com uvicorn diretamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse: `http://localhost:8000/docs` para a documentação interativa.

### Iniciar Bot WhatsApp

```powershell
cd Whatsbot
npm run dev
```

**Primeira execução:**
1. Um QR Code aparecerá no terminal
2. Escaneie com WhatsApp (Configurações > Aparelhos Conectados)
3. O bot estará pronto para uso

### Testar API Diretamente

```powershell
# Chat
curl -X POST "http://localhost:8000/chat" `
  -H "Content-Type: application/json" `
  -d '{"message":"Olá, me ajude a aprender a ler"}'

# Gerar Imagem
curl -X POST "http://localhost:8000/generate-image" `
  -H "Content-Type: application/json" `
  -d '{"prompt":"Texto educativo com palavras simples","size":"1024x1024"}'

# Criar Usuário
curl -X POST "http://localhost:8000/users/" `
  -H "Content-Type: application/json" `
  -d '{"name":"Maria","age":35,"learning_rate":"iniciante"}'

# Buscar Usuário
curl "http://localhost:8000/users/1"
```

## 📁 Estrutura do Projeto

```
ApoIA/
├── AiHelper/                  # Backend FastAPI
│   ├── libs/                  # Clientes (OpenAI, Supabase)
│   │   ├── __init__.py
│   │   ├── OpenAI.py
│   │   └── supabase.py
│   ├── routes/                # Rotas da API
│   │   ├── audio.py          # Processamento de áudio
│   │   ├── chat.py           # Chat com GPT
│   │   ├── image.py          # Geração de imagens
│   │   ├── user.py           # CRUD de usuários
│   │   └── video.py          # Simulação de vídeos
│   ├── services/              # Lógica de negócio
│   │   ├── conversation_manager.py      # Orquestrador principal
│   │   ├── literacy_evaluator.py        # Avaliação de alfabetização
│   │   ├── reading_exercises.py         # Exercícios de leitura
│   │   ├── text_detection.py            # Detecção de nome/idade
│   │   ├── user_state_manager.py        # Gerenciamento de estado
│   │   ├── conversation_history.py      # Histórico de conversas
│   │   ├── vectorstore_manager.py       # Busca vetorial (RAG)
│   │   └── user.py                      # Serviços de usuário
│   ├── storage/               # Dados persistidos
│   │   ├── audios/           # Áudios temporários
│   │   ├── conversations/    # Estados e históricos
│   │   │   ├── histories/
│   │   │   ├── states/
│   │   │   └── vectorstores/
│   │   ├── transcricoes/     # Textos transcritos
│   │   └── respostas/        # Respostas geradas
│   ├── main.py               # Aplicação principal
│   ├── requirements.txt      # Dependências Python
│   ├── .env.example          # Exemplo de variáveis
│   └── README.md             # Documentação
│
└── Whatsbot/                  # Bot WhatsApp
    ├── src/
    │   ├── main.ts           # Servidor principal
    │   ├── api/
    │   │   └── AiHelper.ts   # Cliente API backend
    │   ├── lib/
    │   │   └── redis.ts      # Cliente Redis
    │   ├── routes/           # Rotas Fastify
    │   │   ├── index.ts
    │   │   ├── root.ts
    │   │   └── send.ts
    │   └── service/
    │       └── AiServices.ts # Integração com backend
    ├── package.json          # Dependências Node
    └── tsconfig.json         # Configuração TypeScript
```

## 🔌 API Endpoints

### Chat
- `POST /chat` - Conversa com GPT-4o-mini

### Imagens
- `POST /generate-image` - Gera imagem com DALL-E 3

### Áudio
- `POST /audio/processar/` - Upload de áudio (FormData)
- `POST /audio/processar_base64` - Áudio em base64 (JSON)
- `POST /audio/falar` - Text-to-Speech

### Usuários
- `POST /users/` - Criar usuário
- `GET /users/{id}` - Buscar usuário

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Notas Importantes

### Segurança
- **Produção**: Altere `allow_origins=["*"]` para domínios específicos
- **Chaves API**: Nunca commite arquivos `.env`
- **Rate Limiting**: Configure limites adequados no Fastify

### Performance
- FAISS armazena vetores localmente para busca rápida
- Históricos são salvos em JSON para persistência

### Áudio
- Formatos suportados: OGG, MP3, WAV, M4A
- Whisper processa diretamente sem conversão
- Respostas TTS são retornadas em base64 (`data:audio/wav;base64,...`)

### Limitações
- A geração de vídeo é simulada (Sora não disponível publicamente)
- WhatsApp limita tamanho de áudios e imagens
- OpenAI tem limites de rate e custos por uso

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais como parte do programa Devs Impacto 16.

## 👥 Autores

Equipe Apo.IA - Novembro 2024

---
