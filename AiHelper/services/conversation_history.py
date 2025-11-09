"""
Módulo de Gerenciamento de Histórico de Conversas

Responsável por manter histórico persistente de mensagens.
Funcionalidades:
- Salvar mensagens em JSON
- Carregar histórico do disco
- Gerenciar cache em memória
- Limpar histórico de usuário

Autor: Equipe Apo.IA
Data: Novembro 2024
"""

import os
import json
from typing import Dict, List
from datetime import datetime


class ConversationHistoryManager:
    """
    Gerenciador de histórico de conversas.
    
    Mantém registro persistente de todas as mensagens
    trocadas com cada usuário.
    """
    
    def __init__(self, history_dir: str = "storage/conversations/histories"):
        """
        Inicializa gerenciador de histórico.
        
        Args:
            history_dir: Diretório para salvar históricos
        """
        self.history_dir = history_dir
        self.user_histories: Dict[str, List[Dict]] = {}  # Cache em memória
        
        # Cria diretório se não existir
        os.makedirs(self.history_dir, exist_ok=True)
    
    def add_message(self, user_id: str, message: str, is_user: bool = True):
        """
        Adiciona mensagem ao histórico.
        
        Args:
            user_id: ID do usuário
            message: Conteúdo da mensagem
            is_user: True se mensagem do usuário, False se da IA
        """
        # Carrega histórico se não está em cache
        if user_id not in self.user_histories:
            self.user_histories[user_id] = self._load_user_history(user_id)
        
        # Adiciona nova mensagem
        timestamp = datetime.now().isoformat()
        role = "user" if is_user else "assistant"
        
        self.user_histories[user_id].append({
            "role": role,
            "content": message,
            "timestamp": timestamp
        })
        
        # Persiste no disco
        self._save_user_history(user_id)
    
    def get_history(self, user_id: str, limit: int = None) -> List[Dict]:
        """
        Obtém histórico de conversas do usuário.
        
        Args:
            user_id: ID do usuário
            limit: Quantidade máxima de mensagens (None = todas)
            
        Returns:
            Lista de mensagens [{role, content, timestamp}, ...]
        """
        # Carrega histórico se não está em cache
        if user_id not in self.user_histories:
            self.user_histories[user_id] = self._load_user_history(user_id)
        
        history = self.user_histories[user_id]
        
        if limit:
            return history[-limit:]
        return history
    
    def clear_history(self, user_id: str):
        """
        Limpa histórico do usuário (memória e disco).
        
        Args:
            user_id: ID do usuário
        """
        # Remove da memória
        if user_id in self.user_histories:
            del self.user_histories[user_id]
            print(f"  ✓ Histórico removido da memória")
        
        # Remove do disco
        history_file = f"{self.history_dir}/{user_id}.json"
        if os.path.exists(history_file):
            os.remove(history_file)
            print(f"  ✓ Histórico deletado do disco")
    
    def _load_user_history(self, user_id: str) -> List[Dict]:
        """
        Carrega histórico do disco.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de mensagens
        """
        history_file = f"{self.history_dir}/{user_id}.json"
        
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return []
    
    def _save_user_history(self, user_id: str):
        """
        Salva histórico no disco.
        
        Args:
            user_id: ID do usuário
        """
        history_file = f"{self.history_dir}/{user_id}.json"
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(
                self.user_histories.get(user_id, []), 
                f, 
                ensure_ascii=False, 
                indent=2
            )
