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
import json
import os

try:
    # Usa wrapper local do cliente OpenAI, se disponível
    from libs.OpenAI import client as openai_client
except Exception:
    openai_client = None


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


def generate_dynamic_reading_challenge(nivel: str, exercicio_num: int = 1) -> Dict:
    """
    Gera dinamicamente um desafio de leitura via GPT conforme o nível do aluno.

    Regras por nível:
    - iniciante: exatamente UMA palavra simples (ex: "CASA", "SOL").
    - intermediário: 3 a 6 palavras básicas do cotidiano (em uma linha, separadas por espaço).
    - avançado: 1 a 2 frases MUITO curtas e simples (no total até ~16 palavras).

    Returns:
        Dict com {"titulo", "texto", "dificuldade", "palavras_chave"}
    """
    if openai_client is None:
        # Sem cliente OpenAI disponível, faz fallback
        return get_reading_text(nivel, exercicio_num)

    nivel_norm = (nivel or "iniciante").lower()
    if "avanc" in nivel_norm:
        nivel_norm = "avançado"
    elif "inter" in nivel_norm:
        nivel_norm = "intermediário"
    else:
        nivel_norm = "iniciante"

    if nivel_norm == "iniciante":
        regras = (
            "Crie exatamente UMA palavra simples em português, em CAIXA ALTA, sem números e sem pontuação. "
            "Exemplos de estilo: 'CASA', 'SOL', 'PATO', 'BOLA'."
        )
        dificuldade = 1
        titulo_padrao = "Palavra do Dia"
    elif nivel_norm == "intermediário":
        regras = (
            "Crie UMA LINHA com 3 a 6 palavras básicas do cotidiano, separadas por espaço, em português. "
            "Use palavras curtas e comuns (ex: 'casa bola gato sol livro'). Não use números."
        )
        dificuldade = 2
        titulo_padrao = "Palavras Básicas"
    else:  # avançado
        regras = (
            "Crie um texto MUITO curto em português com 1 ou 2 frases simples, totalizando no máximo 16 palavras. "
            "Frases curtas, vocabulário fácil, temas do cotidiano."
        )
        dificuldade = 3
        titulo_padrao = "Leitura Simples"

    system = (
        "Você é uma assistente de alfabetização. Gere conteúdos MUITO simples, amigáveis e adequados a crianças. "
        "Responda SOMENTE em JSON válido, sem texto extra."
    )
    user = (
        f"Nível: {nivel_norm}. {regras} \n\n"
        "Requisitos de saída (JSON):\n"
        "{\n"
        "  \"titulo\": string (um título curto e amigável),\n"
        "  \"texto\": string,\n"
        "  \"dificuldade\": number (1 para iniciante, 2 para intermediário, 3 para avançado),\n"
        "  \"palavras_chave\": string[] (lista de 3 a 8 palavras relevantes, todas em minúsculas)\n"
        "}\n\n"
        "Observações:\n"
        "- Use apenas caracteres em português.\n"
        "- NUNCA inclua explicações fora do JSON.\n"
    )

    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = resp.choices[0].message.content if resp.choices else "{}"
        # Tenta isolar JSON se vier algo extra
        json_str = _extract_json(content)
        data = json.loads(json_str)

        # Saneamento básico
        titulo = str(data.get("titulo") or titulo_padrao).strip()
        texto = str(data.get("texto") or "").strip()
        palavras_chave = data.get("palavras_chave") or []
        if not isinstance(palavras_chave, list):
            palavras_chave = []

        # Garantias mínimas por nível
        if nivel_norm == "iniciante":
            # Texto deve ser uma única palavra
            texto = texto.replace("\n", " ").strip()
            partes = texto.split()
            if len(partes) != 1:
                # fallback simples: pega a primeira palavra válida
                texto = partes[0] if partes else "SOL"
        elif nivel_norm == "intermediário":
            # Entre 3 e 6 palavras
            palavras = texto.replace("\n", " ").split()
            if len(palavras) < 3:
                palavras = (palavras + ["casa", "bola", "gato"])[:3]
            elif len(palavras) > 6:
                palavras = palavras[:6]
            texto = " ".join(palavras)
        else:
            # 1-2 frases, máx ~16 palavras
            palavras = texto.replace("\n", " ").split()
            if len(palavras) == 0:
                texto = "Eu leio um livro."
            elif len(palavras) > 16:
                texto = " ".join(palavras[:16]).strip()

        return {
            "titulo": titulo or titulo_padrao,
            "texto": texto,
            "dificuldade": dificuldade,
            "palavras_chave": palavras_chave[:8],
        }
    except Exception:
        # Em caso de qualquer falha, volta para versão estática
        return get_reading_text(nivel_norm, exercicio_num)


def _extract_json(text: str) -> str:
    """Extrai o primeiro bloco JSON válido de um texto qualquer."""
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    # Busca pelo primeiro { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    # Fallback
    return "{}"


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
