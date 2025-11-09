from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime
import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class ConversationManager:
    """
    Gerenciador de conversas com RAG usando LangChain.
    Mantém contexto da conversa e histórico por usuário.
    Sistema de alfabetização Apo.IA com fluxo estruturado.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.embeddings = OpenAIEmbeddings(api_key=self.api_key)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=self.api_key
        )
        
        # Armazena vectorstores e históricos por usuário
        self.user_vectorstores: Dict[str, FAISS] = {}
        self.user_histories: Dict[str, List[Dict]] = {}
        self.user_states: Dict[str, Dict] = {}  # Estado da conversa por usuário
        
        # Diretórios para persistência
        self.storage_dir = "storage/conversations"
        self.vectorstore_dir = f"{self.storage_dir}/vectorstores"
        self.history_dir = f"{self.storage_dir}/histories"
        self.state_dir = f"{self.storage_dir}/states"
        
        os.makedirs(self.vectorstore_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.state_dir, exist_ok=True)
        
    def _get_user_id(self, numero: str) -> str:
        """Extrai ID do usuário do número de telefone"""
        return numero.split("@")[0] if "@" in numero else numero
    
    def _load_user_history(self, user_id: str) -> List[Dict]:
        """Carrega histórico de conversa do usuário"""
        history_file = f"{self.history_dir}/{user_id}.json"
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_user_history(self, user_id: str):
        """Salva histórico de conversa do usuário"""
        history_file = f"{self.history_dir}/{user_id}.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_histories.get(user_id, []), f, ensure_ascii=False, indent=2)
    
    def _load_user_state(self, user_id: str) -> Dict:
        """Carrega estado do usuário (fase da conversa, dados coletados, etc)"""
        state_file = f"{self.state_dir}/{user_id}.json"
        
        # Estado padrão para novo usuário
        default_state = {
            "fase": "inicial",  # inicial, aguardando_nome, teste_leitura, personalizado
            "nome": None,
            "idade": None,
            "nivel_alfabetizacao": None,
            "palavras_teste": [],
            "acertos": 0,
            "total_testes": 0,
            "ultimo_acesso": datetime.now().isoformat()
        }
        
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            # Verifica se último acesso foi há mais de 24 horas (conversa antiga)
            if "ultimo_acesso" in state:
                try:
                    from datetime import timedelta
                    ultimo_acesso = datetime.fromisoformat(state["ultimo_acesso"])
                    tempo_decorrido = datetime.now() - ultimo_acesso
                    
                    # Se passou mais de 24 horas, reseta para nova conversa
                    if tempo_decorrido > timedelta(hours=24):
                        print(f"⚠️ Conversa antiga detectada (mais de 24h). Resetando estado.")
                        return default_state
                except:
                    pass
            
            # Atualiza último acesso
            state["ultimo_acesso"] = datetime.now().isoformat()
            return state
            
        return default_state
    
    def _save_user_state(self, user_id: str):
        """Salva estado do usuário"""
        state_file = f"{self.state_dir}/{user_id}.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_states.get(user_id, {}), f, ensure_ascii=False, indent=2)
    
    def _get_user_state(self, user_id: str) -> Dict:
        """Obtém estado atual do usuário"""
        if user_id not in self.user_states:
            self.user_states[user_id] = self._load_user_state(user_id)
        
        # IMPORTANTE: Se está na fase "inicial", garante que estado seja limpo
        state = self.user_states[user_id]
        if state["fase"] == "inicial":
            # Reseta informações pessoais para garantir novo início
            state["nome"] = None
            state["idade"] = None
            state["nivel_alfabetizacao"] = None
            state["palavras_teste"] = []
            state["acertos"] = 0
            state["total_testes"] = 0
            
        return state
    
    def _get_or_create_vectorstore(self, user_id: str) -> FAISS:
        """Obtém ou cria vectorstore para o usuário"""
        if user_id in self.user_vectorstores:
            return self.user_vectorstores[user_id]
        
        vectorstore_path = f"{self.vectorstore_dir}/{user_id}"
        
        # Tenta carregar vectorstore existente
        if os.path.exists(f"{vectorstore_path}/index.faiss"):
            try:
                vectorstore = FAISS.load_local(
                    vectorstore_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                self.user_vectorstores[user_id] = vectorstore
                print(f"✅ Vectorstore carregado para usuário {user_id}")
                return vectorstore
            except Exception as e:
                print(f"⚠️ Erro ao carregar vectorstore: {e}. Criando novo...")
        
        # Cria novo vectorstore com documento inicial
        initial_doc = f"Início da conversa com o usuário {user_id} em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        vectorstore = FAISS.from_texts(
            [initial_doc],
            self.embeddings,
            metadatas=[{"timestamp": datetime.now().isoformat(), "type": "system"}]
        )
        
        # Salva vectorstore
        vectorstore.save_local(vectorstore_path)
        self.user_vectorstores[user_id] = vectorstore
        
        print(f"✅ Novo vectorstore criado para usuário {user_id}")
        return vectorstore
    
    def _get_chat_history(self, user_id: str, limit: int = 10) -> List:
        """Obtém histórico de chat como lista de mensagens LangChain"""
        if user_id not in self.user_histories:
            self.user_histories[user_id] = self._load_user_history(user_id)
        
        history = self.user_histories[user_id]
        messages = []
        
        # Converte últimas mensagens para formato LangChain
        for msg in history[-limit:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        return messages
    
    def add_message_to_context(self, user_id: str, message: str, is_user: bool = True):
        """Adiciona mensagem ao contexto vetorial"""
        vectorstore = self._get_or_create_vectorstore(user_id)
        
        timestamp = datetime.now().isoformat()
        role = "user" if is_user else "assistant"
        
        # Adiciona ao vectorstore
        vectorstore.add_texts(
            [message],
            metadatas=[{
                "timestamp": timestamp,
                "role": role,
                "type": "message"
            }]
        )
        
        # Salva vectorstore atualizado
        vectorstore_path = f"{self.vectorstore_dir}/{user_id}"
        vectorstore.save_local(vectorstore_path)
        
        # Adiciona ao histórico
        if user_id not in self.user_histories:
            self.user_histories[user_id] = []
        
        self.user_histories[user_id].append({
            "role": role,
            "content": message,
            "timestamp": timestamp
        })
        
        self._save_user_history(user_id)
    
    def get_relevant_context(self, user_id: str, query: str, k: int = 5) -> List[str]:
        """Recupera contexto relevante do histórico"""
        vectorstore = self._get_or_create_vectorstore(user_id)
        
        # Busca documentos relevantes
        docs = vectorstore.similarity_search(query, k=k)
        
        return [doc.page_content for doc in docs]
    
    def _detect_name_and_age(self, user_message: str) -> Dict:
        """Detecta nome e idade na mensagem do usuário"""
        import re
        
        print(f"🔍 Detectando nome e idade em: '{user_message}'")
        
        # Detecta idade (números entre 1 e 120)
        idade = None
        idade_patterns = [
            r'\b(\d{1,3})\s*anos?\b',  # "25 anos" ou "25 ano"
            r'\btenho\s+(\d{1,3})\b',   # "tenho 25"
            r'\b(\d{1,3})\s*$',         # número no final
            r'^\s*(\d{1,3})\s*$'        # apenas o número
        ]
        
        for pattern in idade_patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                idade_temp = int(match.group(1))
                if 1 <= idade_temp <= 120:
                    idade = idade_temp
                    print(f"  ✓ Idade encontrada: {idade}")
                    break
        
        # Detecta nome
        nome = None
        patterns = [
            # Padrões explícitos com verbos (prioridade máxima)
            r'(?:me chamo|meu nome é|nome é|eu sou o|eu sou a|sou o|sou a|sou)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)\s*(?:e\s+|,|$)',
            # Nome seguido de "e tenho" ou "," ou final
            r'([A-Za-zÀ-ÿ]{3,})\s+(?:e\s+tenho|,\s*tenho)',
            # Nome no início capitalizado (seguido de "e" ou vírgula ou final)
            r'^([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)\s*(?:e\s+|,|$)',
            # Apenas uma palavra capitalizada (pode ser nome sozinho)
            r'^\s*([A-Z][a-zà-ÿ]{2,})\s*$',
            # Qualquer palavra capitalizada com 3+ letras (último recurso)
            r'\b([A-Z][a-zà-ÿ]{2,})\b'
        ]
        
        palavras_ignorar = ['Oi', 'Olá', 'Bom', 'Boa', 'Tenho', 'Anos', 'Ano', 'Meu', 'Minha', 'Nome', 'Idade', 'Sou', 'E']
        
        for pattern in patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                nome_temp = match.group(1).strip()
                # Capitaliza o nome corretamente
                nome_temp = ' '.join(word.capitalize() for word in nome_temp.split())
                
                # Evita palavras comuns
                if nome_temp not in palavras_ignorar and len(nome_temp) > 1:
                    nome = nome_temp
                    print(f"  ✓ Nome encontrado: {nome}")
                    break
        
        if not nome:
            print(f"  ✗ Nome NÃO encontrado")
        if not idade:
            print(f"  ✗ Idade NÃO encontrada")
            
        return {"nome": nome, "idade": idade}
    
    def _analyze_reading_level(self, user_response: str, expected_words: List[str]) -> Dict:
        """Analisa o nível de alfabetização baseado na resposta"""
        user_words = user_response.lower().split()
        expected_set = set(w.lower() for w in expected_words)
        
        # Conta acertos
        acertos = sum(1 for word in user_words if word in expected_set)
        total = len(expected_words)
        taxa_acerto = (acertos / total * 100) if total > 0 else 0
        
        # Define nível
        if taxa_acerto >= 80:
            nivel = "avançado"
        elif taxa_acerto >= 50:
            nivel = "intermediário"
        else:
            nivel = "iniciante"
        
        return {
            "nivel": nivel,
            "acertos": acertos,
            "total": total,
            "taxa_acerto": taxa_acerto
        }
    
    def generate_response(self, numero: str, user_message: str) -> str:
        """
        Gera resposta seguindo EXATAMENTE o fluxo da Apo.IA para alfabetização.
        
        FLUXO OBRIGATÓRIO:
        1. Saudação inicial → Solicita nome e idade
        2. Coleta nome e idade → Envia imagem de teste
        3. Aguarda resposta do teste → Avalia nível
        4. Personaliza aprendizado → Continua ensino
        
        Args:
            numero: Número do WhatsApp do usuário
            user_message: Mensagem do usuário
            
        Returns:
            Resposta gerada pela IA
        """
        user_id = self._get_user_id(numero)
        state = self._get_user_state(user_id)
        
        print(f"\n{'='*60}")
        print(f"🤖 GERANDO RESPOSTA PARA USUÁRIO: {user_id}")
        print(f"📝 Mensagem recebida: '{user_message}'")
        print(f"📊 Fase atual do usuário: '{state['fase']}'")
        print(f"📋 Estado completo: {state}")
        print(f"{'='*60}\n")
        
        # Detecta se é uma saudação inicial em conversa já existente
        saudacoes_iniciais = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'ei']
        mensagem_lower = user_message.lower().strip()
        
        # Se está em fase personalizado e manda APENAS uma saudação simples, pode querer reiniciar
        if state["fase"] == "personalizado" and mensagem_lower in saudacoes_iniciais:
            print("⚠️ Saudação inicial detectada em conversa existente.")
            print("   Verificando se deve reiniciar...")
            
            # Verifica histórico recente - se não há mensagens recentes, reinicia
            history = self.user_histories.get(user_id, [])
            if len(history) == 0:
                print("   ✓ Sem histórico recente. REINICIANDO conversa.")
                state["fase"] = "inicial"
                state["nome"] = None
                state["idade"] = None
                state["nivel_alfabetizacao"] = None
                state["palavras_teste"] = []
                state["acertos"] = 0
                state["total_testes"] = 0
                self._save_user_state(user_id)
        
        # Adiciona mensagem do usuário ao contexto
        self.add_message_to_context(user_id, user_message, is_user=True)
        
        # Fluxo baseado na fase
        resposta_texto = ""
        
        # 🟢 FASE 1: SAUDAÇÃO INICIAL
        if state["fase"] == "inicial":
            print("✅ FASE 1: Enviando saudação inicial")
            resposta_texto = """Oi! Eu sou a Apo.IA, sua assistente para te ajudar a aprender a ler e escrever de um jeito fácil e divertido!

Eu vou te acompanhar passo a passo, ok? 😊

Pra começar, me conta seu nome e sua idade, por favor."""
            
            state["fase"] = "aguardando_nome"
            self._save_user_state(user_id)
        
        # 🟢 FASE 2: COLETANDO NOME E IDADE
        elif state["fase"] == "aguardando_nome":
            print("✅ FASE 2: Coletando nome e idade")
            info = self._detect_name_and_age(user_message)
            
            # Atualiza apenas se detectou novos valores
            if info["nome"] and not state["nome"]:
                state["nome"] = info["nome"]
                print(f"✅ Nome detectado e salvo: {state['nome']}")
            if info["idade"] and not state["idade"]:
                state["idade"] = info["idade"]
                print(f"✅ Idade detectada e salva: {state['idade']}")
            
            # Verifica se tem AMBOS nome e idade
            if state["nome"] and state["idade"]:
                print(f"✅✅ DADOS COMPLETOS! Nome: {state['nome']}, Idade: {state['idade']}")
                print("🎨 AVANÇANDO PARA FASE 3: Teste de leitura")
                
                resposta_texto = f"""Prazer em te conhecer, {state["nome"]}! 🤗

Agora eu quero ver como você lê essas palavras.

Vou enviar uma imagem com algumas palavras pra você. Depois, diga ou escreva quais palavras você vê na imagem, tá bom?"""
                
                state["fase"] = "solicitar_teste_leitura"
                state["palavras_teste"] = ["CASA", "SOL", "PATO", "BOLA"]
                self._save_user_state(user_id)
            
            # Tem apenas nome - pede idade
            elif state["nome"] and not state["idade"]:
                print(f"ℹ️ Tem nome ({state['nome']}), falta idade")
                resposta_texto = f"Legal, {state['nome']}! E quantos anos você tem?"
                self._save_user_state(user_id)
            
            # Tem apenas idade - pede nome
            elif state["idade"] and not state["nome"]:
                print(f"ℹ️ Tem idade ({state['idade']}), falta nome")
                resposta_texto = f"Você tem {state['idade']} anos, que legal! E qual é o seu nome?"
                self._save_user_state(user_id)
            
            # Não tem nada ainda
            else:
                print("⚠️ Nome e idade NÃO detectados na mensagem")
                resposta_texto = "Me conta seu nome e sua idade, por favor. Pode ser assim: 'Meu nome é João e tenho 25 anos' 😊"
        
        # 🟢 FASE 3: IMAGEM SERÁ ENVIADA (marcador)
        elif state["fase"] == "solicitar_teste_leitura":
            print("✅ FASE 3: Preparando para enviar imagem de teste")
            # Esta mensagem explica o teste. O áudio.py vai detectar e enviar a imagem
            resposta_texto = f"Agora eu quero ver como você lê essas palavras. Vou enviar uma imagem com algumas palavras pra você. Depois, diga ou escreva quais palavras você vê na imagem, tá bom? 😊"
            # NÃO muda de fase aqui - deixa para should_generate_test_image fazer isso
        
        # 🟢 FASE 4: AGUARDANDO RESPOSTA DO TESTE
        elif state["fase"] == "aguardando_teste_leitura":
            print("✅ FASE 4: Analisando resposta do teste de leitura")
            print(f"   Palavras esperadas: {state['palavras_teste']}")
            print(f"   Resposta do usuário: '{user_message}'")
            
            resultado = self._analyze_reading_level(user_message, state["palavras_teste"])
            
            state["nivel_alfabetizacao"] = resultado["nivel"]
            state["acertos"] = resultado["acertos"]
            state["total_testes"] = resultado["total"]
            state["fase"] = "personalizado"
            self._save_user_state(user_id)
            
            print(f"📊 RESULTADO DO TESTE:")
            print(f"   Acertos: {resultado['acertos']}/{resultado['total']}")
            print(f"   Taxa: {resultado['taxa_acerto']:.1f}%")
            print(f"   Nível: {resultado['nivel']}")
            print(f"🎓 AVANÇANDO PARA FASE 5: Aprendizado personalizado")
            
            resposta_texto = f"""Muito bem, {state["nome"]}! 👏

Você acertou {resultado["acertos"]} de {resultado["total"]} palavras!

Eu já entendi o seu nível. Agora vou preparar leituras em áudio e exercícios personalizados pra te ajudar a evoluir rapidinho!

Podemos começar? 😄"""
        
        # 🟢 FASE 5: APRENDIZADO PERSONALIZADO
        else:
            print("✅ FASE 5: Aprendizado personalizado com IA")
            print(f"   Nome: {state.get('nome', 'N/A')}")
            print(f"   Nível: {state.get('nivel_alfabetizacao', 'N/A')}")
            
            # Busca contexto relevante (limitado para evitar contexto antigo demais)
            relevant_context = self.get_relevant_context(user_id, user_message, k=3)
            # Usa apenas mensagens RECENTES do histórico (últimas 5)
            chat_history = self._get_chat_history(user_id, limit=5)
            
            # Prompt FOCADO EM ALFABETIZAÇÃO
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""Você é a Apo.IA, assistente de alfabetização. 

🎯 MISSÃO: Ajudar {state.get('nome', 'o usuário')} a aprender a ler e escrever.

📊 DADOS DO ALUNO:
- Nome: {state.get('nome', 'não informado')}
- Idade: {state.get('idade', 'não informada')}
- Nível: {state.get('nivel_alfabetizacao', 'iniciante')}
- Acertos no teste: {state.get('acertos', 0)}/{state.get('total_testes', 4)}

🎓 REGRAS OBRIGATÓRIAS:
1. Use linguagem MUITO SIMPLES e clara
2. Seja SEMPRE encorajadora e positiva
3. Foque em ensinar leitura e escrita
4. Use emojis para conexão emocional
5. Dê exemplos práticos do dia a dia
6. Celebre cada pequeno progresso
7. Adapte ao nível do aluno

💬 ESTILO:
- Frases curtas e diretas
- Palavras simples e comuns
- Tom amigável como uma professora paciente
- Evite termos técnicos

CONTEXTO RECENTE:
{"\n".join(relevant_context[-3:]) if relevant_context else "Primeira conversa"}

Responda de forma educativa, mantendo o foco em alfabetização."""),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}")
            ])
            
            # Gera resposta
            chain = prompt | self.llm
            
            try:
                response = chain.invoke({
                    "chat_history": chat_history,
                    "question": user_message
                })
                
                resposta_texto = response.content
                
            except Exception as e:
                print(f"❌ Erro ao gerar resposta: {e}")
                # Fallback amigável
                resposta_texto = f"Desculpa, {state.get('nome', 'amigo(a)')}! Tive um probleminha aqui. Pode repetir o que você disse? 😊"
        
        # Adiciona resposta ao contexto (para todas as fases)
        self.add_message_to_context(user_id, resposta_texto, is_user=False)
        
        print(f"✅ Resposta gerada com sucesso")
        return resposta_texto
    
    def get_conversation_summary(self, numero: str, limit: int = 10) -> List[Dict]:
        """Retorna resumo da conversa do usuário"""
        user_id = self._get_user_id(numero)
        history = self.user_histories.get(user_id, [])
        return history[-limit:]
    
    def should_generate_test_image(self, numero: str) -> Dict:
        """
        Verifica se deve gerar imagem de teste de leitura
        
        Returns:
            Dict com 'should_generate' (bool), 'words' (list), 'prompt' (str) se aplicável
        """
        user_id = self._get_user_id(numero)
        state = self._get_user_state(user_id)
        
        if state["fase"] == "solicitar_teste_leitura":
            # Muda para aguardando resposta
            state["fase"] = "aguardando_teste_leitura"
            self._save_user_state(user_id)
            
            words = state.get("palavras_teste", ["CASA", "SOL", "PATO", "BOLA"])
            
            return {
                "should_generate": True,
                "words": words,
                "prompt": f"Crie uma imagem educativa e clara para alfabetização. Mostre 4 palavras simples escritas em letras GRANDES, COLORIDAS e bem legíveis (fonte tipo Comic Sans ou similar, fácil de ler). As palavras devem estar dispostas verticalmente ou em uma grade 2x2. Use cores diferentes para cada palavra e adicione pequenos ícones ilustrativos ao lado de cada palavra. As palavras são: {', '.join(words)}. Fundo branco ou muito claro."
            }
        
        return {"should_generate": False}
    
    def get_user_info(self, numero: str) -> Dict:
        """Retorna informações do usuário"""
        user_id = self._get_user_id(numero)
        state = self._get_user_state(user_id)
        return {
            "user_id": user_id,
            "fase": state.get("fase"),
            "nome": state.get("nome"),
            "idade": state.get("idade"),
            "nivel": state.get("nivel_alfabetizacao")
        }
    
    def clear_user_context(self, numero: str):
        """Limpa contexto de um usuário específico"""
        import shutil
        
        user_id = self._get_user_id(numero)
        
        print(f"🗑️ Limpando contexto do usuário {user_id}...")
        
        # Remove do cache em memória
        if user_id in self.user_vectorstores:
            del self.user_vectorstores[user_id]
            print(f"  ✓ Vectorstore removido da memória")
        
        if user_id in self.user_histories:
            del self.user_histories[user_id]
            print(f"  ✓ Histórico removido da memória")
        
        if user_id in self.user_states:
            del self.user_states[user_id]
            print(f"  ✓ Estado removido da memória")
        
        # Remove arquivos físicos
        # Remove vectorstore
        vectorstore_path = f"{self.vectorstore_dir}/{user_id}"
        if os.path.exists(vectorstore_path):
            shutil.rmtree(vectorstore_path)
            print(f"  ✓ Vectorstore deletado do disco")
        
        # Remove histórico
        history_file = f"{self.history_dir}/{user_id}.json"
        if os.path.exists(history_file):
            os.remove(history_file)
            print(f"  ✓ Histórico deletado do disco")
        
        # Remove estado
        state_file = f"{self.state_dir}/{user_id}.json"
        if os.path.exists(state_file):
            os.remove(state_file)
            print(f"  ✓ Estado deletado do disco")
        
        print(f"✅ Contexto do usuário {user_id} totalmente limpo!")


# Instância global
conversation_manager = ConversationManager()
