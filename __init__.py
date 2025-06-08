"""
API de Análise de Sentimentos em Notícias Políticas

Este pacote contém a implementação da API para coleta e análise 
de sentimentos em notícias políticas brasileiras.
"""

from .models import NoticiaResponse, AspectSentimentResponse, AnaliseDetalhadaItem
from .services import NoticiaService

__version__ = "1.0.0" 