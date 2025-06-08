from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class NoticiaBase(BaseModel):
    titulo: str
    texto: str
    data: str
    fonte: str
    url: str
    origem: str

class NoticiaResponse(NoticiaBase):
    noticia_id: Optional[int] = None
    aspecto: Optional[str] = None
    sentimento: Optional[str] = None
    relevancia: Optional[int] = None
    regiao: Optional[str] = None
    candidatos: Optional[List[str]] = None

class AnaliseDetalhadaItem(BaseModel):
    texto: str
    aspecto: str
    sentimento: str
    relevancia: int

class AspectSentimentResponse(NoticiaBase):
    aspecto: str
    sentimento: str
    relevancia: Optional[int] = None
    analises_detalhadas: Optional[List[AnaliseDetalhadaItem]] = None
    regiao: Optional[str] = None
    candidatos: Optional[List[str]] = None

class EstatisticasResponse(BaseModel):
    total_noticias: int
    noticias_por_fonte: dict
    noticias_por_aspecto: dict
    noticias_por_sentimento: dict
    noticias_por_regiao: Optional[dict] = None
    noticias_por_candidato: Optional[dict] = None
    periodo: dict

class PredicaoRequest(BaseModel):
    texto: str
    preprocessar: Optional[bool] = True

class PredicaoResponse(BaseModel):
    aspecto: str
    sentimento: str
    confianca_aspecto: Optional[float] = None
    confianca_sentimento: Optional[float] = None
    texto_preprocessado: Optional[str] = None
    candidatos_detectados: Optional[List[str]] = None
    regiao_detectada: Optional[str] = None
    entidades: Optional[Dict[str, List[str]]] = None
    palavras_chave: Optional[List[str]] = None
    relevancia: Optional[int] = None
    analises_detalhadas: Optional[List[AnaliseDetalhadaItem]] = None

class ModeloInfo(BaseModel):
    nome: str
    tipo: str
    versao: str
    data_treinamento: Optional[str] = None
    metricas: Optional[Dict] = None
    classes: List[str]

class CandidatoResponse(BaseModel):
    nome: str
    partido: Optional[str] = None
    cargo: Optional[str] = None
    mencoes_totais: int
    sentimento_medio: Dict[str, float]
    principais_aspectos: Dict[str, int]
    regioes: Dict[str, int]

class RegiaoResponse(BaseModel):
    nome: str
    estado: Optional[str] = None
    total_noticias: int
    principais_aspectos: Dict[str, int]
    principais_candidatos: Dict[str, int]
    sentimento_predominante: Dict[str, float] 