import requests
import json
import time
from pprint import pprint

BASE_URL = "http://localhost:8000"

def test_root():
    """Test the root endpoint"""
    print("\n=== Testando endpoint raiz ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    pprint(response.json())

def test_collect_news():
    """Test collecting news"""
    print("\n=== Testando coleta de notícias ===")
    print("ATENÇÃO: Este teste pode demorar vários minutos. Por favor, aguarde...")
    print("A coleta de notícias está limitada a 1 página por fonte para fins de teste.")
    print("Acompanhe os logs detalhados abaixo:")
    
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/noticias/coletar")
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"Tempo total: {elapsed:.2f} segundos")
        
        result = response.json()
        print(f"\nResumo da coleta:")
        print(f"- Total de notícias coletadas: {result['total_coletadas']}")
        print(f"- Fontes:")
        for fonte, quantidade in result['fontes'].items():
            print(f"  * {fonte}: {quantidade} notícias")
    except Exception as e:
        print(f"Erro durante a coleta de notícias: {str(e)}")
        raise

def test_get_news():
    """Test getting news"""
    print("\n=== Testando listagem de notícias ===")
    
    try:
        response = requests.get(f"{BASE_URL}/noticias/?limit=5")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            noticias = response.json()
            print(f"Total de notícias: {len(noticias)}")
            
            if noticias and len(noticias) > 0:
                print("Exemplo de notícia:")
                pprint(noticias[0])
            else:
                print("Nenhuma notícia encontrada. Execute a coleta de notícias primeiro.")
        else:
            print(f"Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            
    except Exception as e:
        print(f"Erro ao listar notícias: {str(e)}")
        import traceback
        print(traceback.format_exc())

def test_analyze_news():
    """Test news analysis"""
    print("\n=== Testando análise de notícias ===")
    try:
        response = requests.get(f"{BASE_URL}/noticias/analise?limit=3")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                noticias = response.json()
                print(f"Total de notícias analisadas: {len(noticias)}")
                
                if noticias and len(noticias) > 0:
                    print("Exemplo de notícia com análise:")
                    pprint(noticias[0])
                else:
                    print("Nenhuma notícia encontrada para análise.")
            except requests.exceptions.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON: {str(e)}")
                print(f"Conteúdo da resposta: {response.text[:200]}...")
        else:
            print(f"Erro na requisição: {response.status_code}")
            print(f"Conteúdo da resposta: {response.text[:200]}...")
    except Exception as e:
        print(f"Erro ao testar análise de notícias: {str(e)}")
        import traceback
        print(traceback.format_exc())

def test_analyze_text():
    """Test text analysis"""
    print("\n=== Testando análise de texto ===")
    texto = "O governo federal anunciou hoje novas medidas econômicas para controlar a inflação. O Congresso deve votar a proposta na próxima semana."
    
    try:
        response = requests.post(
            f"{BASE_URL}/noticias/analisar-texto",
            json={"texto": texto}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("Análise do texto:")
            pprint(response.json())
        else:
            print(f"Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
    except Exception as e:
        print(f"Erro ao analisar texto: {str(e)}")
        import traceback
        print(traceback.format_exc())

def test_model_predictions():
    """Test model predictions"""
    print("\n=== Testando previsões com modelos ===")
    
    # Texto para teste
    texto = "O governo federal anunciou hoje novas medidas econômicas para controlar a inflação. O Congresso deve votar a proposta na próxima semana."
    
    # Testar previsão completa
    print("1. Testando previsão completa (aspecto e sentimento):")
    try:
        response = requests.post(
            f"{BASE_URL}/modelos/prever", 
            json={"texto": texto, "preprocessar": True}
        )
        print(f"Status: {response.status_code}")
        pprint(response.json())
    except Exception as e:
        print(f"Erro ao fazer previsão completa: {str(e)}")
    
    # Testar previsão de aspecto
    print("\n2. Testando previsão de aspecto:")
    try:
        response = requests.post(
            f"{BASE_URL}/modelos/prever-aspecto", 
            json={"texto": texto, "preprocessar": True}
        )
        print(f"Status: {response.status_code}")
        pprint(response.json())
    except Exception as e:
        print(f"Erro ao fazer previsão de aspecto: {str(e)}")
    
    # Testar previsão de sentimento
    print("\n3. Testando previsão de sentimento:")
    try:
        response = requests.post(
            f"{BASE_URL}/modelos/prever-sentimento", 
            json={"texto": texto, "preprocessar": True}
        )
        print(f"Status: {response.status_code}")
        pprint(response.json())
    except Exception as e:
        print(f"Erro ao fazer previsão de sentimento: {str(e)}")

def test_get_news_by_aspect():
    """Test getting news by aspect"""
    print("\n=== Testando notícias por aspecto ===")
    response = requests.get(f"{BASE_URL}/noticias/aspectos")
    aspectos = response.json()
    
    if not aspectos:
        print("Nenhum aspecto encontrado. Pulando teste.")
        return
        
    aspect = aspectos[0]
    print(f"Buscando notícias do aspecto: {aspect}")
    
    try:
        response = requests.get(f"{BASE_URL}/noticias/por-aspecto/{aspect}?limit=3")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            noticias = response.json()
            print(f"Total de notícias: {len(noticias)}")
            
            if noticias and len(noticias) > 0:
                print("Exemplo de notícia:")
                pprint(noticias[0])
            else:
                print("Nenhuma notícia encontrada para este aspecto.")
        else:
            print(f"Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            
    except Exception as e:
        print(f"Erro ao buscar notícias por aspecto: {str(e)}")
        import traceback
        print(traceback.format_exc())

def test_get_news_by_sentiment():
    """Test getting news by sentiment"""
    print("\n=== Testando notícias por sentimento ===")
    response = requests.get(f"{BASE_URL}/noticias/sentimentos")
    sentimentos = response.json()
    
    if not sentimentos:
        print("Nenhum sentimento encontrado. Pulando teste.")
        return
        
    sentiment = sentimentos[0]
    print(f"Buscando notícias do sentimento: {sentiment}")
    
    try:
        response = requests.get(f"{BASE_URL}/noticias/por-sentimento/{sentiment}?limit=3")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            noticias = response.json()
            print(f"Total de notícias: {len(noticias)}")
            
            if noticias and len(noticias) > 0:
                print("Exemplo de notícia:")
                pprint(noticias[0])
            else:
                print("Nenhuma notícia encontrada para este sentimento.")
        else:
            print(f"Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            
    except Exception as e:
        print(f"Erro ao buscar notícias por sentimento: {str(e)}")
        import traceback
        print(traceback.format_exc())

def test_statistics():
    """Test getting statistics"""
    print("\n=== Testando estatísticas ===")
    response = requests.get(f"{BASE_URL}/noticias/estatisticas")
    print(f"Status: {response.status_code}")
    pprint(response.json())

def test_sources():
    """Test getting sources"""
    print("\n=== Testando fontes ===")
    response = requests.get(f"{BASE_URL}/noticias/fontes")
    print(f"Status: {response.status_code}")
    pprint(response.json())

def test_models_info():
    """Test getting models information"""
    print("\n=== Testando informações dos modelos ===")
    try:
        response = requests.get(f"{BASE_URL}/modelos/info")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                info = response.json()
                print("Informações dos modelos:")
                pprint(info)
            except requests.exceptions.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON: {str(e)}")
                print(f"Conteúdo da resposta: {response.text[:200]}...")
        else:
            print(f"Erro na requisição: {response.status_code}")
            try:
                error_info = response.json()
                print(f"Detalhes do erro: {error_info}")
            except:
                print(f"Conteúdo da resposta: {response.text[:200]}...")
    except Exception as e:
        print(f"Erro ao obter informações dos modelos: {str(e)}")

# Novos testes para candidatos e regiões
def test_get_candidatos():
    """Test getting candidates"""
    print("\n=== Testando listagem de candidatos ===")
    response = requests.get(f"{BASE_URL}/noticias/candidatos")
    print(f"Status: {response.status_code}")
    candidatos = response.json()
    print(f"Total de candidatos detectados: {len(candidatos)}")
    if candidatos:
        print("Candidatos encontrados:")
        pprint(candidatos[:10] if len(candidatos) > 10 else candidatos)  # Limitar a 10 para exibição
    else:
        print("Nenhum candidato encontrado. Execute a coleta de notícias primeiro.")

def test_get_regioes():
    """Test getting regions"""
    print("\n=== Testando listagem de regiões ===")
    response = requests.get(f"{BASE_URL}/noticias/regioes")
    print(f"Status: {response.status_code}")
    regioes = response.json()
    print(f"Total de regiões detectadas: {len(regioes)}")
    if regioes:
        print("Regiões encontradas:")
        pprint(regioes)
    else:
        print("Nenhuma região encontrada. Execute a coleta de notícias primeiro.")

def test_get_news_by_candidato():
    """Test getting news by candidate"""
    print("\n=== Testando notícias por candidato ===")
    response = requests.get(f"{BASE_URL}/noticias/candidatos")
    candidatos = response.json()
    
    if not candidatos:
        print("Nenhum candidato encontrado. Pulando teste.")
        return
        
    candidato = candidatos[0]
    print(f"Buscando notícias sobre o candidato: {candidato}")
    
    try:
        response = requests.get(f"{BASE_URL}/noticias/por-candidato/{candidato}?limit=3")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            noticias = response.json()
            print(f"Total de notícias: {len(noticias)}")
            
            if noticias and len(noticias) > 0:
                print("Exemplo de notícia:")
                pprint(noticias[0])
            else:
                print("Nenhuma notícia encontrada para este candidato.")
        else:
            print(f"Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            
    except Exception as e:
        print(f"Erro ao buscar notícias por candidato: {str(e)}")
        import traceback
        print(traceback.format_exc())

def test_get_news_by_regiao():
    """Test getting news by region"""
    print("\n=== Testando notícias por região ===")
    response = requests.get(f"{BASE_URL}/noticias/regioes")
    regioes = response.json()
    
    if not regioes:
        print("Nenhuma região encontrada. Pulando teste.")
        return
        
    regiao = regioes[0]
    print(f"Buscando notícias da região: {regiao}")
    
    try:
        response = requests.get(f"{BASE_URL}/noticias/por-regiao/{regiao}?limit=3")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            noticias = response.json()
            print(f"Total de notícias: {len(noticias)}")
            
            if noticias and len(noticias) > 0:
                print("Exemplo de notícia:")
                pprint(noticias[0])
            else:
                print("Nenhuma notícia encontrada para esta região.")
        else:
            print(f"Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            
    except Exception as e:
        print(f"Erro ao buscar notícias por região: {str(e)}")
        import traceback
        print(traceback.format_exc())

def test_analise_candidato():
    """Test candidate analysis"""
    print("\n=== Testando análise de candidato ===")
    response = requests.get(f"{BASE_URL}/noticias/candidatos")
    candidatos = response.json()
    
    if not candidatos:
        print("Nenhum candidato encontrado. Pulando teste.")
        return
    
    candidato = candidatos[0]
    print(f"Analisando candidato: {candidato}")
    try:
        response = requests.get(f"{BASE_URL}/noticias/candidato/{candidato}/analise")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            analise = response.json()
            print("Análise do candidato:")
            pprint(analise)
        else:
            print(f"Erro na requisição: {response.status_code}")
            try:
                error_info = response.json()
                print(f"Detalhes do erro: {error_info}")
            except:
                print(f"Conteúdo da resposta: {response.text[:200]}...")
    except Exception as e:
        print(f"Erro ao analisar candidato: {str(e)}")

def test_analise_regiao():
    """Test region analysis"""
    print("\n=== Testando análise de região ===")
    response = requests.get(f"{BASE_URL}/noticias/regioes")
    regioes = response.json()
    
    if not regioes:
        print("Nenhuma região encontrada. Pulando teste.")
        return
    
    regiao = regioes[0]
    print(f"Analisando região: {regiao}")
    try:
        response = requests.get(f"{BASE_URL}/noticias/regiao/{regiao}/analise")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            analise = response.json()
            print("Análise da região:")
            pprint(analise)
        else:
            print(f"Erro na requisição: {response.status_code}")
            try:
                error_info = response.json()
                print(f"Detalhes do erro: {error_info}")
            except:
                print(f"Conteúdo da resposta: {response.text[:200]}...")
    except Exception as e:
        print(f"Erro ao analisar região: {str(e)}")

def test_mapa_temas_regionais():
    """Test regional topics map"""
    print("\n=== Testando mapa de temas regionais ===")
    try:
        response = requests.get(f"{BASE_URL}/noticias/mapa-temas-regionais")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            mapa = response.json()
            print("Mapa de temas regionais:")
            print(f"- Total de regiões: {len(mapa.get('regioes', []))}")
            print(f"- Total de aspectos: {len(mapa.get('aspectos', []))}")
            print(f"- Temas por região: {len(mapa.get('temas_por_regiao', {}))}")
            
            # Mostrar exemplo de uma região se disponível
            if mapa.get('temas_por_regiao') and mapa.get('regioes'):
                exemplo_regiao = list(mapa['temas_por_regiao'].keys())[0] if mapa['temas_por_regiao'] else None
                if exemplo_regiao:
                    print(f"\nExemplo de temas da região {exemplo_regiao}:")
                    pprint(mapa['temas_por_regiao'][exemplo_regiao])
        else:
            print(f"Erro na requisição: {response.status_code}")
            try:
                error_info = response.json()
                print(f"Detalhes do erro: {error_info}")
            except:
                print(f"Conteúdo da resposta: {response.text[:200]}...")
    except Exception as e:
        print(f"Erro ao obter mapa de temas regionais: {str(e)}")

def test_painel_candidatos():
    """Test candidates panel"""
    print("\n=== Testando painel de candidatos ===")
    try:
        response = requests.get(f"{BASE_URL}/noticias/painel-candidatos")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            painel = response.json()
            print("Painel de candidatos:")
            print(f"- Total de candidatos: {len(painel.get('candidatos', {}))}")
            
            # Mostrar comparativo
            if painel.get('comparativo'):
                print("\nComparativo de candidatos:")
                for metrica, valores in painel['comparativo'].items():
                    print(f"- {metrica}: {len(valores)} candidatos")
                
                # Mostrar exemplo de um candidato se disponível
                if painel.get('candidatos'):
                    exemplo_candidato = list(painel['candidatos'].keys())[0] if painel['candidatos'] else None
                    if exemplo_candidato:
                        print(f"\nExemplo de análise do candidato {exemplo_candidato}:")
                        pprint(painel['candidatos'][exemplo_candidato])
        else:
            print(f"Erro na requisição: {response.status_code}")
            try:
                error_info = response.json()
                print(f"Detalhes do erro: {error_info}")
            except:
                print(f"Conteúdo da resposta: {response.text[:200]}...")
    except Exception as e:
        print(f"Erro ao obter painel de candidatos: {str(e)}")

def run_all_tests():
    """Run all tests"""
    print("=== Iniciando testes da API ===")
    test_root()
    
    # Perguntar se deve coletar novas notícias (pode demorar)
    collect = input("\nDeseja coletar novas notícias? (s/n): ")
    if collect.lower() == 's':
        test_collect_news()
        print("Aguardando 5 segundos para continuar...")
        time.sleep(5)
    
    # Testar modelos e análise de texto (não dependem de dados coletados)
    test_analyze_text()
    test_model_predictions()
    test_models_info()
    
    # Testar endpoints que dependem de dados
    test_get_news()
    test_statistics()
    test_sources()
    test_analyze_news()
    test_get_news_by_aspect()
    test_get_news_by_sentiment()
    
    # Testar novos endpoints de candidatos e regiões
    test_get_candidatos()
    test_get_regioes()
    test_get_news_by_candidato()
    test_get_news_by_regiao()
    test_analise_candidato()
    test_analise_regiao()
    test_mapa_temas_regionais()
    test_painel_candidatos()
    
    print("\n=== Testes concluídos ===")

def run_candidatos_tests():
    """Run only tests related to candidates"""
    print("=== Iniciando testes de candidatos ===")
    test_get_candidatos()
    test_get_news_by_candidato()
    test_analise_candidato()
    test_painel_candidatos()
    print("\n=== Testes de candidatos concluídos ===")

def run_regioes_tests():
    """Run only tests related to regions"""
    print("=== Iniciando testes de regiões ===")
    test_get_regioes()
    test_get_news_by_regiao()
    test_analise_regiao()
    test_mapa_temas_regionais()
    print("\n=== Testes de regiões concluídos ===")

if __name__ == "__main__":
    teste_tipo = input("Escolha o tipo de teste (1=Completo, 2=Candidatos, 3=Regiões): ")
    
    if teste_tipo == "2":
        run_candidatos_tests()
    elif teste_tipo == "3":
        run_regioes_tests()
    else:
        run_all_tests() 