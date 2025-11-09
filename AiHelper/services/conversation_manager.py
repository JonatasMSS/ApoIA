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
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
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
from services.reading_exercises import (
    get_reading_text,
    analyze_reading_attempt,
    generate_dynamic_reading_challenge
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
        
        Fases:
        1. inicial - Saudação
        2. aguardando_nome - Coleta nome/idade
        3. solicitar_teste_leitura - Prepara teste
        4. aguardando_teste_leitura - Avalia teste
        5. exercicios_leitura - Exercícios de leitura em voz alta
        6. aguardando_leitura_audio - Esperando áudio de leitura
        7. personalizado - Conversação livre adaptada
        
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
        elif fase == "exercicios_leitura":
            return self._handle_reading_exercises_phase(state, user_id)
        elif fase == "aguardando_leitura_audio":
            return self._handle_reading_evaluation_phase(state, user_message, user_id)
        elif fase == "aguardando_decisao_pos_feedback":
            return self._handle_post_feedback_decision(state, user_message, user_id)
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
            
            resposta = f"""Muito legal te conhecer, {state["nome"]}! 🤗

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
        
        # Atualiza estado (com promoção mínima baseada em acertos)
        state["nivel_alfabetizacao"] = resultado["nivel"]
        state["acertos"] = resultado["acertos"]
        state["total_testes"] = resultado["total"]

        # Regra solicitada: ao acertar 4 palavras ou mais no teste inicial,
        # o próximo exercício deve ser um texto simples (nível avançado).
        # Isso garante que não enviaremos apenas UMA palavra após bom desempenho.
        try:
            if int(resultado.get("acertos", 0)) >= 4:
                state["nivel_alfabetizacao"] = "avançado"
        except Exception:
            pass
        state["exercicio_numero"] = 1  # Inicia contador de exercícios
        state["fase"] = "exercicios_leitura"  # Vai para exercícios de leitura
        self.state_manager.save_user_state(user_id)
        
        print(f"📊 Resultado: {resultado['acertos']}/{resultado['total']} - {resultado['nivel'].upper()}")
        print(f"📖 Avançando para exercícios de leitura")

        resposta = f"""Muito bem, {state["nome"]}! 👏

Você acertou {resultado["acertos"]} de {resultado["total"]} palavras!

Seu nível é: {state["nivel_alfabetizacao"].upper()} (ajustado para enviar um texto simples)

Agora vamos praticar leitura em voz alta! 📚

Vou te enviar um texto bem simples. Você vai:
1️⃣ Ver o texto escrito (imagem)
2️⃣ Ouvir eu lendo o texto (áudio)
3️⃣ Tentar ler o texto em voz alta

Depois eu vou te dar um retorno sobre como você leu! 😊

Pronto para começar?"""

        return resposta
    
    def _handle_reading_exercises_phase(self, state: Dict, user_id: str) -> str:
        """Fase 5: Exercícios de leitura em voz alta."""
        print("✅ FASE 5: Exercícios de leitura")
        
        # Pega texto baseado no nível
        exercicio_num = state.get("exercicio_numero", 1)
        # Tenta gerar dinamicamente via GPT; se falhar, usa fallback estático
        try:
            texto_info = generate_dynamic_reading_challenge(state["nivel_alfabetizacao"], exercicio_num)
            # Garante chaves esperadas
            if not isinstance(texto_info, dict) or not texto_info.get("texto"):
                raise ValueError("conteúdo inválido do gerador dinâmico")
        except Exception as _:
            texto_info = get_reading_text(state["nivel_alfabetizacao"], exercicio_num)
        
        # Salva texto atual no estado
        state["texto_atual"] = texto_info["texto"]
        state["texto_titulo"] = texto_info["titulo"]
        state["fase"] = "aguardando_leitura_audio"
        self.state_manager.save_user_state(user_id)
        
        print(f"   📖 Texto: {texto_info['titulo']}")
        print(f"   📊 Nível: {texto_info['dificuldade']}")
        
        resposta = f"""📚 Exercício de Leitura #{exercicio_num}

Título: "{texto_info["titulo"]}"

Vou te enviar o texto agora! Primeiro, veja o texto e ouça eu lendo. Depois, você tenta ler em voz alta, tá bom? 😊

(O texto e o áudio serão enviados a seguir)"""
        
        return resposta
    
    def _handle_reading_evaluation_phase(self, state: Dict, user_message: str, user_id: str) -> str:
        """Fase 6: Avaliação da leitura em voz alta."""
        print("✅ FASE 6: Avaliando leitura")
        
        texto_esperado = state.get("texto_atual", "")
        texto_titulo = state.get("texto_titulo", "Texto")
        
        print(f"   📖 Esperado: {texto_esperado[:50]}...")
        print(f"   🎤 Lido: {user_message[:50]}...")
        
        # Analisa tentativa de leitura
        resultado = analyze_reading_attempt(texto_esperado, user_message)

        # Gera retorno amigável com LLM (PT-BR simples, sem termos técnicos)
        feedback = self._generate_friendly_feedback(resultado, texto_titulo, state)

        print(f"   📊 Similaridade: {resultado['similaridade']}%")
        print(f"   ⭐ Avaliação: {resultado['avaliacao']}")

        # Após o retorno, aguardamos a decisão do aluno por áudio livre
        state["fase"] = "aguardando_decisao_pos_feedback"
        self.state_manager.save_user_state(user_id)

        # Mensagem curta e simples (sem números fixos)
        feedback += ("\n\nO que você quer fazer agora? Diga: ajuda ou outro exercício.")
        return feedback

    def _generate_friendly_feedback(self, resultado: Dict, titulo: str, state: Dict) -> str:
        """Cria um retorno curto e carinhoso usando LLM, sem termos técnicos ou porcentagens."""
        try:
            nome = state.get("nome") or "amigo(a)"
            nivel = state.get("nivel_alfabetizacao") or "iniciante"
            avaliacao = resultado.get("avaliacao", "regular")

            # Orientações por avaliação, sem números
            dica_por_avaliacao = {
                "excelente": "Você leu muito bem! Sua leitura está fluindo. Parabéns!",
                "bom": "Você foi muito bem! Só mais um pouquinho de prática e fica ainda melhor.",
                "regular": "Bom esforço! Vamos praticar mais um pouco. Eu estou com você.",
                "precisa_melhorar": "Tudo bem! A gente treina junto e você vai conseguir."
            }
            elogio = dica_por_avaliacao.get(avaliacao, "Ótimo trabalho! Vamos seguir juntos.")

            system = (
                "Você é a Apo.IA. Escreva um retorno MUITO curto, carinhoso e simples em português do Brasil. "
                "NÃO use palavras difíceis nem termos como 'análise', 'estatística', 'porcentagem' ou 'dados'. "
                "Evite números. Não use palavras estrangeiras. Use frases curtas e amigáveis."
            )
            user = (
                f"Nome: {nome}. Nível: {nivel}. Título do texto: {titulo}. "
                f"Avaliação: {avaliacao}. Mensagem base: {elogio}. "
                "Crie 2 a 3 frases curtas encorajando a continuar."
            )

            messages = [
                SystemMessage(content=system),
                HumanMessage(content=user)
            ]
            resp = self.llm.invoke(messages)
            content = resp.content if hasattr(resp, 'content') else str(resp)
            # Garantias mínimas: remover possíveis termos indesejados
            ban = ["análise", "analise", "estatística", "porcentagem", "dados", "%"]
            for b in ban:
                content = content.replace(b, "")
            return content.strip()
        except Exception:
            # Fallback simples
            return "Você foi muito bem! Vamos continuar treinando juntos. Eu acredito em você!"

    # ====== NOVA FASE: decisão livre após retorno ======
    def _handle_post_feedback_decision(self, state: Dict, user_message: str, user_id: str) -> str:
        """Interpreta a decisão do aluno via GPT (sem números fixos)."""
        print("✅ FASE: Decisão pós-retorno (interpretação livre)")
        decision = self._decide_next_action(user_message, state)

        action = decision.get("action", "unknown")
        increase = decision.get("increase_level")

        if action == "help":
            state["fase"] = "personalizado"
            self.state_manager.save_user_state(user_id)
            return (
                "Vamos para o modo de ajuda. Pode me dizer o que você quer aprender agora. 😊"
            )

        if action == "exercise":
            # Ajusta nível se pedido para aumentar
            if isinstance(increase, bool) and increase:
                atual = state.get("nivel_alfabetizacao") or "iniciante"
                novo = self._proximo_nivel(atual)
                state["nivel_alfabetizacao"] = novo
            # prepara próximo exercício
            state["fase"] = "exercicios_leitura"
            state["exercicio_numero"] = int(state.get("exercicio_numero", 1)) + 1
            self.state_manager.save_user_state(user_id)
            return self._handle_reading_exercises_phase(state, user_id)

        # Se não ficou claro, peça de forma simples (sem números)
        return "Não entendi. Prefere ajuda ou outro exercício?"

    def _proximo_nivel(self, n: str) -> str:
        n = (n or "iniciante").lower()
        if n.startswith("avanc"): return "avançado"
        if n.startswith("inter"): return "avançado"
        return "intermediário"

    # ==================== CLASSIFICADOR GERAL DE DECISÃO (GPT) ====================
    def _decide_next_action(self, user_message: str, state: Dict) -> Dict:
        """Retorna {action: 'help'|'exercise'|'unknown', increase_level: true|false|null}."""
        try:
            nivel_atual = state.get("nivel_alfabetizacao") or "iniciante"
            messages = [
                SystemMessage(content=(
                    "Você é um classificador. Leia a fala do aluno em português e decida o próximo passo.\n"
                    "Responda SOMENTE em JSON válido com o formato:\n"
                    "{\n  \"action\": \"help|exercise|unknown\",\n  \"increase_level\": true|false|null\n}\n"
                    "Definições:\n- action=help: o aluno quer ajuda/conversar com a assistente.\n"
                    "- action=exercise: o aluno quer fazer outro exercício.\n"
                    "- increase_level: true se o aluno pediu algo mais difícil / aumentar nível; false se pediu manter; null se não ficou claro.\n"
                    "Considere variações livres como 'quero continuar', 'mais difícil', 'me ajuda', 'fazer outro', 'pode ser mais fácil', etc.\n"
                )),
                HumanMessage(content=f"Nível atual: {nivel_atual}. Fala do aluno: {user_message}")
            ]
            resp = self.llm.invoke(messages)
            content = resp.content if hasattr(resp, 'content') else str(resp)
            import json as _json
            data = _json.loads(content)
            # Sanitiza saída
            action = str(data.get('action', 'unknown')).strip().lower()
            if action not in {"help", "exercise", "unknown"}:
                action = "unknown"
            increase = data.get('increase_level', None)
            if not isinstance(increase, bool):
                increase = None
            return {"action": action, "increase_level": increase}
        except Exception:
            return {"action": "unknown", "increase_level": None}
    
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
9. NUNCA use palavras estrangeiras. Substitua por termos do português do Brasil.
     - Exemplos: "feedback" -> "retorno", "ok/okay" -> "certo", "setup" -> "configuração",
         "coach/trainer" -> "treinador(a)", "challenge" -> "desafio", "task" -> "tarefa".

💬 ESTILO:
- Frases curtas
- Vocabulário simples
- Tom de professora paciente
- Evite jargões

📚 CONTEXTO:
{"\n".join(relevant_context[-3:]) if relevant_context else "Início da conversa"}

Responda mantendo foco em alfabetização e em português do Brasil simples."""),
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
    
    def should_generate_reading_text(self, numero: str) -> Dict:
        """
        Verifica se deve gerar texto de exercício de leitura.
        
        Returns:
            Dict com should_generate, texto, titulo, audio_text
        """
        user_id = self._get_user_id(numero)
        state = self.state_manager.get_user_state(user_id)
        
        if state["fase"] == "aguardando_leitura_audio":
            print("📖 Gerando texto de leitura")
            
            # Pega o texto atual do estado
            texto = state.get("texto_atual", "")
            titulo = state.get("texto_titulo", "Texto")
            exercicio_num = state.get("exercicio_numero", 1)
            
            return {
                "should_generate": True,
                "texto": texto,
                "titulo": titulo,
                "exercicio_num": exercicio_num,
                "audio_text": texto  # Texto para TTS ler
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
