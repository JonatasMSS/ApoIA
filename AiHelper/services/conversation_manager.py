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
        
        # Diretórios para persistência
        self.storage_dir = "storage/conversations"
        self.vectorstore_dir = f"{self.storage_dir}/vectorstores"
        self.history_dir = f"{self.storage_dir}/histories"
        
        os.makedirs(self.vectorstore_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        
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
    
    def generate_response(self, numero: str, user_message: str) -> str:
        """
        Gera resposta usando RAG com contexto da conversa.
        
        Args:
            numero: Número do WhatsApp do usuário
            user_message: Mensagem do usuário
            
        Returns:
            Resposta gerada pela IA
        """
        user_id = self._get_user_id(numero)
        
        print(f"🤖 Gerando resposta para usuário {user_id}")
        print(f"📝 Mensagem: {user_message}")
        
        # Adiciona mensagem do usuário ao contexto
        self.add_message_to_context(user_id, user_message, is_user=True)
        
        # Obtém contexto relevante
        relevant_context = self.get_relevant_context(user_id, user_message, k=5)
        print(f"📚 Contexto relevante recuperado: {len(relevant_context)} mensagens")
        
        # Obtém histórico de chat
        chat_history = self._get_chat_history(user_id, limit=10)
        
        # Cria prompt com contexto
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente prestativo e amigável. 
            Use o contexto da conversa anterior para dar respostas mais personalizadas e coerentes.
            Se o usuário fizer referência a algo mencionado antes, use esse contexto.
            
            Contexto relevante da conversa:
            {context}
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        # Cria chain
        chain = prompt | self.llm
        
        # Gera resposta
        try:
            response = chain.invoke({
                "context": "\n".join(relevant_context),
                "chat_history": chat_history,
                "question": user_message
            })
            
            resposta_texto = response.content
            
            # Adiciona resposta ao contexto
            self.add_message_to_context(user_id, resposta_texto, is_user=False)
            
            print(f"✅ Resposta gerada com sucesso")
            return resposta_texto
            
        except Exception as e:
            print(f"❌ Erro ao gerar resposta: {e}")
            raise
    
    def get_conversation_summary(self, numero: str, limit: int = 10) -> List[Dict]:
        """Retorna resumo da conversa do usuário"""
        user_id = self._get_user_id(numero)
        history = self.user_histories.get(user_id, [])
        return history[-limit:]
    
    def clear_user_context(self, numero: str):
        """Limpa contexto de um usuário específico"""
        user_id = self._get_user_id(numero)
        
        # Remove do cache
        if user_id in self.user_vectorstores:
            del self.user_vectorstores[user_id]
        if user_id in self.user_histories:
            del self.user_histories[user_id]
        
        print(f"🗑️ Contexto do usuário {user_id} limpo")


# Instância global
conversation_manager = ConversationManager()
