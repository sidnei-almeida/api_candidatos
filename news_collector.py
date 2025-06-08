import os
from datetime import datetime, timedelta
import time
import random
import json

# Classe de coletor de notícias compatível com a API
class NewsCollector:
    def __init__(self):
        self.sources = {
            'G1': 'G1 - Política',
            'BBC': 'BBC Brasil',
            'UOL': 'UOL Notícias',
            'Estadão': 'Estadão Política'
        }
        
        # Obter o diretório atual
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
        print(f"NewsCollector inicializado com sucesso! Diretório: {self.current_dir}")
    
    def collect_all_news(self):
        """
        Método principal para coleta de notícias.
        Retorna um dicionário com notícias coletadas.
        """
        print("Função de coleta de notícias chamada.")
        print("NOTA: Esta é uma versão simplificada que retorna dados fictícios para teste.")
        
        # Dados de exemplo para teste
        noticias = []
        
        # Carregar candidatos para incluir nos textos
        candidatos = self._carregar_candidatos()
        if not candidatos or len(candidatos) < 3:
            candidatos = ["Lula", "Bolsonaro", "Tarcísio", "Cláudio Castro", "Eduardo Leite", "Romeu Zema"]
        
        # Fontes de notícias
        fontes = {
            'G1': 'G1 - Política',
            'BBC': 'BBC Brasil',
            'UOL': 'UOL Notícias',
            'Estadão': 'Estadão Política',
            'Folha': 'Folha de São Paulo'
        }
        
        # Temas para notícias
        temas = [
            "economia", "inflação", "educação", "saúde", "segurança", 
            "corrupção", "eleições", "congresso", "judiciário", "reforma"
        ]
        
        # Verbos para títulos
        verbos = [
            "anuncia", "critica", "defende", "propõe", "questiona", 
            "discute", "apresenta", "rejeita", "aprova", "veta"
        ]
        
        # Regiões para menções
        regioes = [
            "São Paulo", "Rio de Janeiro", "Brasília", "Minas Gerais", 
            "Nordeste", "Sul", "Norte", "Centro-Oeste", "Amazonas", "Bahia"
        ]
        
        # Gerar 10 notícias para cada fonte
        fontes_stats = {}
        for fonte, origem in fontes.items():
            fonte_noticias = []
            
            # Criar de 10 a 15 notícias por fonte
            num_noticias = random.randint(10, 15)
            for i in range(num_noticias):
                # Selecionar elementos aleatórios
                candidato = random.choice(candidatos)
                tema = random.choice(temas)
                verbo = random.choice(verbos)
                regiao = random.choice(regioes)
                
                # Criar título
                titulo = f"{candidato} {verbo} medidas sobre {tema} em {regiao}"
                
                # Criar texto mais elaborado
                texto = f"Em pronunciamento hoje, {candidato} {verbo} um conjunto de medidas relacionadas a {tema}. "
                texto += f"Durante evento em {regiao}, o político destacou a importância de priorizar este tema. "
                
                # Adicionar menção a outro candidato para ter relações
                outro_candidato = random.choice([c for c in candidatos if c != candidato])
                texto += f"{outro_candidato} também comentou sobre o assunto, expressando opinião contrária. "
                
                # Adicionar mais contexto sobre o tema
                if tema == "economia":
                    texto += "A proposta inclui redução de impostos e incentivos para pequenas empresas. "
                elif tema == "educação":
                    texto += "O plano prevê investimentos em escolas públicas e valorização dos professores. "
                elif tema == "saúde":
                    texto += "As medidas visam melhorar o atendimento no SUS e reduzir filas de espera. "
                elif tema == "segurança":
                    texto += "O projeto pretende aumentar o efetivo policial e modernizar equipamentos. "
                elif tema == "corrupção":
                    texto += "As propostas incluem maior transparência e mecanismos de controle. "
                
                # Adicionar data (últimos 30 dias)
                dias_atras = random.randint(1, 30)
                data = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
                
                # Criar URL fictícia
                url = f"https://exemplo.com/{fonte.lower()}/{tema}/{i+1}"
                
                # Adicionar à lista de notícias
                noticia = {
                    'titulo': titulo,
                    'texto': texto,
                    'data': data,
                    'fonte': fonte,
                    'url': url,
                    'origem': origem,
                    'tema': tema,
                    'regiao': regiao,
                    'candidatos_mencionados': [candidato, outro_candidato]
                }
                
                fonte_noticias.append(noticia)
            
            # Adicionar notícias desta fonte ao total
            noticias.extend(fonte_noticias)
            fontes_stats[fonte] = len(fonte_noticias)
        
        print(f"Total de notícias geradas: {len(noticias)}")
        for fonte, quantidade in fontes_stats.items():
            print(f"- {fonte}: {quantidade} notícias")
        
        return {
            'total': len(noticias),
            'news': noticias,
            'sources': fontes_stats
        }
    
    def _carregar_candidatos(self):
        """Carrega lista de candidatos do arquivo JSON"""
        try:
            candidatos_file = os.path.join(self.current_dir, 'data', 'candidatos.json')
            if os.path.exists(candidatos_file):
                with open(candidatos_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [c['nome'] for c in data.get('candidatos', [])]
            else:
                print(f"Arquivo de candidatos não encontrado: {candidatos_file}")
                return []
        except Exception as e:
            print(f"Erro ao carregar candidatos: {str(e)}")
            return []
    
    # Métodos de compatibilidade com a classe anterior
    def coletar_noticias_g1(self, max_paginas=1):
        """Método de compatibilidade para G1"""
        resultado = self.collect_all_news()
        return [n for n in resultado['news'] if n['fonte'] == 'G1']
    
    def coletar_noticias_bbc(self, max_paginas=1):
        """Método de compatibilidade para BBC"""
        resultado = self.collect_all_news()
        return [n for n in resultado['news'] if n['fonte'] == 'BBC']
    
    def coletar_noticias_uol(self):
        """Método de compatibilidade para UOL"""
        resultado = self.collect_all_news()
        return [n for n in resultado['news'] if n['fonte'] == 'UOL']
    
    def coletar_noticias_estadao(self):
        """Método de compatibilidade para Estadão"""
        resultado = self.collect_all_news()
        return [n for n in resultado['news'] if n['fonte'] == 'Estadão'] 