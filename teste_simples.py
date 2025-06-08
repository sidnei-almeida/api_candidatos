import requests
import json
from pprint import pprint

# URL base da API
BASE_URL = "http://localhost:8000"

def print_separador(texto):
    """Imprime um separador com texto"""
    print("\n" + "=" * 80)
    print(f" {texto} ".center(80, "="))
    print("=" * 80)

def teste_endpoint_base():
    """Testa o endpoint raiz da API"""
    print_separador("TESTE DO ENDPOINT RAIZ")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Resposta:")
            pprint(response.json())
            return True
        else:
            print(f"Erro: {response.text}")
            return False
    except Exception as e:
        print(f"Erro ao conectar à API: {str(e)}")
        return False

def teste_analise_texto():
    """Testa a análise de texto"""
    print_separador("TESTE DE ANÁLISE DE TEXTO")
    texto = "O governo federal anunciou hoje novas medidas econômicas para controlar a inflação. O Congresso deve votar a proposta na próxima semana."
    
    try:
        # Enviando o texto no corpo da requisição como JSON
        response = requests.post(
            f"{BASE_URL}/noticias/analisar-texto",
            json={"texto": texto}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Análise do texto:")
            pprint(response.json())
            return True
        else:
            print(f"Erro: {response.text}")
            return False
    except Exception as e:
        print(f"Erro ao analisar texto: {str(e)}")
        return False

def teste_modelos_info():
    """Testa informações dos modelos"""
    print_separador("TESTE DE INFORMAÇÕES DOS MODELOS")
    try:
        response = requests.get(f"{BASE_URL}/modelos/info")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Informações dos modelos:")
            pprint(response.json())
            return True
        else:
            print(f"Erro: {response.text}")
            return False
    except Exception as e:
        print(f"Erro ao obter informações dos modelos: {str(e)}")
        return False

def teste_candidatos():
    """Testa listagem de candidatos"""
    print_separador("TESTE DE LISTAGEM DE CANDIDATOS")
    try:
        response = requests.get(f"{BASE_URL}/noticias/candidatos")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            candidatos = response.json()
            print(f"Candidatos encontrados: {len(candidatos)}")
            if candidatos:
                print("Lista de candidatos:")
                for i, candidato in enumerate(candidatos):
                    print(f"{i+1}. {candidato}")
            return True
        else:
            print(f"Erro: {response.text}")
            return False
    except Exception as e:
        print(f"Erro ao obter candidatos: {str(e)}")
        return False

def teste_noticias():
    """Testa listagem de notícias"""
    print_separador("TESTE DE LISTAGEM DE NOTÍCIAS")
    try:
        response = requests.get(f"{BASE_URL}/noticias/?limit=3")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            noticias = response.json()
            print(f"Notícias encontradas: {len(noticias)}")
            if noticias:
                print("Exemplo de notícia:")
                exemplo = noticias[0]
                print(f"Título: {exemplo.get('titulo', 'N/A')}")
                print(f"Fonte: {exemplo.get('fonte', 'N/A')}")
                print(f"Data: {exemplo.get('data', 'N/A')}")
                print(f"Aspecto: {exemplo.get('aspecto', 'N/A')}")
                print(f"Sentimento: {exemplo.get('sentimento', 'N/A')}")
            return True
        else:
            print(f"Erro: {response.text}")
            return False
    except Exception as e:
        print(f"Erro ao obter notícias: {str(e)}")
        return False

def executar_testes():
    """Executa todos os testes básicos"""
    print_separador("INICIANDO TESTES DA API")
    
    # Contador de testes
    testes_ok = 0
    total_testes = 5
    
    # Executa os testes
    if teste_endpoint_base():
        testes_ok += 1
    
    if teste_analise_texto():
        testes_ok += 1
    
    if teste_modelos_info():
        testes_ok += 1
    
    if teste_candidatos():
        testes_ok += 1
    
    if teste_noticias():
        testes_ok += 1
    
    # Resultado final
    print_separador("RESULTADO DOS TESTES")
    print(f"Testes concluídos com sucesso: {testes_ok}/{total_testes}")
    print(f"Taxa de sucesso: {(testes_ok/total_testes)*100:.1f}%")
    
    if testes_ok == total_testes:
        print("\n✅ TODOS OS TESTES PASSARAM! A API está pronta para implementação.")
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM. Verifique os erros antes de prosseguir.")

if __name__ == "__main__":
    executar_testes() 