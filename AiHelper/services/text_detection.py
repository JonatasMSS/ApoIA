"""
Módulo de Detecção de Informações em Texto

Responsável por extrair informações estruturadas de mensagens de texto usando regex.
Funcionalidades:
- Detecção de nome e idade
- Extração de dados pessoais
- Validação de padrões textuais

Autor: Equipe Apo.IA
Data: Novembro 2024
"""

import re
from typing import Dict, Optional


def detect_name_and_age(user_message: str) -> Dict[str, Optional[any]]:
    """
    Detecta nome e idade na mensagem do usuário usando regex.
    
    Estratégia:
    1. Idade: Busca números entre 1-120 com contexto
    2. Nome: Busca palavras capitalizadas com padrões específicos
    3. Evita falsos positivos (palavras comuns)
    
    Padrões suportados:
    - "Meu nome é João e tenho 25 anos"
    - "João, 25 anos"
    - "Sou a Maria e tenho 30"
    - "Pedro 45"
    
    Args:
        user_message: Mensagem do usuário
        
    Returns:
        Dict com {nome: str|None, idade: int|None}
    """
    print(f"🔍 Detectando nome e idade em: '{user_message}'")
    
    # ===== DETECÇÃO DE IDADE =====
    idade = _detect_age(user_message)
    
    # ===== DETECÇÃO DE NOME =====
    nome = _detect_name(user_message)
    
    # Log de falhas
    if not nome:
        print(f"  ✗ Nome NÃO encontrado")
    if not idade:
        print(f"  ✗ Idade NÃO encontrada")
    
    return {"nome": nome, "idade": idade}


def _detect_age(user_message: str) -> Optional[int]:
    """
    Detecta idade na mensagem.
    
    Args:
        user_message: Mensagem do usuário
        
    Returns:
        Idade detectada (int) ou None
    """
    idade_patterns = [
        r'\b(\d{1,3})\s*anos?\b',    # "25 anos" ou "25 ano"
        r'\btenho\s+(\d{1,3})\b',     # "tenho 25"
        r'\b(\d{1,3})\s*$',           # número no final da frase
        r'^\s*(\d{1,3})\s*$'          # apenas o número
    ]
    
    for pattern in idade_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            idade_temp = int(match.group(1))
            # Valida range realista
            if 1 <= idade_temp <= 120:
                print(f"  ✓ Idade encontrada: {idade_temp}")
                return idade_temp
    
    return None


def _detect_name(user_message: str) -> Optional[str]:
    """
    Detecta nome na mensagem.
    
    Args:
        user_message: Mensagem do usuário
        
    Returns:
        Nome detectado (str) ou None
    """
    nome_patterns = [
        # Padrões explícitos com verbos (maior confiança)
        r'(?:me chamo|meu nome é|nome é|eu sou o|eu sou a|sou o|sou a|sou)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)\s*(?:e\s+|,|$)',
        # Nome seguido de contexto de idade
        r'([A-Za-zÀ-ÿ]{3,})\s+(?:e\s+tenho|,\s*tenho)',
        # Nome capitalizado no início
        r'^([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)\s*(?:e\s+|,|$)',
        # Palavra capitalizada isolada
        r'^\s*([A-Z][a-zà-ÿ]{2,})\s*$',
        # Qualquer palavra capitalizada (menor confiança)
        r'\b([A-Z][a-zà-ÿ]{2,})\b'
    ]
    
    # Palavras que NÃO são nomes
    palavras_ignorar = [
        'Oi', 'Olá', 'Bom', 'Boa', 'Tenho', 'Anos', 'Ano', 
        'Meu', 'Minha', 'Nome', 'Idade', 'Sou', 'E'
    ]
    
    for pattern in nome_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            nome_temp = match.group(1).strip()
            # Capitaliza corretamente (cada palavra)
            nome_temp = ' '.join(word.capitalize() for word in nome_temp.split())
            
            # Valida: não é palavra comum e tem tamanho mínimo
            if nome_temp not in palavras_ignorar and len(nome_temp) > 1:
                print(f"  ✓ Nome encontrado: {nome_temp}")
                return nome_temp
    
    return None
