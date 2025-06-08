import sys
import os
import joblib
import pandas as pd
import json
import re
import nltk
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np
import time
import ast

# Import do news_collector
try:
    # Tenta importar diretamente (se o arquivo estiver na mesma pasta)
    try:
        from news_collector import NewsCollector
        print("NewsCollector importado localmente")
    except ImportError:
        # Se não encontrar, tenta importar da pasta raiz
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from news_collector import NewsCollector
        print("NewsCollector importado da pasta raiz")
except ImportError:
    print("AVISO: NewsCollector não encontrado. A coleta de notícias não estará disponível.")
    
    # Classe vazia para evitar erros
    class NewsCollector:
        def __init__(self, *args, **kwargs):
            pass
        
        def collect_all_news(self, *args, **kwargs):
            return {"total": 0, "news": [], "sources": {}}

# Import para processamento de texto
try:
    from unidecode import unidecode
    import spacy
except ImportError:
    print("AVISO: Bibliotecas de processamento de texto não encontradas. Funcionalidades limitadas.")
    
    def unidecode(text):
        return text

class NoticiaService:
    def __init__(self):
        # Get the project root directory
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        
        # Modelos pré-treinados
        self.modelo_aspectos = None
        self.modelo_sentimentos = None
        self.label_mappings = None
        
        # NLP para processamento de texto
        self.nlp = None
        
        # Cache de notícias
        self.df_cache = pd.DataFrame()
        
        # Carregar modelos
        try:
            # Primeiro, tentar carregar os modelos da pasta atual (api)
            modelo_aspectos_path = os.path.join(self.project_root, 'modelo_aspectos.joblib')
            modelo_sentimentos_path = os.path.join(self.project_root, 'modelo_sentimentos.joblib')
            
            print(f"Tentando carregar modelos de: {modelo_aspectos_path}")
            
            if os.path.exists(modelo_aspectos_path) and os.path.exists(modelo_sentimentos_path):
                self.modelo_aspectos = joblib.load(modelo_aspectos_path)
                self.modelo_sentimentos = joblib.load(modelo_sentimentos_path)
                print(f"Modelos carregados com sucesso de {modelo_aspectos_path}")
            else:
                raise FileNotFoundError(f"Modelos não encontrados em {modelo_aspectos_path}")
                
        except Exception as e:
            print(f"Erro ao carregar modelos: {str(e)}")
            print("Os modelos serão criados pelo script setup.py se necessário.")
            self.modelo_aspectos = None
            self.modelo_sentimentos = None
        
        # Load label mappings
        try:
            label_mappings_path = os.path.join(self.project_root, 'label_mappings.json')
            
            if os.path.exists(label_mappings_path):
                with open(label_mappings_path, 'r', encoding='utf-8') as f:
                    self.label_mappings = json.load(f)
                print(f"Mapeamento de rótulos carregado com sucesso de {label_mappings_path}")
            else:
                print(f"Arquivo de mapeamento não encontrado em {label_mappings_path}. Usando valores padrão.")
                self.label_mappings = {
                    "aspects": {
                        "congresso": 0,
                        "economia": 1,
                        "governo": 2,
                        "outros": 3
                    },
                    "sentiments": {
                        "negativo": 0,
                        "neutro": 1,
                        "positivo": 2
                    }
                }
                # Salvar mapeamento padrão
                with open(label_mappings_path, 'w', encoding='utf-8') as f:
                    json.dump(self.label_mappings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao carregar mapeamento de rótulos: {str(e)}")
        
        # Carregar spaCy para análise de texto
        try:
            import spacy
            self.nlp = spacy.load("pt_core_news_lg")
            print("Modelo spaCy carregado com sucesso!")
        except Exception as e:
            print(f"Não foi possível carregar o modelo spaCy: {str(e)}")
            self.nlp = None
        
        # Inicializar dicionários e léxicos para análise
        self.aspectos_dict = self._carregar_dicionario_aspectos()
        self.lexico_politico = self._carregar_lexico_politico()
        
        # Configurar diretório de dados
        self.data_dir = os.path.join(self.project_root, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize or load cache
        self.cache_file = os.path.join(self.data_dir, 'noticias_cache.csv')
        if os.path.exists(self.cache_file):
            try:
                self.df_cache = pd.read_csv(self.cache_file)
                print(f"Cache carregado com sucesso: {len(self.df_cache)} notícias")
            except:
                print("Erro ao carregar cache. Iniciando com DataFrame vazio.")
                self.df_cache = pd.DataFrame()
        else:
            print("Arquivo de cache não encontrado. Iniciando com DataFrame vazio.")
            self.df_cache = pd.DataFrame()

    def coletar_todas_noticias(self) -> Dict:
        """Collect news from all sources"""
        todas_noticias = []
        fontes_stats = {}
        
        try:
            print("\n===== INICIANDO COLETA DE NOTÍCIAS =====")
            
            # Inicializar coletor de notícias, se necessário
            if not hasattr(self, 'news_collector') or self.news_collector is None:
                try:
                    self.news_collector = NewsCollector()
                    print("Coletor de notícias inicializado com sucesso.")
                except Exception as e:
                    print(f"Erro ao inicializar coletor de notícias: {str(e)}")
                    return {
                        "total_coletadas": 0,
                        "fontes": {}
                    }
            
            # Usar o novo método collect_all_news se disponível
            if hasattr(self.news_collector, 'collect_all_news'):
                print("Usando método collect_all_news para coletar notícias...")
                start_time = time.time()
                
                try:
                    resultado = self.news_collector.collect_all_news()
                    todas_noticias = resultado.get('news', [])
                    fontes_stats = resultado.get('sources', {})
                    
                    print(f"✓ Coleta concluída em {time.time() - start_time:.2f} segundos")
                    print(f"Total de notícias coletadas: {len(todas_noticias)}")
                    
                    for fonte, quantidade in fontes_stats.items():
                        print(f"  - {fonte}: {quantidade} notícias")
                        
                except Exception as e:
                    print(f"✗ Erro ao coletar notícias: {str(e)}")
            
            # Processar e classificar as notícias coletadas
            print(f"\n===== PROCESSANDO NOTÍCIAS =====")
            print(f"Total de notícias coletadas: {len(todas_noticias)}")
            
            if len(todas_noticias) == 0:
                print("Nenhuma notícia foi coletada. Verifique a conexão com a internet ou as fontes de notícias.")
                return {
                    "total_coletadas": 0,
                    "fontes": fontes_stats
                }
            
            print("\n----- Classificando notícias -----")
            noticias_processadas = []
            start_time = time.time()
            
            for i, noticia in enumerate(todas_noticias):
                if i % 5 == 0:  # Mostrar progresso a cada 5 notícias
                    print(f"Processando notícia {i+1}/{len(todas_noticias)} ({(i+1)/len(todas_noticias)*100:.1f}%)...")
                
                # Adicionar análise de aspecto e sentimento
                texto_completo = f"{noticia.get('titulo', '')} {noticia.get('texto', '')}"
                try:
                    analise = self.analisar_texto_completo(texto_completo)
                    noticia.update(analise)
                    noticias_processadas.append(noticia)
                    
                    if i % 10 == 0:  # Mostrar detalhes a cada 10 notícias
                        print(f"  - '{noticia.get('titulo', '')[:50]}...' → Aspecto: {analise['aspecto']}, Sentimento: {analise['sentimento']}")
                except Exception as e:
                    print(f"  ✗ Erro ao analisar notícia {i+1}: {str(e)}")
            
            print(f"\n✓ Classificação concluída em {time.time() - start_time:.2f} segundos")
            print(f"Total de notícias processadas: {len(noticias_processadas)}/{len(todas_noticias)}")
            
            # Update cache
            if noticias_processadas:
                print("\n----- Atualizando cache -----")
                start_time = time.time()
                
                df_novo = pd.DataFrame(noticias_processadas)
                
                if self.df_cache.empty:
                    self.df_cache = df_novo
                    print(f"Cache inicializado com {len(df_novo)} notícias")
                else:
                    print(f"Cache atual: {len(self.df_cache)} notícias")
                    self.df_cache = pd.concat([self.df_cache, df_novo])
                    print(f"Cache após concatenação: {len(self.df_cache)} notícias")
                    
                # Remover duplicatas
                tamanho_antes = len(self.df_cache)
                self.df_cache = self.df_cache.drop_duplicates(subset=['url'])
                print(f"Duplicatas removidas: {tamanho_antes - len(self.df_cache)} notícias")
                
                # Salvar cache
                try:
                    self.df_cache.to_csv(self.cache_file, index=False)
                    print(f"✓ Cache salvo com sucesso: {len(self.df_cache)} notícias no total")
                    print(f"  Arquivo: {self.cache_file}")
                    print(f"  Tempo de processamento: {time.time() - start_time:.2f} segundos")
                except Exception as e:
                    print(f"✗ Erro ao salvar cache: {str(e)}")
            
            print("\n===== COLETA DE NOTÍCIAS CONCLUÍDA =====")
            print(f"Total de notícias coletadas por fonte:")
            for fonte, quantidade in fontes_stats.items():
                print(f"  - {fonte}: {quantidade} notícias")
        
        except Exception as e:
            print(f"\n✗ ERRO DURANTE A COLETA DE NOTÍCIAS: {str(e)}")
        
        return {
            "total_coletadas": len(todas_noticias),
            "fontes": fontes_stats
        }

    def get_noticias(
        self,
        fonte: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get news with filters"""
        if self.df_cache.empty:
            print("Cache vazio. Retornando lista vazia.")
            return []
        
        df = self.df_cache.copy()
        
        # Apply filters
        if fonte:
            df = df[df['fonte'] == fonte]
        
        if data_inicio:
            df = df[df['data'] >= data_inicio]
            
        if data_fim:
            df = df[df['data'] <= data_fim]
            
        # Sort by date and limit
        df = df.sort_values('data', ascending=False).head(limit)
        
        # Tratar valores NaN antes de converter para dicionários
        # Substituir NaN em campos de string por string vazia
        for coluna in df.columns:
            if df[coluna].dtype == 'object':
                df[coluna] = df[coluna].fillna('')
            elif pd.api.types.is_numeric_dtype(df[coluna]):
                # Converter NaN numéricos para 0
                df[coluna] = df[coluna].fillna(0)
        
        # Garantir que o campo 'data' seja sempre uma string válida
        # Substituir valores vazios ou inválidos por data atual
        from datetime import datetime
        data_atual = datetime.now().strftime("%Y-%m-%d")
        df['data'] = df['data'].apply(lambda x: data_atual if not x or pd.isna(x) else x)
        
        return df.to_dict('records')

    def preprocess_text(self, text: str) -> str:
        """
        Pré-processa o texto usando spaCy para:
        1. Limpeza básica
        2. Tokenização
        3. Lematização
        4. Normalização de entidades
        """
        if not self.nlp:
            return text
            
        # Limpeza básica
        text = text.replace('"', '').replace('"', '').replace('"', '')
        text = unidecode(text)  # Remove acentos
        
        # Processar com spaCy
        doc = self.nlp(text.lower())
        
        # Lista para guardar tokens processados
        processed_tokens = []
        
        for token in doc:
            # Se for uma entidade nomeada, normaliza
            if token.ent_type_:
                # Normaliza mantendo o tipo da entidade
                processed_tokens.append(f"{token.ent_type_}_{token.ent_type}")
            else:
                # Se não for entidade, usa o lema (forma base da palavra)
                processed_tokens.append(token.lemma_)
        
        # Reconstrói o texto mantendo espaços e pontuação apropriados
        processed_text = ' '.join(processed_tokens)
        
        # Remove espaços múltiplos
        processed_text = re.sub(r'\s+', ' ', processed_text)
        
        return processed_text.strip()

    def normalizar_texto(self, texto: str) -> str:
        """Remove acentos, converte para minúsculas e remove caracteres especiais"""
        texto = unidecode(str(texto)).lower()
        texto = re.sub(r'[^\w\s]', ' ', texto)
        return texto

    def encontrar_aspectos(self, texto: str) -> Tuple[str, int]:
        """Encontra o aspecto principal presente no texto"""
        if not self.aspectos_dict:
            return "outros", 0
            
        texto_norm = self.normalizar_texto(texto)
        aspectos_encontrados = []
        
        for aspecto, palavras_chave in self.aspectos_dict.items():
            # Conta quantas palavras-chave diferentes foram encontradas
            matches = sum(1 for palavra in palavras_chave if palavra in texto_norm)
            if matches > 0:
                # Guarda o aspecto e quantidade de matches
                aspectos_encontrados.append((aspecto, matches))
        
        # Ordena por número de matches (mais matches primeiro)
        aspectos_encontrados.sort(key=lambda x: x[1], reverse=True)
        
        # Se encontrou aspectos, retorna o mais relevante
        if aspectos_encontrados:
            return aspectos_encontrados[0]
        
        return "outros", 0

    def contar_palavras_lexico(self, texto: str) -> Dict[str, int]:
        """Conta ocorrências de palavras do léxico no texto"""
        if not self.lexico_politico:
            return {"positivo": 0, "negativo": 0, "neutro": 0}
            
        texto_norm = self.normalizar_texto(texto)
        palavras = texto_norm.split()
        
        contagem = {'positivo': 0, 'negativo': 0, 'neutro': 0}
        
        for palavra in palavras:
            for sentimento, lista_palavras in self.lexico_politico.items():
                if palavra in lista_palavras:
                    contagem[sentimento] += 1
        
        return contagem

    def classificar_sentimento(self, texto: str, titulo: str) -> str:
        """Classifica o sentimento combinando léxico político"""
        # Combina título e texto, dando mais peso ao título
        texto_completo = f"{titulo} {titulo} {texto}"
        
        # Análise baseada no léxico político
        contagem = self.contar_palavras_lexico(texto_completo)
        
        # Determina sentimento baseado na contagem
        max_contagem = max(contagem.values())
        if max_contagem == 0:
            return 'neutro'
        else:
            # Caso contrário, usa o sentimento com mais ocorrências
            for sentimento, valor in contagem.items():
                if valor == max_contagem:
                    return sentimento
        
        return 'neutro'

    def split_and_analyze_text(self, texto: str) -> List[Dict]:
        """Divide o texto em orações e analisa cada uma"""
        if not self.nlp:
            return [{"texto": texto, "aspecto": "outros", "sentimento": "neutro"}]
            
        doc = self.nlp(texto)
        
        # Dividir em orações
        sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]  # Mínimo de 20 caracteres
        
        # Se não houver divisão possível, retornar o texto original
        if not sentences:
            return [{"texto": texto, "aspecto": "outros", "sentimento": "neutro"}]
        
        # Analisar cada oração
        results = []
        for sent in sentences:
            processed_text = self.preprocess_text(sent)
            aspecto, relevancia = self.encontrar_aspectos(processed_text)
            sentimento = self.classificar_sentimento(processed_text, "")
            
            results.append({
                'texto': sent,
                'aspecto': aspecto,
                'sentimento': sentimento,
                'relevancia': relevancia
            })
        
        return results

    def analisar_texto(self, texto: str) -> Dict:
        """Analyze text for aspect and sentiment using models"""
        if self.modelo_aspectos and self.modelo_sentimentos:
            try:
                # Proteger contra o erro 'list index out of range'
                try:
                    aspecto_pred = self.modelo_aspectos.predict([texto])
                    if len(aspecto_pred) > 0:
                        aspecto = aspecto_pred[0]
                    else:
                        raise IndexError("Previsão de aspecto retornou lista vazia")
                except (IndexError, ValueError) as e:
                    print(f"Erro ao prever aspecto: {str(e)}")
                    aspecto = 3  # Valor padrão para 'outros'
                
                try:
                    sentimento_pred = self.modelo_sentimentos.predict([texto])
                    if len(sentimento_pred) > 0:
                        sentimento = sentimento_pred[0]
                    else:
                        raise IndexError("Previsão de sentimento retornou lista vazia")
                except (IndexError, ValueError) as e:
                    print(f"Erro ao prever sentimento: {str(e)}")
                    sentimento = 1  # Valor padrão para 'neutro'
                
                # Get aspect and sentiment labels
                try:
                    aspecto_label = [k for k, v in self.label_mappings['aspects'].items() if v == aspecto][0]
                except (IndexError, KeyError):
                    print(f"Aviso: Índice de aspecto {aspecto} não encontrado no mapeamento")
                    aspecto_label = "outros"
                
                try:
                    sentimento_label = [k for k, v in self.label_mappings['sentiments'].items() if v == sentimento][0]
                except (IndexError, KeyError):
                    print(f"Aviso: Índice de sentimento {sentimento} não encontrado no mapeamento")
                    sentimento_label = "neutro"
                
                return {
                    'aspecto': aspecto_label,
                    'sentimento': sentimento_label
                }
            except Exception as e:
                print(f"Erro ao classificar texto com modelos: {str(e)}")
        
        # Fallback para classificação baseada em regras
        aspecto, relevancia = self.encontrar_aspectos(texto)
        sentimento = self.classificar_sentimento(texto, "")
        
        return {
            'aspecto': aspecto,
            'sentimento': sentimento,
            'relevancia': relevancia
        }

    def analisar_texto_completo(self, texto: str) -> Dict:
        """Analisa o texto completo, dividindo em orações e identificando aspectos e sentimentos"""
        # Primeiro, tenta usar os modelos para classificação geral
        analise_geral = self.analisar_texto(texto)
        
        # Depois, divide o texto em orações para análise detalhada
        analises_detalhadas = self.split_and_analyze_text(texto)
        
        # Conta a frequência de cada aspecto e sentimento nas análises detalhadas
        aspectos_count = {}
        sentimentos_count = {}
        
        for analise in analises_detalhadas:
            aspecto = analise['aspecto']
            sentimento = analise['sentimento']
            
            if aspecto in aspectos_count:
                aspectos_count[aspecto] += 1
            else:
                aspectos_count[aspecto] = 1
                
            if sentimento in sentimentos_count:
                sentimentos_count[sentimento] += 1
            else:
                sentimentos_count[sentimento] = 1
        
        # Determina o aspecto e sentimento predominantes
        aspecto_predominante = max(aspectos_count.items(), key=lambda x: x[1])[0] if aspectos_count else analise_geral['aspecto']
        sentimento_predominante = max(sentimentos_count.items(), key=lambda x: x[1])[0] if sentimentos_count else analise_geral['sentimento']
        
        # Retorna o resultado combinado
        return {
            'aspecto': aspecto_predominante,
            'sentimento': sentimento_predominante,
            'analises_detalhadas': analises_detalhadas,
            'relevancia': len(analises_detalhadas)
        }

    def prever_com_modelos(self, texto: str, preprocessar: bool = True) -> Dict:
        """
        Realiza previsão direta usando os modelos pré-treinados e enriquece com análises adicionais
        """
        if not self.modelo_aspectos or not self.modelo_sentimentos:
            raise Exception("Modelos não estão disponíveis")
        
        # Pré-processar o texto se necessário
        texto_processado = self.preprocess_text(texto) if preprocessar else texto
        
        # Fazer previsões
        try:
            # Prever aspecto
            aspecto_idx = self.modelo_aspectos.predict([texto_processado])[0]
            aspecto_probs = self.modelo_aspectos.predict_proba([texto_processado])
            
            # Verificar se aspecto_probs tem conteúdo válido
            if len(aspecto_probs) > 0 and len(aspecto_probs[0]) > 0:
                aspecto_confianca = float(max(aspecto_probs[0]))
            else:
                aspecto_confianca = 0.0
                print("Aviso: Probabilidades de aspecto vazias")
            
            # Prever sentimento
            sentimento_idx = self.modelo_sentimentos.predict([texto_processado])[0]
            sentimento_probs = self.modelo_sentimentos.predict_proba([texto_processado])
            
            # Verificar se sentimento_probs tem conteúdo válido
            if len(sentimento_probs) > 0 and len(sentimento_probs[0]) > 0:
                sentimento_confianca = float(max(sentimento_probs[0]))
            else:
                sentimento_confianca = 0.0
                print("Aviso: Probabilidades de sentimento vazias")
            
            # Converter índices para rótulos
            # Verificar se o índice existe no mapeamento
            aspecto_label = None
            for k, v in self.label_mappings['aspects'].items():
                if v == aspecto_idx:
                    aspecto_label = k
                    break
            
            if aspecto_label is None:
                aspecto_label = "outros"  # Valor padrão se não encontrar
                print(f"Aviso: Índice de aspecto {aspecto_idx} não encontrado no mapeamento")
                
            sentimento_label = None
            for k, v in self.label_mappings['sentiments'].items():
                if v == sentimento_idx:
                    sentimento_label = k
                    break
                    
            if sentimento_label is None:
                sentimento_label = "neutro"  # Valor padrão se não encontrar
                print(f"Aviso: Índice de sentimento {sentimento_idx} não encontrado no mapeamento")
            
            # Análises adicionais
            # 1. Detectar candidatos
            candidatos_detectados = self.detectar_candidatos(texto)
            
            # 2. Detectar regiões
            regiao_detectada = self.detectar_regiao(texto)
            
            # 3. Detectar entidades
            entidades = self.detectar_entidades(texto)
            
            # 4. Fazer análise detalhada por sentenças
            analises_detalhadas = self.split_and_analyze_text(texto)
            
            # 5. Determinar relevância do tema
            relevancia = 0
            if aspecto_label != "outros":
                relevancia = min(int(aspecto_confianca * 3) + 1, 3)  # Escala de 1 a 3
            
            # 6. Extrair palavras-chave e termos relevantes
            palavras_chave = []
            if self.nlp:
                doc = self.nlp(texto)
                # Identificar substantivos, verbos e adjetivos mais relevantes
                palavras_chave = [token.text for token in doc if (token.pos_ in ['NOUN', 'PROPN', 'ADJ', 'VERB']) 
                                  and not token.is_stop and len(token.text) > 3]
                # Remover duplicatas
                palavras_chave = list(set(palavras_chave))[:10]  # Limitar a 10 palavras-chave
                
            # Preparar resultado enriquecido
            resultado = {
                'aspecto': aspecto_label,
                'sentimento': sentimento_label,
                'confianca_aspecto': aspecto_confianca,
                'confianca_sentimento': sentimento_confianca,
                'texto_preprocessado': texto_processado if preprocessar else None,
                'candidatos_detectados': candidatos_detectados,
                'regiao_detectada': regiao_detectada,
                'entidades': entidades,
                'palavras_chave': palavras_chave,
                'relevancia': relevancia,
                'analises_detalhadas': analises_detalhadas
            }
            
            return resultado
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erro ao fazer previsões com os modelos: {str(e)}\n{error_details}")
            # Retornar valores padrão em caso de erro
            return {
                'aspecto': "outros",
                'sentimento': "neutro",
                'confianca_aspecto': 0.0,
                'confianca_sentimento': 0.0,
                'texto_preprocessado': texto_processado if preprocessar else None,
                'candidatos_detectados': [],
                'regiao_detectada': None,
                'entidades': {
                    'organizacoes': [],
                    'pessoas': [],
                    'localizacoes': [],
                    'eventos': [],
                    'outras': []
                },
                'palavras_chave': [],
                'relevancia': 0,
                'analises_detalhadas': [],
                'erro': str(e)
            }

    def prever_aspecto(self, texto: str, preprocessar: bool = True) -> Dict:
        """
        Realiza previsão apenas do aspecto usando o modelo pré-treinado
        """
        if not self.modelo_aspectos:
            raise Exception("Modelo de aspectos não está disponível")
        
        # Pré-processar o texto se necessário
        texto_processado = self.preprocess_text(texto) if preprocessar else texto
        
        # Fazer previsão
        try:
            # Prever aspecto
            aspecto_idx = self.modelo_aspectos.predict([texto_processado])[0]
            aspecto_probs = self.modelo_aspectos.predict_proba([texto_processado])
            
            # Verificar se aspecto_probs tem conteúdo válido
            if len(aspecto_probs) > 0 and len(aspecto_probs[0]) > 0:
                aspecto_confianca = float(max(aspecto_probs[0]))
            else:
                aspecto_confianca = 0.0
                print("Aviso: Probabilidades de aspecto vazias")
            
            # Converter índice para rótulo
            aspecto_label = None
            for k, v in self.label_mappings['aspects'].items():
                if v == aspecto_idx:
                    aspecto_label = k
                    break
            
            if aspecto_label is None:
                aspecto_label = "outros"  # Valor padrão se não encontrar
                print(f"Aviso: Índice de aspecto {aspecto_idx} não encontrado no mapeamento")
            
            return {
                'aspecto': aspecto_label,
                'confianca': aspecto_confianca,
                'texto_preprocessado': texto_processado if preprocessar else None
            }
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erro ao fazer previsão de aspecto: {str(e)}\n{error_details}")
            # Retornar valores padrão em caso de erro
            return {
                'aspecto': "outros",
                'confianca': 0.0,
                'texto_preprocessado': texto_processado if preprocessar else None,
                'erro': str(e)
            }

    def prever_sentimento(self, texto: str, preprocessar: bool = True) -> Dict:
        """
        Realiza previsão apenas do sentimento usando o modelo pré-treinado
        """
        if not self.modelo_sentimentos:
            raise Exception("Modelo de sentimentos não está disponível")
        
        # Pré-processar o texto se necessário
        texto_processado = self.preprocess_text(texto) if preprocessar else texto
        
        # Fazer previsão
        try:
            # Prever sentimento
            sentimento_idx = self.modelo_sentimentos.predict([texto_processado])[0]
            sentimento_probs = self.modelo_sentimentos.predict_proba([texto_processado])
            
            # Verificar se sentimento_probs tem conteúdo válido
            if len(sentimento_probs) > 0 and len(sentimento_probs[0]) > 0:
                sentimento_confianca = float(max(sentimento_probs[0]))
            else:
                sentimento_confianca = 0.0
                print("Aviso: Probabilidades de sentimento vazias")
            
            # Converter índice para rótulo
            sentimento_label = None
            for k, v in self.label_mappings['sentiments'].items():
                if v == sentimento_idx:
                    sentimento_label = k
                    break
            
            if sentimento_label is None:
                sentimento_label = "neutro"  # Valor padrão se não encontrar
                print(f"Aviso: Índice de sentimento {sentimento_idx} não encontrado no mapeamento")
            
            return {
                'sentimento': sentimento_label,
                'confianca': sentimento_confianca,
                'texto_preprocessado': texto_processado if preprocessar else None
            }
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erro ao fazer previsão de sentimento: {str(e)}\n{error_details}")
            # Retornar valores padrão em caso de erro
            return {
                'sentimento': "neutro",
                'confianca': 0.0,
                'texto_preprocessado': texto_processado if preprocessar else None,
                'erro': str(e)
            }

    def get_modelos_info(self) -> Dict:
        """
        Retorna informações sobre os modelos carregados
        """
        try:
            info = {
                'modelos_disponiveis': {
                    'aspectos': self.modelo_aspectos is not None,
                    'sentimentos': self.modelo_sentimentos is not None
                },
                'aspectos_possiveis': list(self.label_mappings['aspects'].keys()),
                'sentimentos_possiveis': list(self.label_mappings['sentiments'].keys()),
                'versao_api': '1.0.0',
                'timestamp': datetime.now().isoformat()
            }
            
            # Adicionar informações específicas dos modelos se disponíveis
            if self.modelo_aspectos is not None:
                try:
                    if hasattr(self.modelo_aspectos, 'get_params'):
                        # Tratar de forma segura os parâmetros dos modelos
                        params = self.modelo_aspectos.get_params()
                        
                        # Remover qualquer método ou função não serializável
                        params_serializable = {}
                        for k, v in params.items():
                            if not callable(v):
                                try:
                                    # Testar se é serializável
                                    json.dumps({k: v})
                                    params_serializable[k] = v
                                except (TypeError, OverflowError):
                                    # Se não for serializável, converter para string
                                    params_serializable[k] = str(v)
                        
                        info['modelo_aspectos'] = {
                            'tipo': type(self.modelo_aspectos).__name__,
                            'parametros': params_serializable
                        }
                    else:
                        info['modelo_aspectos'] = {
                            'tipo': type(self.modelo_aspectos).__name__,
                            'parametros': 'Informação não disponível'
                        }
                except Exception as e:
                    info['modelo_aspectos'] = {
                        'tipo': str(type(self.modelo_aspectos)),
                        'erro': str(e)
                    }
            
            if self.modelo_sentimentos is not None:
                try:
                    if hasattr(self.modelo_sentimentos, 'get_params'):
                        # Tratar de forma segura os parâmetros dos modelos
                        params = self.modelo_sentimentos.get_params()
                        
                        # Remover qualquer método ou função não serializável
                        params_serializable = {}
                        for k, v in params.items():
                            if not callable(v):
                                try:
                                    # Testar se é serializável
                                    json.dumps({k: v})
                                    params_serializable[k] = v
                                except (TypeError, OverflowError):
                                    # Se não for serializável, converter para string
                                    params_serializable[k] = str(v)
                        
                        info['modelo_sentimentos'] = {
                            'tipo': type(self.modelo_sentimentos).__name__,
                            'parametros': params_serializable
                        }
                    else:
                        info['modelo_sentimentos'] = {
                            'tipo': type(self.modelo_sentimentos).__name__,
                            'parametros': 'Informação não disponível'
                        }
                except Exception as e:
                    info['modelo_sentimentos'] = {
                        'tipo': str(type(self.modelo_sentimentos)),
                        'erro': str(e)
                    }
            
            return info
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erro ao obter informações dos modelos: {str(e)}\n{error_details}")
            return {
                'erro': str(e),
                'modelos_disponiveis': {
                    'aspectos': self.modelo_aspectos is not None,
                    'sentimentos': self.modelo_sentimentos is not None
                },
                'versao_api': '1.0.0'
            }

    def get_noticias_com_analise(
        self,
        fonte: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get news with aspect and sentiment analysis"""
        try:
            noticias = self.get_noticias(fonte, data_inicio, data_fim, limit)
            
            if not noticias:
                print("Nenhuma notícia encontrada para análise")
                return []
            
            noticias_processadas = []
            for i, noticia in enumerate(noticias):
                try:
                    # Verificar campos obrigatórios
                    if not isinstance(noticia, dict):
                        print(f"Notícia {i} não é um dicionário válido. Pulando.")
                        continue
                        
                    if 'titulo' not in noticia or 'texto' not in noticia:
                        print(f"Notícia {i} não possui título ou texto. Pulando.")
                        continue
                    
                    # Criar cópia para não modificar o original
                    noticia_processada = noticia.copy()
                    
                    # Verificar todos os campos string e substituir valores None ou NaN
                    for campo in ['titulo', 'texto', 'fonte', 'url', 'origem', 'data']:
                        if campo not in noticia_processada or noticia_processada[campo] is None or pd.isna(noticia_processada[campo]):
                            if campo == 'data':
                                noticia_processada[campo] = datetime.now().strftime("%Y-%m-%d")
                            else:
                                noticia_processada[campo] = ""
                    
                    # Adicionar análise se não existir
                    if 'aspecto' not in noticia_processada or 'sentimento' not in noticia_processada or pd.isna(noticia_processada.get('aspecto')) or pd.isna(noticia_processada.get('sentimento')):
                        texto_completo = f"{noticia_processada.get('titulo', '')} {noticia_processada.get('texto', '')}"
                        try:
                            analise = self.analisar_texto_completo(texto_completo)
                            noticia_processada.update(analise)
                        except Exception as e:
                            print(f"Erro ao analisar notícia {i}: {str(e)}")
                            # Adicionar valores padrão
                            noticia_processada['aspecto'] = noticia_processada.get('aspecto', 'outros')
                            noticia_processada['sentimento'] = noticia_processada.get('sentimento', 'neutro')
                            noticia_processada['relevancia'] = noticia_processada.get('relevancia', 0)
                    
                    # Garantir que campos numéricos sejam válidos
                    if 'relevancia' not in noticia_processada or noticia_processada['relevancia'] is None or pd.isna(noticia_processada['relevancia']):
                        noticia_processada['relevancia'] = 0
                    
                    # Verificar campo de candidatos
                    if 'candidatos' not in noticia_processada or noticia_processada['candidatos'] is None or pd.isna(noticia_processada['candidatos']):
                        noticia_processada['candidatos'] = []
                    elif isinstance(noticia_processada['candidatos'], str):
                        if noticia_processada['candidatos'].startswith('[') and noticia_processada['candidatos'].endswith(']'):
                            try:
                                noticia_processada['candidatos'] = ast.literal_eval(noticia_processada['candidatos'])
                            except:
                                noticia_processada['candidatos'] = []
                        else:
                            noticia_processada['candidatos'] = [noticia_processada['candidatos']]
                    
                    # Verificar campo de região
                    if 'regiao' not in noticia_processada or noticia_processada['regiao'] is None or pd.isna(noticia_processada['regiao']):
                        noticia_processada['regiao'] = ""
                    
                    # Verificar análises detalhadas
                    if 'analises_detalhadas' not in noticia_processada:
                        # Criar análise detalhada padrão
                        noticia_processada['analises_detalhadas'] = [{
                            'texto': noticia_processada.get('texto', ''),
                            'aspecto': noticia_processada.get('aspecto', 'outros'),
                            'sentimento': noticia_processada.get('sentimento', 'neutro'),
                            'relevancia': noticia_processada.get('relevancia', 0)
                        }]
                    elif noticia_processada['analises_detalhadas'] is None or pd.isna(noticia_processada['analises_detalhadas']):
                        noticia_processada['analises_detalhadas'] = [{
                            'texto': noticia_processada.get('texto', ''),
                            'aspecto': noticia_processada.get('aspecto', 'outros'),
                            'sentimento': noticia_processada.get('sentimento', 'neutro'),
                            'relevancia': noticia_processada.get('relevancia', 0)
                        }]
                    
                    noticias_processadas.append(noticia_processada)
                except Exception as e:
                    print(f"Erro ao processar notícia {i}: {str(e)}")
            
            return noticias_processadas
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erro em get_noticias_com_analise: {str(e)}\n{error_details}")
            return []

    def get_estatisticas(self) -> Dict:
        """Get statistics about collected news"""
        try:
            df = self.df_cache.copy()
            
            # Se não houver dados, retorna estatísticas vazias
            if df.empty:
                return {
                    'total_noticias': 0,
                    'noticias_por_fonte': {},
                    'noticias_por_aspecto': {},
                    'noticias_por_sentimento': {},
                    'periodo': {
                        'inicio': None,
                        'fim': None
                    }
                }
            
            # Add analysis if not present
            if 'aspecto' not in df.columns or 'sentimento' not in df.columns:
                df['analise'] = df.apply(
                    lambda x: self.analisar_texto(f"{x['titulo']} {x['texto']}"),
                    axis=1
                )
                df['aspecto'] = df['analise'].apply(lambda x: x['aspecto'])
                df['sentimento'] = df['analise'].apply(lambda x: x['sentimento'])
            
            # Garantir que as datas sejam strings para evitar problemas de comparação
            if 'data' in df.columns:
                df['data'] = df['data'].astype(str)
                # Substituir valores 'nan' por uma data padrão
                df['data'] = df['data'].replace('nan', datetime.now().strftime("%Y-%m-%d"))
            
            periodo = {
                'inicio': str(df['data'].min()) if not df.empty else None,
                'fim': str(df['data'].max()) if not df.empty else None
            }
            
            # Verificar se os valores do período são 'nan' e substituí-los
            if periodo['inicio'] == 'nan':
                periodo['inicio'] = datetime.now().strftime("%Y-%m-%d")
            if periodo['fim'] == 'nan':
                periodo['fim'] = datetime.now().strftime("%Y-%m-%d")
            
            return {
                'total_noticias': len(df),
                'noticias_por_fonte': df['fonte'].value_counts().to_dict(),
                'noticias_por_aspecto': df['aspecto'].value_counts().to_dict(),
                'noticias_por_sentimento': df['sentimento'].value_counts().to_dict(),
                'periodo': periodo
            }
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erro ao obter estatísticas: {str(e)}\n{error_details}")
            # Retornar estatísticas vazias em caso de erro
            return {
                'total_noticias': 0,
                'noticias_por_fonte': {},
                'noticias_por_aspecto': {},
                'noticias_por_sentimento': {},
                'periodo': {
                    'inicio': None,
                    'fim': None
                },
                'erro': str(e)
            }

    def detectar_regiao(self, texto: str) -> Optional[str]:
        """Detecta a região mencionada no texto"""
        # Lista de regiões do Brasil para detecção
        regioes = [
            "São Paulo", "Rio de Janeiro", "Minas Gerais", "Espírito Santo",
            "Rio Grande do Sul", "Santa Catarina", "Paraná",
            "Bahia", "Sergipe", "Alagoas", "Pernambuco", "Paraíba", "Rio Grande do Norte", "Ceará", "Piauí", "Maranhão",
            "Amazonas", "Pará", "Acre", "Rondônia", "Roraima", "Amapá", "Tocantins",
            "Mato Grosso", "Mato Grosso do Sul", "Goiás", "Distrito Federal",
            "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", 
            "Brasil", "Brasília"
        ]
        
        # Primeiro verificar se a notícia já tem um campo 'regiao'
        if hasattr(texto, 'get') and callable(texto.get) and texto.get('regiao'):
            return texto.get('regiao')
            
        # Caso contrário, buscar no texto
        texto_norm = self.normalizar_texto(texto)
        
        for regiao in regioes:
            regiao_norm = self.normalizar_texto(regiao)
            if regiao_norm in texto_norm:
                return regiao
                
        # Se não encontrou nenhuma região específica
        return None
    
    def get_fontes(self) -> List[str]:
        """Get list of available news sources"""
        return self.df_cache['fonte'].unique().tolist() if not self.df_cache.empty else []

    def detectar_candidatos(self, texto: str) -> List[str]:
        """
        Detecta menções a candidatos ou políticos no texto
        """
        # Carregar lista de candidatos do arquivo se existir
        candidatos_conhecidos = self.carregar_candidatos_conhecidos()
        
        # Verificar menções diretas usando a lista de candidatos conhecidos
        candidatos_detectados = []
        texto_normalizado = self.normalizar_texto(texto)
        
        for candidato in candidatos_conhecidos:
            if candidato.lower() in texto_normalizado:
                candidatos_detectados.append(candidato)
        
        # Usar spaCy para detectar entidades de pessoa se disponível
        if self.nlp:
            doc = self.nlp(texto)
            for ent in doc.ents:
                if ent.label_ == "PER":  # Entidade é uma pessoa
                    nome = ent.text.strip()
                    # Verificar se já não foi adicionado
                    nome_normalizado = self.normalizar_texto(nome)
                    if nome not in candidatos_detectados and len(nome) > 3:  # Evitar abreviações
                        # Verificar se é um candidato conhecido
                        for candidato in candidatos_conhecidos:
                            if self.normalizar_texto(candidato) in nome_normalizado or nome_normalizado in self.normalizar_texto(candidato):
                                candidatos_detectados.append(candidato)
                                break
                        else:
                            # Se não encontrou na lista de conhecidos, adiciona o novo nome
                            candidatos_detectados.append(nome)
        
        # Remover duplicatas preservando a ordem
        return list(dict.fromkeys(candidatos_detectados))

    def carregar_candidatos_conhecidos(self) -> List[str]:
        """
        Carrega lista de candidatos conhecidos do arquivo
        """
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidatos_file = os.path.join(project_root, 'data', 'candidatos.json')
            
            if os.path.exists(candidatos_file):
                with open(candidatos_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Lista padrão de alguns políticos/candidatos relevantes
                candidatos_padrao = [
                    "Lula", "Luiz Inácio Lula da Silva",
                    "Jair Bolsonaro", "Bolsonaro",
                    "Simone Tebet", "Tebet",
                    "Ciro Gomes", "Ciro",
                    "Fernando Haddad", "Haddad",
                    "Tarcísio de Freitas", "Tarcísio",
                    "Pablo Marçal", "Marçal",
                    "Romeu Zema", "Zema",
                    "Eduardo Leite",
                    "Ronaldo Caiado", "Caiado",
                    "Helder Barbalho",
                    "João Doria", "Doria",
                    "Geraldo Alckmin", "Alckmin",
                    "Michelle Bolsonaro",
                    "Arthur Lira", "Lira",
                    "Rodrigo Pacheco", "Pacheco"
                ]
                
                # Salvar lista padrão para uso futuro
                os.makedirs(os.path.dirname(candidatos_file), exist_ok=True)
                with open(candidatos_file, 'w', encoding='utf-8') as f:
                    json.dump(candidatos_padrao, f, ensure_ascii=False, indent=2)
                
                return candidatos_padrao
        except Exception as e:
            print(f"Erro ao carregar candidatos conhecidos: {str(e)}")
            return []

    def detectar_regiao(self, texto: str) -> Optional[str]:
        """Detecta a região mencionada no texto"""
        # Lista de regiões do Brasil para detecção
        regioes = [
            "São Paulo", "Rio de Janeiro", "Minas Gerais", "Espírito Santo",
            "Rio Grande do Sul", "Santa Catarina", "Paraná",
            "Bahia", "Sergipe", "Alagoas", "Pernambuco", "Paraíba", "Rio Grande do Norte", "Ceará", "Piauí", "Maranhão",
            "Amazonas", "Pará", "Acre", "Rondônia", "Roraima", "Amapá", "Tocantins",
            "Mato Grosso", "Mato Grosso do Sul", "Goiás", "Distrito Federal",
            "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", 
            "Brasil", "Brasília"
        ]
        
        # Primeiro verificar se a notícia já tem um campo 'regiao'
        if hasattr(texto, 'get') and callable(texto.get) and texto.get('regiao'):
            return texto.get('regiao')
            
        # Caso contrário, buscar no texto
        texto_norm = self.normalizar_texto(texto)
        
        for regiao in regioes:
            regiao_norm = self.normalizar_texto(regiao)
            if regiao_norm in texto_norm:
                return regiao
                
        # Se não encontrou nenhuma região específica
        return None

    def get_candidatos(self) -> List[str]:
        """
        Retorna a lista de candidatos mencionados nas notícias
        """
        if self.df_cache.empty:
            return []
        
        # Se o campo candidatos já existir no cache
        if 'candidatos' in self.df_cache.columns:
            # Extrair todos os candidatos mencionados
            todos_candidatos = set()
            for candidatos in self.df_cache['candidatos'].dropna():
                if isinstance(candidatos, list):
                    todos_candidatos.update(candidatos)
                elif isinstance(candidatos, str):
                    try:
                        # Tentar converter string para lista
                        candidatos_lista = ast.literal_eval(candidatos)
                        if isinstance(candidatos_lista, list):
                            todos_candidatos.update(candidatos_lista)
                    except:
                        # Se falhar, considerar como um único candidato
                        todos_candidatos.add(candidatos)
            
            return sorted(list(todos_candidatos))
        
        # Se não existir, detectar os candidatos e atualizar o cache
        candidatos_detectados = set()
        df = self.df_cache.copy()
        
        # Adicionar coluna de candidatos
        df['candidatos'] = df.apply(
            lambda x: self.detectar_candidatos(f"{x['titulo']} {x['texto']}"),
            axis=1
        )
        
        # Atualizar o cache
        self.df_cache = df
        
        # Salvar cache atualizado
        try:
            self.df_cache.to_csv(self.cache_file, index=False)
            print(f"Cache atualizado com informações de candidatos")
        except Exception as e:
            print(f"Erro ao salvar cache atualizado: {str(e)}")
        
        # Extrair todos os candidatos únicos
        for candidatos in df['candidatos']:
            if candidatos:
                candidatos_detectados.update(candidatos)
        
        return sorted(list(candidatos_detectados))

    def get_regioes(self) -> List[str]:
        """
        Retorna a lista de regiões mencionadas nas notícias
        """
        if self.df_cache.empty:
            return []
        
        # Se o campo regiao já existir no cache
        if 'regiao' in self.df_cache.columns:
            # Extrair todas as regiões mencionadas
            return sorted(list(self.df_cache['regiao'].dropna().unique()))
        
        # Se não existir, detectar as regiões e atualizar o cache
        df = self.df_cache.copy()
        
        # Adicionar coluna de região
        df['regiao'] = df.apply(
            lambda x: self.detectar_regiao(f"{x['titulo']} {x['texto']}"),
            axis=1
        )
        
        # Atualizar o cache
        self.df_cache = df
        
        # Salvar cache atualizado
        try:
            self.df_cache.to_csv(self.cache_file, index=False)
            print(f"Cache atualizado com informações de regiões")
        except Exception as e:
            print(f"Erro ao salvar cache atualizado: {str(e)}")
        
        # Extrair todas as regiões únicas
        regioes = sorted(list(df['regiao'].dropna().unique()))
        
        return regioes

    def analisar_candidato(
        self,
        candidato: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> Dict:
        """
        Analisa as menções a um candidato nas notícias
        """
        if self.df_cache.empty:
            raise Exception("Não há notícias disponíveis para análise")
        
        # Garantir que candidatos foram detectados
        if 'candidatos' not in self.df_cache.columns:
            self.get_candidatos()  # Atualiza o cache com as informações de candidatos
        
        # Filtrar notícias que mencionam o candidato
        df = self.df_cache.copy()
        
        # Converter candidatos para lista se for string
        if 'candidatos' in df.columns:
            df['candidatos_lista'] = df['candidatos'].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
        else:
            # Se não existir coluna de candidatos, criar
            df['candidatos_lista'] = df.apply(
                lambda x: self.detectar_candidatos(f"{x['titulo']} {x['texto']}"),
                axis=1
            )
        
        # Filtrar por data se especificado
        if data_inicio:
            df = df[df['data'] >= data_inicio]
        if data_fim:
            df = df[df['data'] <= data_fim]
        
        # Filtrar notícias que mencionam o candidato
        df_candidato = df[df['candidatos_lista'].apply(lambda x: x is not None and candidato in x)]
        
        if df_candidato.empty:
            raise Exception(f"Não foram encontradas menções ao candidato '{candidato}'")
        
        # Calcular estatísticas
        total_mencoes = len(df_candidato)
        
        # Sentimento médio
        sentimentos = df_candidato['sentimento'].value_counts().to_dict()
        total_sentimentos = sum(sentimentos.values())
        sentimento_medio = {k: v/total_sentimentos for k, v in sentimentos.items()}
        
        # Principais aspectos
        aspectos = df_candidato['aspecto'].value_counts().to_dict()
        
        # Distribuição por região
        if 'regiao' in df_candidato.columns:
            regioes = df_candidato['regiao'].value_counts().to_dict()
        else:
            regioes = {}
        
        # Detectar partido e cargo se disponíveis
        # (Na versão atual, usamos valores fixos para demonstração)
        partido = None
        cargo = None
        
        return {
            'nome': candidato,
            'partido': partido,
            'cargo': cargo,
            'mencoes_totais': total_mencoes,
            'sentimento_medio': sentimento_medio,
            'principais_aspectos': aspectos,
            'regioes': regioes
        }

    def analisar_regiao(
        self,
        regiao: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> Dict:
        """
        Analisa as notícias relacionadas a uma região
        """
        if self.df_cache.empty:
            raise Exception("Não há notícias disponíveis para análise")
        
        # Garantir que regiões foram detectadas
        if 'regiao' not in self.df_cache.columns:
            self.get_regioes()  # Atualiza o cache com as informações de regiões
        
        # Filtrar notícias da região
        df = self.df_cache.copy()
        
        # Filtrar por data se especificado
        if data_inicio:
            df = df[df['data'] >= data_inicio]
        if data_fim:
            df = df[df['data'] <= data_fim]
        
        # Filtrar notícias da região (comparação case insensitive)
        # Substituir parenteses na busca por escaped parens para evitar problemas com regex
        regiao_search = regiao.lower().replace('(', '\\(').replace(')', '\\)')
        df_regiao = df[df['regiao'].fillna('').str.lower().str.contains(regiao_search, regex=True)]
        
        if df_regiao.empty:
            # Se não encontrar a região exata, tenta encontrar uma região parcial
            regiao_base = regiao.split('(')[0].strip().lower() if '(' in regiao else regiao.lower()
            df_regiao = df[df['regiao'].fillna('').str.lower().str.contains(regiao_base, regex=False)]
        
        if df_regiao.empty:
            # Se ainda estiver vazio, retornar uma resposta padrão em vez de erro
            return {
                'nome': regiao,
                'estado': None if '(' not in regiao else regiao.split('(')[1].split(')')[0].strip(),
                'total_noticias': 0,
                'principais_aspectos': {},
                'principais_candidatos': {},
                'sentimento_predominante': {'neutro': 1.0}
            }
        
        # Calcular estatísticas
        total_noticias = len(df_regiao)
        
        # Principais aspectos
        aspectos = df_regiao['aspecto'].value_counts().to_dict()
        
        # Sentimento predominante
        sentimentos = df_regiao['sentimento'].value_counts().to_dict()
        total_sentimentos = sum(sentimentos.values())
        sentimento_predominante = {k: v/total_sentimentos for k, v in sentimentos.items()}
        
        # Principais candidatos mencionados
        principais_candidatos = {}
        if 'candidatos' in df_regiao.columns:
            # Contar menções a candidatos
            candidatos_contagem = {}
            for candidatos in df_regiao['candidatos'].dropna():
                if isinstance(candidatos, list):
                    for candidato in candidatos:
                        candidatos_contagem[candidato] = candidatos_contagem.get(candidato, 0) + 1
                elif isinstance(candidatos, str):
                    try:
                        import ast
                        candidatos_lista = ast.literal_eval(candidatos)
                        if isinstance(candidatos_lista, list):
                            for candidato in candidatos_lista:
                                candidatos_contagem[candidato] = candidatos_contagem.get(candidato, 0) + 1
                    except:
                        candidatos_contagem[candidatos] = candidatos_contagem.get(candidatos, 0) + 1
            
            # Ordenar por contagem
            principais_candidatos = dict(sorted(candidatos_contagem.items(), key=lambda item: item[1], reverse=True)[:10])
        
        # Extrair estado da região se existir
        estado = None
        if '(' in regiao and ')' in regiao:
            estado = regiao.split('(')[1].split(')')[0].strip()
        
        return {
            'nome': regiao,
            'estado': estado,
            'total_noticias': total_noticias,
            'principais_aspectos': aspectos,
            'principais_candidatos': principais_candidatos,
            'sentimento_predominante': sentimento_predominante
        }

    def get_mapa_temas_regionais(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> Dict:
        """
        Gera um mapa de temas regionais baseado nas notícias
        """
        if self.df_cache.empty:
            return {"regioes": {}, "aspectos": {}, "temas_por_regiao": {}}
        
        # Garantir que regiões foram detectadas
        if 'regiao' not in self.df_cache.columns:
            self.get_regioes()  # Atualiza o cache com as informações de regiões
        
        # Filtrar por data se especificado
        df = self.df_cache.copy()
        if data_inicio:
            df = df[df['data'] >= data_inicio]
        if data_fim:
            df = df[df['data'] <= data_fim]
        
        # Obter lista de regiões
        regioes = sorted(list(df['regiao'].dropna().unique()))
        
        # Obter lista de aspectos
        aspectos = sorted(list(df['aspecto'].dropna().unique()))
        
        # Calcular temas predominantes por região
        temas_por_regiao = {}
        for regiao in regioes:
            df_regiao = df[df['regiao'] == regiao]
            if not df_regiao.empty:
                aspectos_regiao = df_regiao['aspecto'].value_counts().to_dict()
                sentimentos_regiao = df_regiao['sentimento'].value_counts().to_dict()
                
                # Incluir apenas os 3 principais aspectos
                principais_aspectos = dict(sorted(aspectos_regiao.items(), key=lambda item: item[1], reverse=True)[:3])
                
                # Calcular sentimento predominante
                sentimento_predominante = max(sentimentos_regiao.items(), key=lambda item: item[1])[0] if sentimentos_regiao else "neutro"
                
                temas_por_regiao[regiao] = {
                    'aspectos': principais_aspectos,
                    'sentimento_predominante': sentimento_predominante,
                    'total_noticias': len(df_regiao)
                }
        
        return {
            "regioes": regioes,
            "aspectos": aspectos,
            "temas_por_regiao": temas_por_regiao
        }

    def get_painel_candidatos(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        candidatos: Optional[List[str]] = None
    ) -> Dict:
        """
        Gera dados para o painel de candidatos
        """
        if self.df_cache.empty:
            return {"candidatos": {}, "comparativo": {}}
        
        # Garantir que candidatos foram detectados
        if 'candidatos' not in self.df_cache.columns:
            self.get_candidatos()  # Atualiza o cache com as informações de candidatos
        
        # Filtrar por data se especificado
        df = self.df_cache.copy()
        if data_inicio:
            df = df[df['data'] >= data_inicio]
        if data_fim:
            df = df[df['data'] <= data_fim]
        
        # Obter lista de candidatos se não especificado
        if not candidatos:
            # Extrair todos os candidatos mencionados
            todos_candidatos = set()
            for candidatos_item in df['candidatos'].dropna():
                if isinstance(candidatos_item, list):
                    todos_candidatos.update(candidatos_item)
                elif isinstance(candidatos_item, str):
                    try:
                        candidatos_lista = ast.literal_eval(candidatos_item)
                        if isinstance(candidatos_lista, list):
                            todos_candidatos.update(candidatos_lista)
                    except:
                        todos_candidatos.add(candidatos_item)
            
            candidatos = sorted(list(todos_candidatos))
        
        # Analisar cada candidato
        dados_candidatos = {}
        for candidato in candidatos:
            try:
                analise = self.analisar_candidato(
                    candidato=candidato,
                    data_inicio=data_inicio,
                    data_fim=data_fim
                )
                dados_candidatos[candidato] = analise
            except Exception as e:
                print(f"Erro ao analisar candidato {candidato}: {str(e)}")
        
        # Gerar comparativo entre candidatos
        comparativo = {
            'mencoes_totais': {c: dados_candidatos[c]['mencoes_totais'] for c in dados_candidatos},
            'sentimento_positivo': {c: dados_candidatos[c]['sentimento_medio'].get('positivo', 0) for c in dados_candidatos},
            'sentimento_negativo': {c: dados_candidatos[c]['sentimento_medio'].get('negativo', 0) for c in dados_candidatos},
            'sentimento_neutro': {c: dados_candidatos[c]['sentimento_medio'].get('neutro', 0) for c in dados_candidatos},
            'aspectos_predominantes': {c: sorted(dados_candidatos[c]['principais_aspectos'].items(), key=lambda item: item[1], reverse=True)[0][0] 
                                       if dados_candidatos[c]['principais_aspectos'] else "outros" 
                                       for c in dados_candidatos}
        }
        
        return {
            "candidatos": dados_candidatos,
            "comparativo": comparativo
        }

    def detectar_entidades(self, texto: str) -> Dict[str, List[str]]:
        """
        Detecta entidades importantes no texto, como organizações, pessoas e localizações
        """
        entidades = {
            'organizacoes': [],
            'pessoas': [],
            'localizacoes': [],
            'eventos': [],
            'outras': []
        }
        
        if not self.nlp:
            return entidades
            
        doc = self.nlp(texto)
        
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                if ent.text not in entidades['organizacoes']:
                    entidades['organizacoes'].append(ent.text)
            elif ent.label_ == 'PER':
                if ent.text not in entidades['pessoas']:
                    entidades['pessoas'].append(ent.text)
            elif ent.label_ in ['LOC', 'GPE']:
                if ent.text not in entidades['localizacoes']:
                    entidades['localizacoes'].append(ent.text)
            elif ent.label_ == 'EVENT':
                if ent.text not in entidades['eventos']:
                    entidades['eventos'].append(ent.text)
            else:
                if ent.text not in entidades['outras']:
                    entidades['outras'].append(ent.text)
        
        return entidades

    def recomendar_noticias_relacionadas(
        self,
        candidato: Optional[str] = None,
        regiao: Optional[str] = None,
        aspecto: Optional[str] = None,
        sentimento: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Recomenda notícias relacionadas com base em critérios específicos
        """
        if self.df_cache.empty:
            return []
        
        # Criar cópia do dataframe para aplicar filtros
        df = self.df_cache.copy()
        
        # Aplicar filtros se fornecidos
        filtros_aplicados = False
        
        # Filtrar por candidato
        if candidato:
            filtros_aplicados = True
            # Garantir que a coluna candidatos existe e está processada
            if 'candidatos' in df.columns:
                # Converter string para lista se necessário
                if df['candidatos'].dtype == object:
                    df['candidatos_lista'] = df['candidatos'].apply(
                        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else 
                                ([x] if isinstance(x, str) else (x if isinstance(x, list) else []))
                    )
                else:
                    df['candidatos_lista'] = df['candidatos']
                
                # Filtrar por candidato
                df = df[df['candidatos_lista'].apply(lambda x: x is not None and candidato in x)]
        
        # Filtrar por região
        if regiao:
            filtros_aplicados = True
            if 'regiao' in df.columns:
                df = df[df['regiao'].fillna('').str.lower().str.contains(regiao.lower())]
        
        # Filtrar por aspecto
        if aspecto:
            filtros_aplicados = True
            df = df[df['aspecto'] == aspecto]
        
        # Filtrar por sentimento
        if sentimento:
            filtros_aplicados = True
            df = df[df['sentimento'] == sentimento]
        
        # Se nenhum filtro foi aplicado, retornar as notícias mais recentes
        if not filtros_aplicados:
            df = df.sort_values('data', ascending=False).head(limit)
        else:
            # Se poucos resultados, relaxar alguns filtros
            if len(df) < limit and (aspecto or sentimento):
                # Criar novo dataframe com filtros relaxados
                df_relaxado = self.df_cache.copy()
                
                # Manter apenas filtros de candidato e região
                if candidato and 'candidatos' in df_relaxado.columns:
                    df_relaxado['candidatos_lista'] = df_relaxado['candidatos'].apply(
                        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else 
                                ([x] if isinstance(x, str) else (x if isinstance(x, list) else []))
                    )
                    df_relaxado = df_relaxado[df_relaxado['candidatos_lista'].apply(lambda x: x is not None and candidato in x)]
                
                if regiao and 'regiao' in df_relaxado.columns:
                    df_relaxado = df_relaxado[df_relaxado['regiao'].fillna('').str.lower().str.contains(regiao.lower())]
                
                # Remover resultados já incluídos
                if not df.empty:
                    df_relaxado = df_relaxado[~df_relaxado['url'].isin(df['url'])]
                
                # Adicionar até atingir o limite
                if not df_relaxado.empty:
                    df_relaxado = df_relaxado.sort_values('data', ascending=False)
                    num_adicionar = min(limit - len(df), len(df_relaxado))
                    if num_adicionar > 0:
                        df = pd.concat([df, df_relaxado.head(num_adicionar)])
            
            # Limitar ao número especificado
            df = df.sort_values('data', ascending=False).head(limit)
        
        # Converter para lista de dicionários
        noticias = df.to_dict('records')
        
        # Processar campos para garantir formato correto
        noticias_processadas = []
        for noticia in noticias:
            if 'candidatos' in noticia:
                # Converter string para lista
                if isinstance(noticia['candidatos'], str):
                    try:
                        if noticia['candidatos'].startswith('['):
                            noticia['candidatos'] = ast.literal_eval(noticia['candidatos'])
                        else:
                            noticia['candidatos'] = [noticia['candidatos']]
                    except:
                        noticia['candidatos'] = []
            else:
                noticia['candidatos'] = []
            
            if 'regiao' not in noticia or noticia['regiao'] is None:
                noticia['regiao'] = ""
                
            noticias_processadas.append(noticia)
        
        return noticias_processadas 

    def _carregar_dicionario_aspectos(self):
        """
        Carrega ou inicializa o dicionário de aspectos políticos com palavras-chave relacionadas.
        """
        # Dicionário padrão de aspectos políticos
        dicionario_padrao = {
            'economia': ['economia', 'inflação', 'pib', 'fiscal', 'imposto', 'taxa', 'juros', 'dólar', 'banco central', 
                        'mercado', 'desemprego', 'orçamento', 'dívida', 'gastos', 'receita', 'financeiro', 'tributário'],
            
            'congresso': ['congresso', 'senado', 'câmara', 'deputado', 'senador', 'parlamento', 'legislativo', 
                         'comissão', 'plenário', 'projeto de lei', 'votação', 'relator', 'bancada', 'emenda'],
            
            'governo': ['governo', 'presidente', 'ministro', 'executivo', 'planalto', 'gestão', 'administração', 
                       'governador', 'prefeito', 'decreto', 'política', 'mandato', 'medida provisória'],
            
            'outros': ['justiça', 'stf', 'supremo', 'judiciário', 'juiz', 'tribunal', 'processo', 'ação', 'investigação',
                      'eleição', 'candidato', 'urna', 'campanha', 'voto', 'partido', 'coligação', 'pesquisa', 'disputa',
                      'corrupção', 'propina', 'desvio', 'lavagem', 'cpi', 'delação', 'operação', 'polícia federal']
        }
        
        # Tenta carregar de um arquivo se disponível
        try:
            aspectos_file = os.path.join(self.project_root, 'data', 'aspectos_politicos.json')
            if os.path.exists(aspectos_file):
                with open(aspectos_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Salva o dicionário padrão em um arquivo para uso futuro
                os.makedirs(os.path.dirname(aspectos_file), exist_ok=True)
                with open(aspectos_file, 'w', encoding='utf-8') as f:
                    json.dump(dicionario_padrao, f, ensure_ascii=False, indent=2)
                print(f"Dicionário de aspectos políticos criado em {aspectos_file}")
                return dicionario_padrao
        except Exception as e:
            print(f"Erro ao carregar dicionário de aspectos: {str(e)}")
            return dicionario_padrao
    
    def _carregar_lexico_politico(self):
        """
        Carrega ou inicializa um léxico político com palavras associadas a sentimentos.
        """
        # Léxico padrão simplificado
        lexico_padrao = {
            'positivo': ['bom', 'ótimo', 'excelente', 'eficiente', 'eficaz', 'crescimento', 'desenvolvimento',
                        'sucesso', 'avanço', 'progresso', 'benefício', 'ganho', 'aprovado', 'vitória', 'acordo',
                        'recuperação', 'superávit', 'lucro', 'transparente', 'honesto', 'responsável', 'justo'],
            
            'negativo': ['ruim', 'péssimo', 'corrupto', 'corrupção', 'fraude', 'crise', 'problema', 'escândalo',
                        'déficit', 'prejuízo', 'inflação', 'desemprego', 'fracasso', 'derrota', 'recessão',
                        'irregular', 'ilegal', 'denúncia', 'acusação', 'investigação', 'propina', 'superfaturado'],
            
            'neutro': ['anunciar', 'dizer', 'afirmar', 'declarar', 'propor', 'apresentar', 'discutir', 'debater',
                      'analisar', 'considerar', 'avaliar', 'planejar', 'votar', 'deliberar', 'decidir', 'informar']
        }
        
        # Tenta carregar de um arquivo se disponível
        try:
            lexico_file = os.path.join(self.project_root, 'data', 'lexico_politico.json')
            if os.path.exists(lexico_file):
                with open(lexico_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Salva o léxico padrão em um arquivo para uso futuro
                os.makedirs(os.path.dirname(lexico_file), exist_ok=True)
                with open(lexico_file, 'w', encoding='utf-8') as f:
                    json.dump(lexico_padrao, f, ensure_ascii=False, indent=2)
                print(f"Léxico político criado em {lexico_file}")
                return lexico_padrao
        except Exception as e:
            print(f"Erro ao carregar léxico político: {str(e)}")
            return lexico_padrao