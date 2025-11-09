"""
Script para limpar dados de usuários específicos
"""
import os
import shutil
import sys

def limpar_usuario(user_id):
    """Limpa todos os dados de um usuário"""
    base_dir = "storage/conversations"
    
    print(f"🗑️ Limpando dados do usuário: {user_id}")
    
    # Remove vectorstore
    vectorstore_path = f"{base_dir}/vectorstores/{user_id}"
    if os.path.exists(vectorstore_path):
        shutil.rmtree(vectorstore_path)
        print(f"  ✓ Vectorstore deletado")
    
    # Remove histórico
    history_file = f"{base_dir}/histories/{user_id}.json"
    if os.path.exists(history_file):
        os.remove(history_file)
        print(f"  ✓ Histórico deletado")
    
    # Remove estado
    state_file = f"{base_dir}/states/{user_id}.json"
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"  ✓ Estado deletado")
    
    print(f"✅ Usuário {user_id} limpo com sucesso!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_id = sys.argv[1].split("@")[0]  # Remove @c.us se tiver
    else:
        user_id = "558388083711"  # Padrão
    
    limpar_usuario(user_id)
