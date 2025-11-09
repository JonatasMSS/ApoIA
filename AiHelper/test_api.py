"""
Exemplos de uso das APIs de geração de conteúdo AI
"""

import requests
import json

# URL base da API (ajuste conforme necessário)
BASE_URL = "http://localhost:8000"

def test_dalle_image():
    """Testa a geração de imagem com DALL-E 3"""
    print("\n🖼️  Testando geração de imagem com DALL-E 3...")
    
    payload = {
        "prompt": "Um gato robótico futurista em uma cidade cyberpunk iluminada por neon, estilo fotorrealista",
        "size": "1024x1024",
        "quality": "standard",
        "n": 1
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-image", json=payload)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Imagem gerada com sucesso!")
        print(f"URL: {result['images'][0]['url']}")
        print(f"Prompt revisado: {result['images'][0]['revised_prompt']}")
        
        return result
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_veo_video():
    """Testa a geração de vídeo com Veo 2"""
    print("\n🎬 Testando geração de vídeo com Veo 2...")
    
    payload = {
        "prompt": "Timelapse de nuvens passando sobre montanhas ao pôr do sol, câmera estática",
        "aspect_ratio": "16:9",
        "duration": 5
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-video", json=payload)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Vídeo gerado com sucesso!")
        print(f"Modelo: {result.get('model')}")
        print(f"Mensagem: {result.get('message')}")
        if result.get('video_url'):
            print(f"URL: {result['video_url']}")
        
        return result
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_veo_info():
    """Obtém informações sobre o modelo Veo"""
    print("\n📊 Obtendo informações do Veo 2...")
    
    try:
        response = requests.get(f"{BASE_URL}/veo-info")
        response.raise_for_status()
        
        result = response.json()
        print("✅ Informações obtidas:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def compare_costs():
    """Compara os custos entre diferentes modelos"""
    print("\n💰 Comparação de Custos:")
    print("="*60)
    print("\n📸 DALL-E 3 (OpenAI):")
    print("  • Standard 1024x1024: ~$0.040 por imagem")
    print("  • HD 1024x1024:       ~$0.080 por imagem")
    print("  • HD 1792x1024:       ~$0.120 por imagem")
    
    print("\n🎥 Geração de Vídeo:")
    print("  • Veo 2 (Google):     ~$0.05 - $0.10 por vídeo (8s)")
    print("  • Sora (OpenAI):      ~$0.50 - $1.00 por vídeo (8s)")
    print("\n  💡 Veo 2 é até 10x mais econômico que Sora!")
    print("="*60)

if __name__ == "__main__":
    print("🚀 Iniciando testes da API de Geração AI")
    print("="*60)
    
    # Mostra comparação de custos
    compare_costs()
    
    # Testa informações do Veo
    test_veo_info()
    
    # Descomente as linhas abaixo para testar as APIs de geração
    # (requer chaves de API válidas e consome créditos)
    
    # test_dalle_image()
    # test_veo_video()
    
    print("\n✅ Testes concluídos!")
    print("\n💡 Dica: Descomente as funções de teste no código para")
    print("   testar a geração real de conteúdo (consome créditos)")
