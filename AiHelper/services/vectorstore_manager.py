"""
Módulo de Gerenciamento de Vectorstore (RAG)

Responsável por gerenciar busca vetorial de contexto usando FAISS.
Funcionalidades:
- Criar/carregar vectorstores por usuário
- Adicionar mensagens ao vectorstore
- Busca semântica de contexto relevante
- Persistência em disco

Autor: Equipe Apo.IA
Data: Novembro 2024
"""

import os
from typing import Dict, List
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


class VectorStoreManager:
    """
    Gerenciador de vectorstore para busca semântica (RAG).
    
    Usa FAISS para manter índice vetorial de mensagens
    e permitir recuperação de contexto relevante.
    """
    
    def __init__(self, api_key: str, vectorstore_dir: str = "storage/conversations/vectorstores"):
        """
        Inicializa gerenciador de vectorstore.
        
        Args:
            api_key: Chave da API OpenAI
            vectorstore_dir: Diretório para salvar vectorstores
        """
        self.vectorstore_dir = vectorstore_dir
        self.embeddings = OpenAIEmbeddings(api_key=api_key)
        self.user_vectorstores: Dict[str, FAISS] = {}  # Cache em memória
        
        # Cria diretório se não existir
        os.makedirs(self.vectorstore_dir, exist_ok=True)
    
    def add_message(self, user_id: str, message: str, is_user: bool = True):
        """
        Adiciona mensagem ao vectorstore.
        
        Args:
            user_id: ID do usuário
            message: Conteúdo da mensagem
            is_user: True se mensagem do usuário, False se da IA
        """
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
        
        # Persiste no disco
        vectorstore_path = f"{self.vectorstore_dir}/{user_id}"
        vectorstore.save_local(vectorstore_path)
    
    def get_relevant_context(self, user_id: str, query: str, k: int = 5) -> List[str]:
        """
        Recupera contexto relevante usando busca semântica.
        
        Args:
            user_id: ID do usuário
            query: Mensagem/pergunta atual
            k: Quantidade de mensagens relevantes
            
        Returns:
            Lista de strings com mensagens relevantes
        """
        vectorstore = self._get_or_create_vectorstore(user_id)
        
        # Busca por similaridade semântica
        docs = vectorstore.similarity_search(query, k=k)
        
        return [doc.page_content for doc in docs]
    
    def clear_vectorstore(self, user_id: str):
        """
        Limpa vectorstore do usuário (memória e disco).
        
        Args:
            user_id: ID do usuário
        """
        import shutil
        
        # Remove da memória
        if user_id in self.user_vectorstores:
            del self.user_vectorstores[user_id]
            print(f"  ✓ Vectorstore removido da memória")
        
        # Remove do disco
        vectorstore_path = f"{self.vectorstore_dir}/{user_id}"
        if os.path.exists(vectorstore_path):
            shutil.rmtree(vectorstore_path)
            print(f"  ✓ Vectorstore deletado do disco")
    
    def _get_or_create_vectorstore(self, user_id: str) -> FAISS:
        """
        Obtém vectorstore existente ou cria novo.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Instância FAISS do vectorstore
        """
        # Retorna do cache se já carregado
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
        
        # Cria novo vectorstore
        vectorstore = self._create_new_vectorstore(user_id)
        self.user_vectorstores[user_id] = vectorstore
        
        print(f"✅ Novo vectorstore criado para usuário {user_id}")
        return vectorstore
    
    def _create_new_vectorstore(self, user_id: str) -> FAISS:
        """
        Cria novo vectorstore para usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Nova instância FAISS
        """
        # Cria com documento inicial
        initial_doc = f"Início da conversa com o usuário {user_id} em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        vectorstore = FAISS.from_texts(
            [initial_doc],
            self.embeddings,
            metadatas=[{
                "timestamp": datetime.now().isoformat(), 
                "type": "system"
            }]
        )
        
        # Salva no disco
        vectorstore_path = f"{self.vectorstore_dir}/{user_id}"
        vectorstore.save_local(vectorstore_path)
        
        return vectorstore
