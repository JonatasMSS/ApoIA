"""
Módulo de Gerenciamento de Estado do Usuário

Responsável por persistir e gerenciar o estado da conversa de cada usuário.
Funcionalidades:
- Carregar/salvar estado do usuário
- Gerenciar fases da conversa
- Controlar dados coletados (nome, idade, nível)
- Reset automático de conversas antigas

Autor: Equipe Apo.IA
Data: Novembro 2024
"""

import os
import json
from typing import Dict
from datetime import datetime, timedelta


class UserStateManager:
    """
    Gerenciador de estado do usuário.
    
    Responsável por persistir informações da conversa:
    - Fase atual
    - Dados pessoais (nome, idade)
    - Avaliação de alfabetização
    - Timestamps de acesso
    """
    
    def __init__(self, state_dir: str = "storage/conversations/states"):
        """
        Inicializa gerenciador de estado.
        
        Args:
            state_dir: Diretório para salvar estados
        """
        self.state_dir = state_dir
        self.user_states: Dict[str, Dict] = {}  # Cache em memória
        
        # Cria diretório se não existir
        os.makedirs(self.state_dir, exist_ok=True)
    
    def get_user_state(self, user_id: str) -> Dict:
        """
        Obtém estado atual do usuário (com cache).
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict com estado atual
        """
        # Carrega do cache ou disco
        if user_id not in self.user_states:
            self.user_states[user_id] = self._load_user_state(user_id)
        
        state = self.user_states[user_id]
        
        # GARANTIA: Fase inicial sempre com dados limpos
        if state["fase"] == "inicial":
            state["nome"] = None
            state["idade"] = None
            state["nivel_alfabetizacao"] = None
            state["palavras_teste"] = []
            state["acertos"] = 0
            state["total_testes"] = 0
        
        return state
    
    def save_user_state(self, user_id: str):
        """
        Salva estado do usuário em disco.
        
        Args:
            user_id: ID do usuário
        """
        state_file = f"{self.state_dir}/{user_id}.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(
                self.user_states.get(user_id, {}), 
                f, 
                ensure_ascii=False, 
                indent=2
            )
    
    def clear_user_state(self, user_id: str):
        """
        Limpa estado do usuário (memória e disco).
        
        Args:
            user_id: ID do usuário
        """
        # Remove da memória
        if user_id in self.user_states:
            del self.user_states[user_id]
            print(f"  ✓ Estado removido da memória")
        
        # Remove do disco
        state_file = f"{self.state_dir}/{user_id}.json"
        if os.path.exists(state_file):
            os.remove(state_file)
            print(f"  ✓ Estado deletado do disco")
    
    def _load_user_state(self, user_id: str) -> Dict:
        """
        Carrega estado do usuário do disco.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict com estado do usuário
        """
        state_file = f"{self.state_dir}/{user_id}.json"
        
        # Estado padrão para novo usuário
        default_state = self._get_default_state()
        
        # Tenta carregar estado existente
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Verifica timeout de conversa (24 horas)
            if self._is_conversation_expired(state):
                print(f"⚠️ Conversa antiga detectada (>24h). Resetando estado.")
                return default_state
            
            # Atualiza timestamp de último acesso
            state["ultimo_acesso"] = datetime.now().isoformat()
            return state
        
        return default_state
    
    def _get_default_state(self) -> Dict:
        """
        Retorna estado padrão para novo usuário.
        
        Returns:
            Dict com estado inicial
        """
        return {
            "fase": "inicial",
            "nome": None,
            "idade": None,
            "nivel_alfabetizacao": None,
            "palavras_teste": [],
            "acertos": 0,
            "total_testes": 0,
            "ultimo_acesso": datetime.now().isoformat()
        }
    
    def _is_conversation_expired(self, state: Dict) -> bool:
        """
        Verifica se a conversa está expirada (>24h sem atividade).
        
        Args:
            state: Estado do usuário
            
        Returns:
            True se expirada, False caso contrário
        """
        if "ultimo_acesso" not in state:
            return False
        
        try:
            ultimo_acesso = datetime.fromisoformat(state["ultimo_acesso"])
            tempo_decorrido = datetime.now() - ultimo_acesso
            return tempo_decorrido > timedelta(hours=24)
        except:
            return False
