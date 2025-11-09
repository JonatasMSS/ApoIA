"""
Módulo de Avaliação de Alfabetização

Responsável por analisar e avaliar o nível de alfabetização dos usuários.
Funcionalidades:
- Análise de teste de leitura
- Classificação de nível (iniciante/intermediário/avançado)
- Cálculo de taxa de acerto

Autor: Equipe Apo.IA
Data: Novembro 2024
"""

from typing import Dict, List


def analyze_reading_level(user_response: str, expected_words: List[str]) -> Dict:
    """
    Analisa nível de alfabetização baseado no teste de leitura.
    
    Processo:
    1. Compara palavras ditas vs esperadas
    2. Calcula taxa de acerto
    3. Classifica em níveis
    
    Classificação:
    - ≥80%: Avançado (lê bem)
    - ≥50%: Intermediário (lê com dificuldade)
    - <50%: Iniciante (pouca ou nenhuma leitura)
    
    Args:
        user_response: Resposta do usuário (palavras lidas)
        expected_words: Palavras que estavam na imagem
        
    Returns:
        Dict com {nivel, acertos, total, taxa_acerto}
    """
    # Normaliza para comparação
    user_words = user_response.lower().split()
    expected_set = set(w.lower() for w in expected_words)
    
    # Conta acertos (palavras corretas mencionadas)
    acertos = sum(1 for word in user_words if word in expected_set)
    total = len(expected_words)
    taxa_acerto = (acertos / total * 100) if total > 0 else 0
    
    # Classifica nível baseado na taxa de acerto
    nivel = _classify_level(taxa_acerto)
    
    return {
        "nivel": nivel,
        "acertos": acertos,
        "total": total,
        "taxa_acerto": taxa_acerto
    }


def _classify_level(taxa_acerto: float) -> str:
    """
    Classifica nível de alfabetização baseado na taxa de acerto.
    
    Args:
        taxa_acerto: Porcentagem de acerto (0-100)
        
    Returns:
        Nível classificado: "avançado", "intermediário" ou "iniciante"
    """
    if taxa_acerto >= 80:
        return "avançado"
    elif taxa_acerto >= 50:
        return "intermediário"
    else:
        return "iniciante"


def get_test_words(nivel: str = "basico") -> List[str]:
    """
    Retorna lista de palavras para teste baseado no nível.
    
    Args:
        nivel: Nível do teste ("basico", "intermediario", "avancado")
        
    Returns:
        Lista de palavras para o teste
    """
    palavras_por_nivel = {
        "basico": ["CASA", "SOL", "PATO", "BOLA"],
        "intermediario": ["ESCOLA", "CACHORRO", "BANANA", "LIVRO"],
        "avancado": ["BIBLIOTECA", "COMPUTADOR", "TELEVISÃO", "BICICLETA"]
    }
    
    return palavras_por_nivel.get(nivel, palavras_por_nivel["basico"])


def generate_test_image_prompt(words: List[str]) -> str:
    """
    Gera prompt otimizado para DALL-E 3 criar imagem de teste.
    
    Args:
        words: Lista de palavras para incluir na imagem
        
    Returns:
        Prompt detalhado para geração da imagem
    """
    prompt = (
        f"Crie uma imagem educativa e clara para alfabetização infantil. "
        f"Mostre {len(words)} palavras simples escritas em letras GRANDES, COLORIDAS e bem legíveis "
        f"(fonte tipo Comic Sans ou similar, amigável e fácil de ler). "
        f"As palavras devem estar dispostas verticalmente ou em uma grade 2x2. "
        f"Use cores vibrantes diferentes para cada palavra. "
        f"Adicione pequenos ícones ilustrativos coloridos ao lado de cada palavra "
        f"para facilitar o reconhecimento. "
        f"As palavras são: {', '.join(words)}. "
        f"Fundo branco ou muito claro para boa legibilidade. "
        f"Estilo alegre e motivador."
    )
    
    return prompt
