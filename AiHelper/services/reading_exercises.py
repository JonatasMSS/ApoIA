"""
Módulo de Exercícios de Leitura

Responsável por gerar e avaliar exercícios de leitura em voz alta.
Funcionalidades:
- Geração de textos simples adaptados ao nível
- Comparação entre texto esperado e lido
- Identificação de erros gramaticais e semânticos
- Feedback construtivo

Autor: Equipe Apo.IA
Data: Novembro 2024
"""

from typing import Dict, List, Tuple
import difflib
import re


def get_reading_text(nivel: str, exercicio_num: int = 1) -> Dict:
    """
    Retorna um texto de leitura baseado no nível do usuário.
    
    Args:
        nivel: Nível do usuário ("iniciante", "intermediário", "avançado")
        exercicio_num: Número do exercício (para variar os textos)
        
    Returns:
        Dict com {texto, titulo, dificuldade, palavras_chave}
    """
    textos_por_nivel = {
        "iniciante": [
            {
                "titulo": "O Sol e a Lua",
                "texto": "O sol brilha de dia. A lua brilha de noite. O sol é quente. A lua é fria.",
                "dificuldade": 1,
                "palavras_chave": ["sol", "lua", "dia", "noite", "quente", "fria"]
            },
            {
                "titulo": "Minha Casa",
                "texto": "Eu tenho uma casa. A casa tem porta. A casa tem janela. Eu gosto da minha casa.",
                "dificuldade": 1,
                "palavras_chave": ["casa", "porta", "janela", "gosto"]
            },
            {
                "titulo": "O Gato",
                "texto": "O gato é bonito. O gato bebe leite. O gato gosta de brincar. Eu amo meu gato.",
                "dificuldade": 1,
                "palavras_chave": ["gato", "bonito", "leite", "brincar", "amo"]
            }
        ],
        "intermediário": [
            {
                "titulo": "O Dia na Escola",
                "texto": "Todos os dias eu vou para a escola. Na escola eu aprendo a ler e escrever. Minha professora é muito legal. Eu gosto de estudar com meus amigos.",
                "dificuldade": 2,
                "palavras_chave": ["escola", "aprendo", "ler", "escrever", "professora", "estudar", "amigos"]
            },
            {
                "titulo": "Meu Final de Semana",
                "texto": "No fim de semana eu gosto de brincar. Eu jogo bola com meus amigos. Também ajudo minha mãe em casa. É muito divertido.",
                "dificuldade": 2,
                "palavras_chave": ["fim de semana", "brincar", "jogo", "bola", "ajudo", "mãe", "divertido"]
            },
            {
                "titulo": "Meu Animal Favorito",
                "texto": "Meu animal favorito é o cachorro. Os cachorros são fiéis e brincam muito. Eles gostam de passear e correr no parque. Eu quero ter um cachorro.",
                "dificuldade": 2,
                "palavras_chave": ["animal", "cachorro", "fiéis", "passear", "correr", "parque"]
            }
        ],
        "avançado": [
            {
                "titulo": "A Importância da Leitura",
                "texto": "A leitura é fundamental para o desenvolvimento pessoal. Quando lemos, aprendemos coisas novas e expandimos nossa imaginação. Os livros nos levam a lugares diferentes e nos apresentam pessoas interessantes. Por isso, devemos ler todos os dias.",
                "dificuldade": 3,
                "palavras_chave": ["leitura", "fundamental", "desenvolvimento", "aprendemos", "imaginação", "expandimos"]
            },
            {
                "titulo": "Cuidando do Meio Ambiente",
                "texto": "É importante cuidar do meio ambiente. Podemos fazer isso reciclando o lixo, economizando água e plantando árvores. Quando cuidamos da natureza, estamos cuidando do nosso futuro e do planeta onde vivemos.",
                "dificuldade": 3,
                "palavras_chave": ["meio ambiente", "reciclando", "economizando", "plantando", "natureza", "futuro", "planeta"]
            }
        ]
    }
    
    # Pega textos do nível
    textos = textos_por_nivel.get(nivel, textos_por_nivel["iniciante"])
    
    # Seleciona texto baseado no número do exercício
    index = (exercicio_num - 1) % len(textos)
    
    return textos[index]


def analyze_reading_attempt(texto_esperado: str, texto_lido: str) -> Dict:
    """
    Analisa a tentativa de leitura do usuário comparando com o texto esperado.
    
    Args:
        texto_esperado: Texto que deveria ser lido
        texto_lido: Texto transcrito do áudio do usuário
        
    Returns:
        Dict com análise detalhada dos erros e acertos
    """
    # Normaliza textos para comparação
    esperado_normalizado = _normalize_text(texto_esperado)
    lido_normalizado = _normalize_text(texto_lido)
    
    # Divide em palavras
    palavras_esperadas = esperado_normalizado.split()
    palavras_lidas = lido_normalizado.split()
    
    # Calcula similaridade
    similaridade = difflib.SequenceMatcher(None, palavras_esperadas, palavras_lidas).ratio()
    similaridade_percent = similaridade * 100
    
    # Identifica diferenças
    erros = _identificar_erros(palavras_esperadas, palavras_lidas)
    
    # Classifica desempenho
    if similaridade_percent >= 90:
        avaliacao = "excelente"
        feedback = "Parabéns! Você leu muito bem! 🎉"
    elif similaridade_percent >= 70:
        avaliacao = "bom"
        feedback = "Muito bem! Você leu quase tudo certo! Continue praticando! 👏"
    elif similaridade_percent >= 50:
        avaliacao = "regular"
        feedback = "Bom esforço! Vamos praticar mais para melhorar! 💪"
    else:
        avaliacao = "precisa_melhorar"
        feedback = "Não se preocupe! Vamos praticar juntos até você conseguir! 😊"
    
    return {
        "similaridade": round(similaridade_percent, 1),
        "avaliacao": avaliacao,
        "feedback": feedback,
        "total_palavras_esperadas": len(palavras_esperadas),
        "total_palavras_lidas": len(palavras_lidas),
        "erros": erros,
        "acertos": len(palavras_esperadas) - len(erros["palavras_erradas"]) - len(erros["palavras_faltantes"])
    }


def _normalize_text(text: str) -> str:
    """Normaliza texto removendo pontuação e caracteres especiais."""
    import string
    import unicodedata
    
    # Remove pontuação
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Lowercase
    text = text.lower()
    # Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Remove espaços extras
    text = ' '.join(text.split())
    
    return text


def _identificar_erros(esperadas: List[str], lidas: List[str]) -> Dict:
    """
    Identifica erros específicos na leitura.
    
    Returns:
        Dict com {palavras_erradas, palavras_faltantes, palavras_extras}
    """
    esperadas_set = set(esperadas)
    lidas_set = set(lidas)
    
    # Palavras que faltaram
    palavras_faltantes = list(esperadas_set - lidas_set)
    
    # Palavras extras (que não estavam no texto)
    palavras_extras = list(lidas_set - esperadas_set)
    
    # Palavras trocadas (usa difflib para identificar)
    matcher = difflib.SequenceMatcher(None, esperadas, lidas)
    palavras_erradas = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            # Palavra foi trocada
            for i, j in zip(range(i1, i2), range(j1, j2)):
                if i < len(esperadas) and j < len(lidas):
                    palavras_erradas.append({
                        "esperada": esperadas[i],
                        "lida": lidas[j]
                    })
    
    return {
        "palavras_erradas": palavras_erradas,
        "palavras_faltantes": palavras_faltantes[:5],  # Limita a 5 para não sobrecarregar
        "palavras_extras": palavras_extras[:5]
    }


def generate_feedback_message(resultado: Dict, texto_info: Dict) -> str:
    """
    Gera mensagem de feedback detalhada para o usuário.
    
    Args:
        resultado: Resultado da análise de leitura
        texto_info: Informações do texto lido
        
    Returns:
        Mensagem de feedback formatada
    """
    feedback = f"""📖 Resultado da Leitura: "{texto_info['titulo']}"

{resultado['feedback']}

📊 Estatísticas:
• Acertos: {resultado['acertos']}/{resultado['total_palavras_esperadas']} palavras
• Precisão: {resultado['similaridade']}%

"""
    
    # Adiciona detalhes dos erros se houver
    if resultado['erros']['palavras_erradas']:
        feedback += "🔤 Palavras que você trocou:\n"
        for erro in resultado['erros']['palavras_erradas'][:3]:  # Mostra até 3
            feedback += f"   • Você disse '{erro['lida']}' mas era '{erro['esperada']}'\n"
        feedback += "\n"
    
    if resultado['erros']['palavras_faltantes']:
        feedback += "📝 Palavras que você pulou:\n"
        for palavra in resultado['erros']['palavras_faltantes'][:3]:
            feedback += f"   • {palavra}\n"
        feedback += "\n"
    
    # Mensagem de encorajamento
    if resultado['avaliacao'] == "excelente":
        feedback += "🌟 Continue assim! Você está lendo muito bem!"
    elif resultado['avaliacao'] == "bom":
        feedback += "💪 Você está no caminho certo! Mais uma vez?"
    else:
        feedback += "🎯 Vamos praticar este texto mais uma vez? Eu acredito em você!"
    
    return feedback
