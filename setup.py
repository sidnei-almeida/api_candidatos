import nltk
import spacy
import os
import joblib
import json
import requests
from pathlib import Path

def download_file(url, save_path):
    """
    Baixa um arquivo da URL fornecida e salva no caminho especificado
    """
    print(f"Baixando arquivo de {url}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Verifica se a resposta foi bem-sucedida
        
        # Salvar o arquivo
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"✓ Arquivo salvo em {save_path}")
        return True
    except Exception as e:
        print(f"✗ Erro ao baixar arquivo: {str(e)}")
        return False

def setup_environment():
    """
    Configura o ambiente de execução baixando recursos necessários
    """
    print("Configurando ambiente de execução...")
    
    # Obter o diretório atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Baixar recursos do NLTK
    print("Baixando recursos do NLTK...")
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    
    # Verificar se o modelo spaCy está instalado
    try:
        print("Verificando modelo spaCy...")
        nlp = spacy.load("pt_core_news_lg")
        print("Modelo spaCy carregado com sucesso!")
    except:
        print("Instalando modelo spaCy...")
        os.system("python -m spacy download pt_core_news_lg")
    
    # URLs dos modelos e arquivos de dados no GitHub
    modelos_urls = {
        "modelo_aspectos.joblib": "https://github.com/sidnei-almeida/api_candidatos/raw/refs/heads/main/modelo_aspectos.joblib",
        "modelo_sentimentos.joblib": "https://github.com/sidnei-almeida/api_candidatos/raw/refs/heads/main/modelo_sentimentos.joblib",
    }
    
    # Baixar modelos se não existirem localmente
    for filename, url in modelos_urls.items():
        modelo_path = os.path.join(current_dir, filename)
        if not os.path.exists(modelo_path):
            print(f"Baixando modelo {filename} do GitHub...")
            if download_file(url, modelo_path):
                print(f"Modelo {filename} baixado com sucesso!")
            else:
                print(f"Não foi possível baixar {filename}. Criando modelo padrão...")
                # Criar um modelo simples caso os modelos não estejam disponíveis
                if filename == "modelo_aspectos.joblib":
                    from sklearn.pipeline import Pipeline
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    from sklearn.linear_model import LogisticRegression
                    
                    print("Criando modelo de aspectos padrão...")
                    modelo_aspectos = Pipeline([
                        ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
                        ('classifier', LogisticRegression(max_iter=1000))
                    ])
                    # Treinar com dados mínimos
                    X = ["economia brasil", "congresso nacional", "governo federal", "outros assuntos"]
                    y = [0, 1, 2, 3]
                    modelo_aspectos.fit(X, y)
                    joblib.dump(modelo_aspectos, modelo_path)
                    print(f"Modelo de aspectos salvo em {modelo_path}")
                
                elif filename == "modelo_sentimentos.joblib":
                    from sklearn.pipeline import Pipeline
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    from sklearn.linear_model import LogisticRegression
                    
                    print("Criando modelo de sentimentos padrão...")
                    modelo_sentimentos = Pipeline([
                        ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
                        ('classifier', LogisticRegression(max_iter=1000))
                    ])
                    # Treinar com dados mínimos
                    X = ["muito bom", "neutro", "muito ruim"]
                    y = [0, 1, 2]
                    modelo_sentimentos.fit(X, y)
                    joblib.dump(modelo_sentimentos, modelo_path)
                    print(f"Modelo de sentimentos salvo em {modelo_path}")
    
    # Verificar mapeamento de labels
    label_mappings_path = os.path.join(current_dir, "label_mappings.json")
    if not os.path.exists(label_mappings_path):
        print("Criando mapeamento de labels padrão...")
        label_mappings = {
            "aspects": {
                "economia": 0,
                "congresso": 1,
                "governo": 2,
                "outros": 3,
                "neutro": 4
            },
            "sentiments": {
                "positivo": 0,
                "neutro": 1,
                "negativo": 2
            }
        }
        with open(label_mappings_path, 'w', encoding='utf-8') as f:
            json.dump(label_mappings, f, ensure_ascii=False, indent=2)
        print(f"Mapeamento de labels salvo em {label_mappings_path}")
    
    # Criar pasta data se não existir
    data_dir = os.path.join(current_dir, "data")
    if not os.path.exists(data_dir):
        print(f"Criando diretório de dados em {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
    
    # URLs dos arquivos de dados no GitHub
    data_urls = {
        "aspectos_politicos.json": "https://github.com/sidnei-almeida/api_candidatos/raw/refs/heads/main/data/aspectos_politicos.json",
        "candidatos.json": "https://github.com/sidnei-almeida/api_candidatos/raw/refs/heads/main/data/candidatos.json",
        "lexico_politico.json": "https://github.com/sidnei-almeida/api_candidatos/raw/refs/heads/main/data/lexico_politico.json",
        "noticias_cache.csv": "https://github.com/sidnei-almeida/api_candidatos/raw/refs/heads/main/data/noticias_cache.csv"
    }
    
    # Baixar arquivos de dados se não existirem localmente
    for filename, url in data_urls.items():
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            print(f"Baixando arquivo {filename} do GitHub...")
            if download_file(url, file_path):
                print(f"Arquivo {filename} baixado com sucesso!")
            else:
                print(f"Não foi possível baixar {filename}.")
                
                # Criar arquivos padrão vazios caso não seja possível baixar
                if filename == "aspectos_politicos.json":
                    aspectos_politicos = {
                        "congresso": ["legislativo", "congresso", "senado", "câmara", "deputado", "senador"],
                        "economia": ["economia", "inflação", "desemprego", "pib", "dólar", "bolsa"],
                        "governo": ["executivo", "governo", "presidente", "ministro", "ministério", "decreto"],
                        "outros": ["outros", "diversos"]
                    }
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(aspectos_politicos, f, ensure_ascii=False, indent=2)
                    print(f"Arquivo {filename} criado com dados padrão")
                
                elif filename == "candidatos.json":
                    candidatos = ["Lula", "Bolsonaro", "Tarcísio de Freitas", "Cláudio Castro", "Eduardo Leite", "Romeu Zema"]
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(candidatos, f, ensure_ascii=False, indent=2)
                    print(f"Arquivo {filename} criado com dados padrão")
                
                elif filename == "lexico_politico.json":
                    lexico_politico = {
                        "positivo": ["bom", "ótimo", "excelente", "eficiente", "sucesso", "avanço", "progresso"],
                        "negativo": ["ruim", "péssimo", "corrupto", "corrupção", "fraude", "crise", "problema"]
                    }
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(lexico_politico, f, ensure_ascii=False, indent=2)
                    print(f"Arquivo {filename} criado com dados padrão")
                
                elif filename == "noticias_cache.csv":
                    # Criar um CSV vazio com cabeçalho básico
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("titulo,texto,data,fonte,url,aspecto,sentimento,candidatos,regiao,relevancia\n")
                    print(f"Arquivo {filename} criado com cabeçalho padrão")
    
    print("Configuração do ambiente concluída!")

if __name__ == "__main__":
    setup_environment() 