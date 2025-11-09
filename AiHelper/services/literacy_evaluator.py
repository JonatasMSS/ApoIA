"""
Módulo de Avaliação de Alfabetização

Responsável por analisar e avaliar o nível de alfabetização dos usuários.
Funcionalidades:
- Análise de teste de leitura
- Classificação de nível (iniciante/intermediário/avançado)
- Cálculo de taxa de acerto
- Geração de imagens de teste com PIL

Autor: Equipe Apo.IA
Data: Novembro 2024
"""

from typing import Dict, List
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import string
import unicodedata


def _normalize_word(word: str) -> str:
    """
    Normaliza uma palavra removendo pontuação e acentos.
    
    Args:
        word: Palavra para normalizar
        
    Returns:
        Palavra normalizada (lowercase, sem pontuação, sem acentos)
    """
    # Remove pontuação
    word = word.translate(str.maketrans('', '', string.punctuation))
    # Lowercase
    word = word.lower()
    # Remove acentos
    word = unicodedata.normalize('NFD', word)
    word = ''.join(c for c in word if unicodedata.category(c) != 'Mn')
    return word.strip()


def analyze_reading_level(user_response: str, expected_words: List[str]) -> Dict:
    """
    Analisa nível de alfabetização baseado no teste de leitura.
    
    Processo:
    1. Normaliza palavras (remove pontuação e acentos)
    2. Compara palavras ditas vs esperadas
    3. Calcula taxa de acerto
    4. Classifica em níveis
    
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
    # Normaliza palavras do usuário (remove pontuação, acentos)
    user_words_raw = user_response.split()
    user_words = [_normalize_word(w) for w in user_words_raw if _normalize_word(w)]
    
    # Normaliza palavras esperadas
    expected_set = set(_normalize_word(w) for w in expected_words)
    
    # Debug info
    print(f"   🔍 Palavras do usuário normalizadas: {user_words}")
    print(f"   🎯 Palavras esperadas normalizadas: {expected_set}")
    
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


def generate_test_image(words: List[str]) -> str:
    """
    Gera uma imagem de teste de alfabetização com as palavras.
    Usa PIL para garantir texto perfeito e legível.
    
    Args:
        words: Lista de palavras para incluir na imagem
        
    Returns:
        String base64 da imagem PNG gerada
    """
    # Configurações da imagem
    img_width = 1024
    img_height = 1024
    background_color = (255, 255, 255)  # Branco
    
    # Cores vibrantes para cada palavra
    colors = [
        (220, 20, 60),    # Vermelho
        (30, 144, 255),   # Azul
        (50, 205, 50),    # Verde
        (255, 140, 0),    # Laranja
        (138, 43, 226),   # Roxo
        (255, 20, 147),   # Pink
    ]
    
    # Criar imagem
    img = Image.new('RGB', (img_width, img_height), background_color)
    draw = ImageDraw.Draw(img)
    
    # Tentar carregar fonte, senão usa padrão
    try:
        # Fonte grande e bold
        font = ImageFont.truetype("arial.ttf", 120)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 120)
        except:
            # Fallback para fonte padrão (menor)
            font = ImageFont.load_default()
    
    # Calcular posições para centralizar as palavras
    y_start = 150
    y_spacing = 200
    
    # Desenhar cada palavra
    for i, word in enumerate(words):
        color = colors[i % len(colors)]
        
        # Calcular posição X para centralizar
        # Use textbbox para obter as dimensões
        bbox = draw.textbbox((0, 0), word, font=font)
        text_width = bbox[2] - bbox[0]
        x = (img_width - text_width) // 2
        y = y_start + (i * y_spacing)
        
        # Desenhar sombra (outline) para melhor legibilidade
        shadow_offset = 3
        draw.text((x + shadow_offset, y + shadow_offset), word, fill=(200, 200, 200), font=font)
        
        # Desenhar texto principal
        draw.text((x, y), word, fill=color, font=font)
    
    # Converter para base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return img_base64


def generate_reading_text_image(titulo: str, texto: str) -> str:
    """
    Gera uma imagem com texto de leitura formatado.
    Usa PIL para garantir texto perfeito e legível.
    
    Args:
        titulo: Título do texto
        texto: Texto completo para exibir
        
    Returns:
        String base64 da imagem PNG gerada
    """
    # Configurações da imagem
    img_width = 1024
    img_height = 1024
    background_color = (255, 255, 255)  # Branco
    title_color = (220, 20, 60)  # Vermelho para título
    text_color = (50, 50, 50)  # Cinza escuro para texto
    
    # Criar imagem
    img = Image.new('RGB', (img_width, img_height), background_color)
    draw = ImageDraw.Draw(img)
    
    # Tentar carregar fontes
    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 60)  # Bold para título
        font_text = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 45)  # Normal para texto
    except:
        try:
            font_title = ImageFont.truetype("arial.ttf", 60)
            font_text = ImageFont.truetype("arial.ttf", 45)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
    
    # Desenhar título centralizado no topo
    bbox_title = draw.textbbox((0, 0), titulo, font=font_title)
    title_width = bbox_title[2] - bbox_title[0]
    x_title = (img_width - title_width) // 2
    y_title = 80
    
    # Sombra do título
    draw.text((x_title + 2, y_title + 2), titulo, fill=(200, 200, 200), font=font_title)
    # Título
    draw.text((x_title, y_title), titulo, fill=title_color, font=font_title)
    
    # Desenhar linha separadora
    line_y = y_title + 80
    draw.line([(150, line_y), (img_width - 150, line_y)], fill=(200, 200, 200), width=3)
    
    # Quebrar texto em linhas (máximo ~30 caracteres por linha para legibilidade)
    palavras = texto.split()
    linhas = []
    linha_atual = ""
    
    for palavra in palavras:
        if len(linha_atual + palavra) < 35:
            linha_atual += palavra + " "
        else:
            linhas.append(linha_atual.strip())
            linha_atual = palavra + " "
    if linha_atual:
        linhas.append(linha_atual.strip())
    
    # Desenhar texto linha por linha
    y_text = line_y + 80
    line_spacing = 70
    margin_x = 100
    
    for linha in linhas:
        draw.text((margin_x, y_text), linha, fill=text_color, font=font_text)
        y_text += line_spacing
    
    # Converter para base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return img_base64


def generate_test_image_prompt(words: List[str]) -> str:
    """
    DEPRECATED: Mantido para compatibilidade.
    Use generate_test_image() para gerar imagens com texto perfeito.
    
    Args:
        words: Lista de palavras para incluir na imagem
        
    Returns:
        Prompt detalhado para geração da imagem
    """
    prompt = (
        f"Text only, no images or drawings. "
        f"White background. "
        f"Write these {len(words)} Portuguese words in large, bold, colorful letters, one per line: "
        f"{', '.join(words)}"
    )
    
    return prompt
