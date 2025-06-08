from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import joblib
import os
import sys
from datetime import datetime
import ast
import pandas as pd
import numpy as np

# Importações locais (de acordo com o contexto de execução)
try:
    # Tenta importar de forma relativa (quando usado como módulo)
    from .services import NoticiaService
    from .models import NoticiaResponse, AspectSentimentResponse, AnaliseDetalhadaItem, PredicaoRequest, PredicaoResponse, CandidatoResponse, RegiaoResponse
except ImportError:
    # Tenta importar diretamente (quando executado diretamente)
    from services import NoticiaService
    from models import NoticiaResponse, AspectSentimentResponse, AnaliseDetalhadaItem, PredicaoRequest, PredicaoResponse, CandidatoResponse, RegiaoResponse

# Initialize FastAPI app
app = FastAPI(
    title="API de Análise de Sentimentos em Notícias Políticas",
    description="API para coleta e análise de sentimentos em notícias políticas brasileiras",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
noticia_service = NoticiaService()

# Função auxiliar para processar campos das notícias
def processar_campos_noticia(noticia: Dict) -> Dict:
    """Processa campos de notícia para garantir tipos de dados corretos"""
    # Processar campo 'candidatos'
    if 'candidatos' not in noticia:
        noticia['candidatos'] = []
    elif noticia['candidatos'] is None:
        noticia['candidatos'] = []
    elif isinstance(noticia['candidatos'], (list, np.ndarray)) and hasattr(noticia['candidatos'], '__iter__') and not isinstance(noticia['candidatos'], str):
        if pd.isna(noticia['candidatos']).any():
            noticia['candidatos'] = []
    elif pd.isna(noticia['candidatos']):
        noticia['candidatos'] = []
    elif isinstance(noticia['candidatos'], str):
        # Converter string para lista
        if noticia['candidatos'].startswith('[') and noticia['candidatos'].endswith(']'):
            # É uma representação de string de uma lista
            try:
                noticia['candidatos'] = ast.literal_eval(noticia['candidatos'])
            except:
                # Se falhar, criar uma lista com base na string
                texto = noticia['candidatos'].strip('[]')
                if texto:
                    # Separar em itens, remover aspas e espaços extras
                    candidatos = [c.strip().strip("'\"") for c in texto.split(',')]
                    noticia['candidatos'] = candidatos
                else:
                    noticia['candidatos'] = []
        else:
            # É uma string simples
            noticia['candidatos'] = [noticia['candidatos']]
            
    # Verificar se o campo 'regiao' existe e é válido
    if 'regiao' not in noticia or noticia['regiao'] is None or pd.isna(noticia['regiao']):
        noticia['regiao'] = ""
    
    # Tratar valores NaN no campo 'data'
    if 'data' not in noticia or noticia['data'] is None or pd.isna(noticia['data']):
        noticia['data'] = datetime.now().strftime("%Y-%m-%d")
    
    # Verificar outros campos string e substituir NaN por strings vazias
    for campo in ['titulo', 'texto', 'fonte', 'url', 'origem']:
        if campo not in noticia or noticia[campo] is None or pd.isna(noticia[campo]):
            noticia[campo] = ""
    
    # Verificar campos numéricos e substituir NaN por 0
    if 'relevancia' not in noticia or noticia['relevancia'] is None or pd.isna(noticia['relevancia']):
        noticia['relevancia'] = 0
    
    # Verificar campos de aspecto e sentimento
    if 'aspecto' not in noticia or noticia['aspecto'] is None or pd.isna(noticia['aspecto']):
        noticia['aspecto'] = "outros"
    
    if 'sentimento' not in noticia or noticia['sentimento'] is None or pd.isna(noticia['sentimento']):
        noticia['sentimento'] = "neutro"
    
    # Verificar análises detalhadas
    if 'analises_detalhadas' not in noticia:
        noticia['analises_detalhadas'] = [{
            'texto': noticia.get('texto', ''),
            'aspecto': noticia.get('aspecto', 'outros'),
            'sentimento': noticia.get('sentimento', 'neutro'),
            'relevancia': noticia.get('relevancia', 0)
        }]
    elif noticia['analises_detalhadas'] is None:
        noticia['analises_detalhadas'] = [{
            'texto': noticia.get('texto', ''),
            'aspecto': noticia.get('aspecto', 'outros'),
            'sentimento': noticia.get('sentimento', 'neutro'),
            'relevancia': noticia.get('relevancia', 0)
        }]
    else:
        # Tratar com segurança, verificando o tipo do objeto
        try:
            # Se for uma lista vazia
            if isinstance(noticia['analises_detalhadas'], list) and len(noticia['analises_detalhadas']) == 0:
                noticia['analises_detalhadas'] = [{
                    'texto': noticia.get('texto', ''),
                    'aspecto': noticia.get('aspecto', 'outros'),
                    'sentimento': noticia.get('sentimento', 'neutro'),
                    'relevancia': noticia.get('relevancia', 0)
                }]
            # Se for um array numpy
            elif isinstance(noticia['analises_detalhadas'], np.ndarray):
                if len(noticia['analises_detalhadas']) == 0 or pd.isna(noticia['analises_detalhadas']).all():
                    noticia['analises_detalhadas'] = [{
                        'texto': noticia.get('texto', ''),
                        'aspecto': noticia.get('aspecto', 'outros'),
                        'sentimento': noticia.get('sentimento', 'neutro'),
                        'relevancia': noticia.get('relevancia', 0)
                    }]
            # Se for um valor único (não-lista)
            elif not isinstance(noticia['analises_detalhadas'], list):
                if pd.isna(noticia['analises_detalhadas']):
                    noticia['analises_detalhadas'] = [{
                        'texto': noticia.get('texto', ''),
                        'aspecto': noticia.get('aspecto', 'outros'),
                        'sentimento': noticia.get('sentimento', 'neutro'),
                        'relevancia': noticia.get('relevancia', 0)
                    }]
        except Exception as e:
            # Em caso de erro, garantir que há um valor padrão
            print(f"Erro ao processar análises detalhadas: {str(e)}")
            noticia['analises_detalhadas'] = [{
                'texto': noticia.get('texto', ''),
                'aspecto': noticia.get('aspecto', 'outros'),
                'sentimento': noticia.get('sentimento', 'neutro'),
                'relevancia': noticia.get('relevancia', 0)
            }]
    
    return noticia

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "API de Análise de Sentimentos em Notícias Políticas",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/noticias/", response_model=List[NoticiaResponse])
async def get_noticias(
    fonte: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    limit: int = 50
):
    """
    Get latest news with optional filters
    """
    try:
        noticias = noticia_service.get_noticias(
            fonte=fonte,
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=limit
        )
        # Verificar se a lista de notícias está vazia
        if not noticias:
            return []
            
        # Garantir que o campo 'candidatos' seja sempre uma lista válida
        noticias_processadas = []
        for noticia in noticias:
            # Processar campo 'candidatos'
            if 'candidatos' not in noticia:
                noticia['candidatos'] = []
            elif noticia['candidatos'] is None:
                noticia['candidatos'] = []
            elif isinstance(noticia['candidatos'], str):
                # Converter string para lista
                if noticia['candidatos'].startswith('[') and noticia['candidatos'].endswith(']'):
                    # É uma representação de string de uma lista
                    try:
                        import ast
                        noticia['candidatos'] = ast.literal_eval(noticia['candidatos'])
                    except:
                        # Se falhar, criar uma lista com base na string
                        texto = noticia['candidatos'].strip('[]')
                        if texto:
                            # Separar em itens, remover aspas e espaços extras
                            candidatos = [c.strip().strip("'\"") for c in texto.split(',')]
                            noticia['candidatos'] = candidatos
                        else:
                            noticia['candidatos'] = []
                else:
                    # É uma string simples
                    noticia['candidatos'] = [noticia['candidatos']]
                    
            # Verificar se o campo 'regiao' existe e é válido
            if 'regiao' not in noticia or noticia['regiao'] is None:
                noticia['regiao'] = ""
            
            # Tratar valores NaN no campo 'data'
            if 'data' not in noticia or noticia['data'] is None or pd.isna(noticia['data']):
                noticia['data'] = datetime.now().strftime("%Y-%m-%d")
                
            # Verificar outros campos string e substituir NaN por strings vazias
            for campo in ['titulo', 'texto', 'fonte', 'url', 'origem']:
                if campo not in noticia or noticia[campo] is None or pd.isna(noticia[campo]):
                    noticia[campo] = ""
                
            noticias_processadas.append(noticia)
            
        return noticias_processadas
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter notícias: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/coletar")
async def coletar_noticias():
    """
    Trigger news collection from all sources
    """
    try:
        result = noticia_service.coletar_todas_noticias()
        return {
            "message": "Coleta de notícias concluída com sucesso",
            "total_coletadas": result["total_coletadas"],
            "fontes": result["fontes"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/analise", response_model=List[AspectSentimentResponse])
async def analisar_noticias(
    fonte: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    limit: int = 50
):
    """
    Get news with aspect and sentiment analysis
    """
    try:
        noticias = noticia_service.get_noticias_com_analise(
            fonte=fonte,
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=limit
        )
        # Se a lista de notícias estiver vazia, retornar lista vazia
        if not noticias:
            return []
            
        # Verificar se as notícias estão no formato esperado
        noticias_validadas = []
        for noticia in noticias:
            try:
                # Garantir que campos obrigatórios existam
                noticia_validada = {
                    'titulo': noticia.get('titulo', ""),
                    'texto': noticia.get('texto', ""),
                    'data': noticia.get('data', datetime.now().strftime("%Y-%m-%d")),
                    'fonte': noticia.get('fonte', "Desconhecida"),
                    'url': noticia.get('url', ""),
                    'origem': noticia.get('origem', ""),
                    'aspecto': noticia.get('aspecto', "outros"),
                    'sentimento': noticia.get('sentimento', "neutro"),
                    'relevancia': noticia.get('relevancia', 0)
                }
                
                # Adicionar análises detalhadas se existirem
                if 'analises_detalhadas' in noticia and isinstance(noticia['analises_detalhadas'], list):
                    noticia_validada['analises_detalhadas'] = noticia['analises_detalhadas']
                else:
                    # Criar análise detalhada padrão baseada no texto completo
                    noticia_validada['analises_detalhadas'] = [{
                        'texto': noticia.get('texto', ""),
                        'aspecto': noticia.get('aspecto', "outros"),
                        'sentimento': noticia.get('sentimento', "neutro"),
                        'relevancia': noticia.get('relevancia', 0)
                    }]
                
                # Processar campos especiais como candidatos e regiao
                noticia_validada = processar_campos_noticia(noticia_validada)
                
                noticias_validadas.append(noticia_validada)
            except Exception as e:
                print(f"Erro ao validar notícia: {str(e)}")
                # Pular esta notícia
                continue
        
        return noticias_validadas
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao analisar notícias: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Erro ao analisar notícias: {str(e)}")

@app.post("/noticias/analisar-texto")
async def analisar_texto(request: PredicaoRequest = Body(...)):
    """
    Analyze a text for aspect and sentiment
    """
    try:
        resultado = noticia_service.analisar_texto_completo(request.texto)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modelos/prever", response_model=PredicaoResponse)
async def prever_aspecto_sentimento(request: PredicaoRequest = Body(...)):
    """
    Predict aspect and sentiment using pre-trained models
    """
    try:
        resultado = noticia_service.prever_com_modelos(request.texto)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modelos/prever-aspecto")
async def prever_aspecto(request: PredicaoRequest = Body(...)):
    """
    Predict only aspect using pre-trained model
    """
    try:
        resultado = noticia_service.prever_aspecto(request.texto)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modelos/prever-sentimento")
async def prever_sentimento(request: PredicaoRequest = Body(...)):
    """
    Predict only sentiment using pre-trained model
    """
    try:
        resultado = noticia_service.prever_sentimento(request.texto)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/por-aspecto/{aspecto}")
async def get_noticias_por_aspecto(
    aspecto: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    limit: int = 50
):
    """
    Get news filtered by aspect
    """
    try:
        noticias = noticia_service.get_noticias_com_analise(
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=limit
        )
        # Se a lista de notícias estiver vazia, retornar lista vazia
        if not noticias:
            return []
            
        # Filtrar por aspecto
        noticias_filtradas = []
        
        for noticia in noticias:
            if noticia.get('aspecto') == aspecto:
                try:
                    # Criar uma cópia da notícia para processar
                    noticia_copia = noticia.copy()
                    
                    # Verificar se analises_detalhadas é uma string e converter para lista
                    if 'analises_detalhadas' in noticia_copia and isinstance(noticia_copia['analises_detalhadas'], str):
                        try:
                            import ast
                            noticia_copia['analises_detalhadas'] = ast.literal_eval(noticia_copia['analises_detalhadas'])
                        except:
                            noticia_copia['analises_detalhadas'] = [{
                                'texto': noticia_copia.get('texto', ''),
                                'aspecto': noticia_copia.get('aspecto', 'outros'),
                                'sentimento': noticia_copia.get('sentimento', 'neutro'),
                                'relevancia': noticia_copia.get('relevancia', 0)
                            }]
                    
                    # Garantir que analises_detalhadas seja uma lista válida para evitar erro
                    if 'analises_detalhadas' in noticia_copia:
                        if not isinstance(noticia_copia['analises_detalhadas'], list):
                            noticia_copia['analises_detalhadas'] = [{
                                'texto': noticia_copia.get('texto', ''),
                                'aspecto': noticia_copia.get('aspecto', 'outros'),
                                'sentimento': noticia_copia.get('sentimento', 'neutro'),
                                'relevancia': noticia_copia.get('relevancia', 0)
                            }]
                    
                    # Processar campos especiais
                    noticia_processada = processar_campos_noticia(noticia_copia)
                    noticias_filtradas.append(noticia_processada)
                except Exception as e:
                    print(f"Erro ao processar notícia por aspecto: {str(e)}")
                    # Adicionar versão simplificada da notícia sem processamento
                    noticia_simples = {
                        'titulo': noticia.get('titulo', ''),
                        'texto': noticia.get('texto', ''),
                        'data': noticia.get('data', ''),
                        'fonte': noticia.get('fonte', ''),
                        'url': noticia.get('url', ''),
                        'aspecto': noticia.get('aspecto', 'outros'),
                        'sentimento': noticia.get('sentimento', 'neutro'),
                        'candidatos': [],
                        'regiao': noticia.get('regiao', ''),
                        'relevancia': noticia.get('relevancia', 0),
                        'analises_detalhadas': [{
                            'texto': noticia.get('texto', ''),
                            'aspecto': noticia.get('aspecto', 'outros'),
                            'sentimento': noticia.get('sentimento', 'neutro'),
                            'relevancia': noticia.get('relevancia', 0)
                        }]
                    }
                    noticias_filtradas.append(noticia_simples)
        
        return noticias_filtradas
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter notícias por aspecto: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/por-sentimento/{sentimento}")
async def get_noticias_por_sentimento(
    sentimento: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    limit: int = 50
):
    """
    Get news filtered by sentiment
    """
    try:
        noticias = noticia_service.get_noticias_com_analise(
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=limit
        )
        # Se a lista de notícias estiver vazia, retornar lista vazia
        if not noticias:
            return []
            
        # Filtrar por sentimento
        noticias_filtradas = []
        
        for noticia in noticias:
            if noticia.get('sentimento') == sentimento:
                try:
                    # Criar uma cópia da notícia para processar
                    noticia_copia = noticia.copy()
                    
                    # Verificar se analises_detalhadas é uma string e converter para lista
                    if 'analises_detalhadas' in noticia_copia and isinstance(noticia_copia['analises_detalhadas'], str):
                        try:
                            import ast
                            noticia_copia['analises_detalhadas'] = ast.literal_eval(noticia_copia['analises_detalhadas'])
                        except:
                            noticia_copia['analises_detalhadas'] = [{
                                'texto': noticia_copia.get('texto', ''),
                                'aspecto': noticia_copia.get('aspecto', 'outros'),
                                'sentimento': noticia_copia.get('sentimento', 'neutro'),
                                'relevancia': noticia_copia.get('relevancia', 0)
                            }]
                    
                    # Garantir que analises_detalhadas seja uma lista válida para evitar erro
                    if 'analises_detalhadas' in noticia_copia:
                        if not isinstance(noticia_copia['analises_detalhadas'], list):
                            noticia_copia['analises_detalhadas'] = [{
                                'texto': noticia_copia.get('texto', ''),
                                'aspecto': noticia_copia.get('aspecto', 'outros'),
                                'sentimento': noticia_copia.get('sentimento', 'neutro'),
                                'relevancia': noticia_copia.get('relevancia', 0)
                            }]
                    
                    # Processar campos especiais
                    noticia_processada = processar_campos_noticia(noticia_copia)
                    noticias_filtradas.append(noticia_processada)
                except Exception as e:
                    print(f"Erro ao processar notícia por sentimento: {str(e)}")
                    # Adicionar versão simplificada da notícia sem processamento
                    noticia_simples = {
                        'titulo': noticia.get('titulo', ''),
                        'texto': noticia.get('texto', ''),
                        'data': noticia.get('data', ''),
                        'fonte': noticia.get('fonte', ''),
                        'url': noticia.get('url', ''),
                        'aspecto': noticia.get('aspecto', 'outros'),
                        'sentimento': noticia.get('sentimento', 'neutro'),
                        'candidatos': [],
                        'regiao': noticia.get('regiao', ''),
                        'relevancia': noticia.get('relevancia', 0),
                        'analises_detalhadas': [{
                            'texto': noticia.get('texto', ''),
                            'aspecto': noticia.get('aspecto', 'outros'),
                            'sentimento': noticia.get('sentimento', 'neutro'),
                            'relevancia': noticia.get('relevancia', 0)
                        }]
                    }
                    noticias_filtradas.append(noticia_simples)
        
        return noticias_filtradas
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter notícias por sentimento: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/estatisticas")
async def get_estatisticas():
    """
    Get statistics about collected news
    """
    try:
        return noticia_service.get_estatisticas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/fontes")
async def get_fontes():
    """
    Get list of available news sources
    """
    try:
        return noticia_service.get_fontes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/aspectos")
async def get_aspectos():
    """
    Get list of available aspects
    """
    try:
        estatisticas = noticia_service.get_estatisticas()
        if 'noticias_por_aspecto' not in estatisticas or not estatisticas['noticias_por_aspecto']:
            return []
        aspectos = list(estatisticas['noticias_por_aspecto'].keys())
        return aspectos
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter aspectos: {str(e)}\n{error_details}")
        return []

@app.get("/noticias/sentimentos")
async def get_sentimentos():
    """
    Get list of available sentiments
    """
    try:
        estatisticas = noticia_service.get_estatisticas()
        if 'noticias_por_sentimento' not in estatisticas or not estatisticas['noticias_por_sentimento']:
            return []
        sentimentos = list(estatisticas['noticias_por_sentimento'].keys())
        return sentimentos
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter sentimentos: {str(e)}\n{error_details}")
        return []

@app.get("/modelos/info")
async def get_modelos_info():
    """
    Get information about the trained models
    """
    try:
        info = noticia_service.get_modelos_info()
        return info
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter informações dos modelos: {str(e)}\n{error_details}")
        # Retornar informações básicas em caso de erro
        return {
            'erro': str(e),
            'modelos_disponiveis': {
                'aspectos': noticia_service.modelo_aspectos is not None,
                'sentimentos': noticia_service.modelo_sentimentos is not None
            },
            'aspectos_possiveis': list(noticia_service.label_mappings['aspects'].keys()) if hasattr(noticia_service, 'label_mappings') else [],
            'sentimentos_possiveis': list(noticia_service.label_mappings['sentiments'].keys()) if hasattr(noticia_service, 'label_mappings') else [],
            'versao_api': '1.0.0'
        }

@app.get("/noticias/por-candidato/{candidato}")
async def get_noticias_por_candidato(
    candidato: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    limit: int = 50
):
    """
    Get news filtered by mentioned candidate
    """
    try:
        noticias = noticia_service.get_noticias_com_analise(
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=limit
        )
        # Se a lista de notícias estiver vazia, retornar lista vazia
        if not noticias:
            return []
            
        # Processar todas as notícias primeiro para garantir que 'candidatos' seja uma lista
        noticias_processadas = [processar_campos_noticia(noticia) for noticia in noticias]
        
        # Filtrar por candidato
        noticias_filtradas = []
        
        for noticia in noticias_processadas:
            if 'candidatos' in noticia and noticia['candidatos'] and candidato in noticia['candidatos']:
                # Verificar se analises_detalhadas é uma string e converter para lista
                if 'analises_detalhadas' in noticia and isinstance(noticia['analises_detalhadas'], str):
                    try:
                        import ast
                        noticia['analises_detalhadas'] = ast.literal_eval(noticia['analises_detalhadas'])
                    except:
                        # Se falhar, criar uma análise detalhada padrão
                        noticia['analises_detalhadas'] = [{
                            'texto': noticia.get('texto', ''),
                            'aspecto': noticia.get('aspecto', 'outros'),
                            'sentimento': noticia.get('sentimento', 'neutro'),
                            'relevancia': noticia.get('relevancia', 0)
                        }]
                noticias_filtradas.append(noticia)
        
        return noticias_filtradas
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter notícias por candidato: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/por-regiao/{regiao}")
async def get_noticias_por_regiao(
    regiao: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    limit: int = 50
):
    """
    Get news filtered by region
    """
    try:
        noticias = noticia_service.get_noticias_com_analise(
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=limit
        )
        # Se a lista de notícias estiver vazia, retornar lista vazia
        if not noticias:
            return []
            
        # Processar todas as notícias primeiro para garantir que 'regiao' seja uma string
        noticias_processadas = [processar_campos_noticia(noticia) for noticia in noticias]
        
        # Filtrar por região
        noticias_filtradas = []
        
        for noticia in noticias_processadas:
            if 'regiao' in noticia and noticia['regiao'] and regiao.lower() in noticia['regiao'].lower():
                # Verificar se analises_detalhadas é uma string e converter para lista
                if 'analises_detalhadas' in noticia and isinstance(noticia['analises_detalhadas'], str):
                    try:
                        import ast
                        noticia['analises_detalhadas'] = ast.literal_eval(noticia['analises_detalhadas'])
                    except:
                        # Se falhar, criar uma análise detalhada padrão
                        noticia['analises_detalhadas'] = [{
                            'texto': noticia.get('texto', ''),
                            'aspecto': noticia.get('aspecto', 'outros'),
                            'sentimento': noticia.get('sentimento', 'neutro'),
                            'relevancia': noticia.get('relevancia', 0)
                        }]
                noticias_filtradas.append(noticia)
        
        return noticias_filtradas
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter notícias por região: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/candidatos", response_model=List[str])
async def get_candidatos():
    """
    Get list of candidates mentioned in the news
    """
    try:
        candidatos = noticia_service.get_candidatos()
        return candidatos
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter candidatos: {str(e)}\n{error_details}")
        return []

@app.get("/noticias/regioes", response_model=List[str])
async def get_regioes():
    """
    Get list of regions mentioned in the news
    """
    try:
        regioes = noticia_service.get_regioes()
        return regioes
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter regiões: {str(e)}\n{error_details}")
        return []

@app.get("/noticias/candidato/{candidato}/analise", response_model=CandidatoResponse)
async def get_analise_candidato(
    candidato: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """
    Get analysis of a candidate based on news mentions
    """
    try:
        analise = noticia_service.analisar_candidato(
            candidato=candidato,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        return analise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao analisar candidato: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/regiao/{regiao}/analise", response_model=RegiaoResponse)
async def get_analise_regiao(
    regiao: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """
    Get analysis of a region based on news
    """
    try:
        analise = noticia_service.analisar_regiao(
            regiao=regiao,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        return analise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao analisar região: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/mapa-temas-regionais")
async def get_mapa_temas_regionais(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """
    Get map of regional topics based on news analysis
    """
    try:
        mapa = noticia_service.get_mapa_temas_regionais(
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        return mapa
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter mapa de temas regionais: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/painel-candidatos")
async def get_painel_candidatos(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    candidatos: Optional[List[str]] = Query(None)
):
    """
    Get panel data for candidates based on news analysis
    """
    try:
        painel = noticia_service.get_painel_candidatos(
            data_inicio=data_inicio,
            data_fim=data_fim,
            candidatos=candidatos
        )
        return painel
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao obter painel de candidatos: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/noticias/analise-contextual")
async def analise_contextual(request: PredicaoRequest = Body(...)):
    """
    Realiza uma análise contextual aprofundada de um texto, incluindo:
    - Aspectos e sentimentos
    - Detecção de candidatos, regiões e entidades
    - Palavras-chave e termos relevantes
    - Análise por sentenças
    """
    try:
        # Usar a versão enriquecida do prever_com_modelos
        resultado = noticia_service.prever_com_modelos(request.texto, request.preprocessar)
        
        # Adicionar timestamp para referência
        resultado['timestamp'] = datetime.now().isoformat()
        
        return resultado
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro na análise contextual: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/noticias/recomendacoes")
async def recomendar_noticias(
    candidato: Optional[str] = None,
    regiao: Optional[str] = None,
    aspecto: Optional[str] = None,
    sentimento: Optional[str] = None,
    limit: int = 5
):
    """
    Recomenda notícias relacionadas com base em diferentes critérios.
    Você pode filtrar por candidato, região, aspecto ou sentimento.
    """
    try:
        noticias = noticia_service.recomendar_noticias_relacionadas(
            candidato=candidato,
            regiao=regiao,
            aspecto=aspecto,
            sentimento=sentimento,
            limit=limit
        )
        
        return noticias
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao recomendar notícias: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Configurar o ambiente
    try:
        # Tenta importar de forma relativa (quando usado como módulo)
        try:
            from .setup import setup_environment
            setup_environment()
        except ImportError:
            # Tenta importar diretamente (quando executado diretamente)
            from setup import setup_environment
            setup_environment()
    except ImportError:
        print("Módulo setup não encontrado. Pulando configuração automática.")
    
    # Iniciar servidor
    import uvicorn
    
    # Ajustar para usar o app diretamente, não através do nome do módulo
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000))) 