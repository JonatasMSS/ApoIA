"""
Gerenciador de Conversas com Sistema RAG para Alfabetização Apo.IA (REFATORADO)

Este módulo orquestra o sistema de alfabetização, delegando responsabilidades
para módulos especializados:

- text_detection: Detecção de nome e idade
- literacy_evaluator: Avaliação de alfabetização
- user_state_manager: Gerenciamento de estado
- conversation_history: Histórico de mensagens
- vectorstore_manager: Busca vetorial (RAG)

Responsabilidade principal:
- Coordenar fluxo de alfabetização em 5 fases
- Gerar respostas contextualizadas com IA

Autor: Equipe Apo.IA
Data: Novembro 2024
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, List
import os
from dotenv import load_dotenv

# Importa módulos especializados
from services.text_detection import detect_name_and_age
from services.literacy_evaluator import (
    analyze_reading_level, 
    get_test_words, 
    generate_test_image_prompt
)
from services.user_state_manager import UserStateManager
from services.conversation_history import ConversationHistoryManager
from services.vectorstore_manager import VectorStoreManager

load_dotenv()


class ConversationManager:
    """
    Gerenciador Central de Conversas com RAG.
    
    Orquestra o sistema de alfabetização Apo.IA, coordenando:
    1. Fluxo estruturado em 5 fases
    2. Detecção de informações pessoais
    3. Avaliação de alfabetização
    4. Geração de respostas contextualizadas
    5. Persistência de dados
    """

    def __init__(self):
        """Inicializa gerenciador e componentes."""
        # Configuração da OpenAI
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=self.api_key
        )
        
        # Inicializa módulos especializados
        self.state_manager = UserStateManager()
        self.history_manager = ConversationHistoryManager()
        self.vectorstore_manager = VectorStoreManager(self.api_key)
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _get_user_id(self, numero: str) -> str:
        """Extrai ID limpo do número de telefone/WhatsApp."""
        return numero.split("@")[0] if "@" in numero else numero
    
    def _get_chat_history(self, user_id: str, limit: int = 10) -> List:
        """
        Obtém histórico formatado para LangChain.
        
        Args:
            user_id: ID do usuário
            limit: Quantidade de mensagens recentes
            
        Returns:
            Lista de mensagens LangChain
        """
        history = self.history_manager.get_history(user_id, limit=limit)
        messages = []
        
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        return messages
    
    def _add_message_to_context(self, user_id: str, message: str, is_user: bool = True):
        """
        Adiciona mensagem ao contexto completo.
        
        Args:
            user_id: ID do usuário
            message: Conteúdo da mensagem
            is_user: True se mensagem do usuário
        """
        # Adiciona ao histórico
        self.history_manager.add_message(user_id, message, is_user)
        
        # Adiciona ao vectorstore
        self.vectorstore_manager.add_message(user_id, message, is_user)
    
    def _should_restart_conversation(self, state: Dict, user_message: str, user_id: str) -> bool:
        """
        Verifica se deve reiniciar conversa.
        
        Returns:
            True se deve reiniciar
        """
        saudacoes = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'ei']
        mensagem_lower = user_message.lower().strip()
        
        if state["fase"] == "personalizado" and mensagem_lower in saudacoes:
            history = self.history_manager.get_history(user_id)
            return len(history) == 0
        
        return False
    
    # ==================== GERAÇÃO DE RESPOSTA (NÚCLEO) ====================
    
    def generate_response(self, numero: str, user_message: str) -> str:
        """
        Gera resposta contextualizada seguindo fluxo de alfabetização.
        
        🎯 FLUXO (5 FASES):
        1. Inicial → Saudação e solicitação de dados
        2. Aguardando Nome → Coleta nome e idade
        3. Solicitar Teste → Marca para envio de imagem
        4. Aguardando Teste → Avalia nível de alfabetização
        5. Personalizado → Ensino adaptado com RAG
        
        Args:
            numero: Número do WhatsApp
            user_message: Mensagem do usuário
            
        Returns:
            Resposta gerada pela IA
        """
        user_id = self._get_user_id(numero)
        state = self.state_manager.get_user_state(user_id)
        
        # Log
        print(f"\n{'='*60}")
        print(f"🤖 GERANDO RESPOSTA: {user_id}")
        print(f"📝 Mensagem: '{user_message}'")
        print(f"📊 Fase: '{state['fase']}'")
        print(f"{'='*60}\n")
        
        # Verifica se deve reiniciar
        if self._should_restart_conversation(state, user_message, user_id):
            print("   ✓ Reiniciando conversa...")
            state = self.state_manager._get_default_state()
            self.state_manager.user_states[user_id] = state
            self.state_manager.save_user_state(user_id)
        
        # Adiciona mensagem ao contexto
        self._add_message_to_context(user_id, user_message, is_user=True)
        
        # Rota para fase específica
        resposta_texto = self._route_by_phase(state, user_message, user_id)
        
        # Adiciona resposta ao contexto
        self._add_message_to_context(user_id, resposta_texto, is_user=False)
        
        print(f"✅ Resposta gerada e salva")
        print(f"{'='*60}\n")
        
        return resposta_texto
    
    def _route_by_phase(self, state: Dict, user_message: str, user_id: str) -> str:
        """
        Roteia para handler da fase atual.
        
        Args:
            state: Estado do usuário
            user_message: Mensagem recebida
            user_id: ID do usuário
            
        Returns:
            Resposta gerada
        """
        fase = state["fase"]
        
        if fase == "inicial":
            return self._handle_initial_phase(state, user_id)
        elif fase == "aguardando_nome":
            return self._handle_name_collection_phase(state, user_message, user_id)
        elif fase == "solicitar_teste_leitura":
            return self._handle_test_request_phase(state, user_id)
        elif fase == "aguardando_teste_leitura":
            return self._handle_test_evaluation_phase(state, user_message, user_id)
        else:  # personalizado
            return self._handle_personalized_phase(state, user_message, user_id)
    
    # ==================== HANDLERS DE FASES ====================
    
    def _handle_initial_phase(self, state: Dict, user_id: str) -> str:
        """Fase 1: Saudação inicial."""
        print("✅ FASE 1: Saudação")
        
        resposta = """Oi! Eu sou a Apo.IA, sua assistente para te ajudar a aprender a ler e escrever de um jeito fácil e divertido!

Eu vou te acompanhar passo a passo, ok? 😊

Pra começar, me conta seu nome e sua idade, por favor."""
        
        state["fase"] = "aguardando_nome"
        self.state_manager.save_user_state(user_id)
        
        return resposta
    
    def _handle_name_collection_phase(self, state: Dict, user_message: str, user_id: str) -> str:
        """Fase 2: Coleta de nome e idade."""
        print("✅ FASE 2: Coletando dados")
        
        # Detecta informações
        info = detect_name_and_age(user_message)
        
        # Atualiza estado
        if info["nome"] and not state["nome"]:
            state["nome"] = info["nome"]
            print(f"   ✓ Nome: {state['nome']}")
        if info["idade"] and not state["idade"]:
            state["idade"] = info["idade"]
            print(f"   ✓ Idade: {state['idade']}")
        
        # Verifica se tem ambos
        if state["nome"] and state["idade"]:
            print(f"✅ Dados completos! Avançando para teste...")
            
            resposta = f"""Prazer em te conhecer, {state["nome"]}! 🤗

Agora eu quero ver como você lê essas palavras.

Vou enviar uma imagem com algumas palavras pra você. Depois, diga ou escreva quais palavras você vê na imagem, tá bom?"""
            
            state["fase"] = "solicitar_teste_leitura"
            state["palavras_teste"] = get_test_words("basico")
            self.state_manager.save_user_state(user_id)
            
            return resposta
        
        # Parcial - solicita faltante
        elif state["nome"]:
            resposta = f"Legal, {state['nome']}! E quantos anos você tem?"
        elif state["idade"]:
            resposta = f"Você tem {state['idade']} anos, que legal! E qual é o seu nome?"
        else:
            resposta = "Me conta seu nome e sua idade, por favor. Pode ser assim: 'Meu nome é João e tenho 25 anos' 😊"
        
        self.state_manager.save_user_state(user_id)
        return resposta
    
    def _handle_test_request_phase(self, state: Dict, user_id: str) -> str:
        """Fase 3: Marcador para envio de imagem."""
        print("✅ FASE 3: Preparando teste")
        
        resposta = "Agora eu quero ver como você lê essas palavras. Vou enviar uma imagem com algumas palavras pra você. Depois, diga ou escreva quais palavras você vê na imagem, tá bom? 😊"
        
        # Não muda fase aqui (mudança feita em should_generate_test_image)
        return resposta
    
    def _handle_test_evaluation_phase(self, state: Dict, user_message: str, user_id: str) -> str:
        """Fase 4: Avaliação do teste."""
        print("✅ FASE 4: Avaliando teste")
        print(f"   Esperadas: {state['palavras_teste']}")
        print(f"   Resposta: '{user_message}'")
        
        # Analisa resposta
        resultado = analyze_reading_level(user_message, state["palavras_teste"])
        
        # Atualiza estado
        state["nivel_alfabetizacao"] = resultado["nivel"]
        state["acertos"] = resultado["acertos"]
        state["total_testes"] = resultado["total"]
        state["fase"] = "personalizado"
        self.state_manager.save_user_state(user_id)
        
        print(f"📊 Resultado: {resultado['acertos']}/{resultado['total']} - {resultado['nivel'].upper()}")
        print(f"🎓 Avançando para fase personalizada")
        
        resposta = f"""Muito bem, {state["nome"]}! 👏

Você acertou {resultado["acertos"]} de {resultado["total"]} palavras!

Eu já entendi o seu nível. Agora vou preparar leituras em áudio e exercícios personalizados pra te ajudar a evoluir rapidinho!

Podemos começar? 😄"""
        
        return resposta
    
    def _handle_personalized_phase(self, state: Dict, user_message: str, user_id: str) -> str:
        """Fase 5: Aprendizado personalizado com RAG."""
        print("✅ FASE 5: Aprendizado personalizado")
        print(f"   Nome: {state.get('nome')}, Nível: {state.get('nivel_alfabetizacao')}")
        
        # Recupera contexto relevante
        relevant_context = self.vectorstore_manager.get_relevant_context(user_id, user_message, k=3)
        chat_history = self._get_chat_history(user_id, limit=5)
        
        # Prompt especializado
        prompt = self._build_literacy_prompt(state, relevant_context)
        
        # Gera resposta
        chain = prompt | self.llm
        
        try:
            print("   🤖 Gerando resposta com GPT-4...")
            response = chain.invoke({
                "chat_history": chat_history,
                "question": user_message
            })
            print("   ✅ Resposta gerada")
            return response.content
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return f"Desculpa, {state.get('nome', 'amigo(a)')}! Tive um probleminha aqui. Pode repetir? 😊"
    
    def _build_literacy_prompt(self, state: Dict, relevant_context: List[str]) -> ChatPromptTemplate:
        """
        Constrói prompt especializado em alfabetização.
        
        Args:
            state: Estado do usuário
            relevant_context: Contexto relevante do RAG
            
        Returns:
            Template de prompt
        """
        return ChatPromptTemplate.from_messages([
            ("system", f"""Você é a Apo.IA, assistente especializada em alfabetização. 

🎯 MISSÃO: Ajudar {state.get('nome', 'o usuário')} a aprender a ler e escrever.

📊 PERFIL DO ALUNO:
- Nome: {state.get('nome', 'não informado')}
- Idade: {state.get('idade', 'não informada')}
- Nível: {state.get('nivel_alfabetizacao', 'iniciante')}
- Acertos no teste: {state.get('acertos', 0)}/{state.get('total_testes', 4)}

🎓 DIRETRIZES:
1. Use linguagem MUITO SIMPLES
2. Seja SEMPRE encorajadora
3. Foque em leitura e escrita prática
4. Use emojis para conexão emocional
5. Exemplos do cotidiano
6. Celebre progressos
7. Adapte ao nível do aluno
8. Ensine fonética quando apropriado

💬 ESTILO:
- Frases curtas
- Vocabulário simples
- Tom de professora paciente
- Evite jargões

📚 CONTEXTO:
{"\n".join(relevant_context[-3:]) if relevant_context else "Início da conversa"}

Responda mantendo foco em alfabetização."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
    
    # ==================== MÉTODOS PÚBLICOS ====================
    
    def get_conversation_summary(self, numero: str, limit: int = 10) -> List[Dict]:
        """Retorna resumo do histórico."""
        user_id = self._get_user_id(numero)
        return self.history_manager.get_history(user_id, limit=limit)
    
    def should_generate_test_image(self, numero: str) -> Dict:
        """
        Verifica se deve gerar imagem de teste.
        
        Returns:
            Dict com should_generate, words, prompt
        """
        user_id = self._get_user_id(numero)
        state = self.state_manager.get_user_state(user_id)
        
        if state["fase"] == "solicitar_teste_leitura":
            print("🎨 Gerando imagem de teste")
            
            # Avança fase
            state["fase"] = "aguardando_teste_leitura"
            self.state_manager.save_user_state(user_id)
            
            words = state.get("palavras_teste", get_test_words())
            prompt = generate_test_image_prompt(words)
            
            return {
                "should_generate": True,
                "words": words,
                "prompt": prompt
            }
        
        return {"should_generate": False}
    
    def get_user_info(self, numero: str) -> Dict:
        """Retorna informações do usuário."""
        user_id = self._get_user_id(numero)
        state = self.state_manager.get_user_state(user_id)
        
        return {
            "user_id": user_id,
            "fase": state.get("fase"),
            "nome": state.get("nome"),
            "idade": state.get("idade"),
            "nivel": state.get("nivel_alfabetizacao")
        }
    
    def clear_user_context(self, numero: str):
        """Limpa contexto completo do usuário."""
        user_id = self._get_user_id(numero)
        
        print(f"\n🗑️ LIMPANDO CONTEXTO: {user_id}")
        print("="*60)
        
        self.vectorstore_manager.clear_vectorstore(user_id)
        self.history_manager.clear_history(user_id)
        self.state_manager.clear_user_state(user_id)
        
        print("="*60)
        print(f"✅ Contexto limpo!\n")


# ==================== INSTÂNCIA GLOBAL ====================
conversation_manager = ConversationManager()
