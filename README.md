# API de Análise de Sentimentos em Notícias Políticas

API para coleta e análise de sentimentos em notícias políticas brasileiras, utilizando processamento de linguagem natural e classificação de aspectos e sentimentos.

## Funcionalidades

- Coleta de notícias políticas de diversas fontes brasileiras
- Pré-processamento de texto com SpaCy
- Classificação de aspectos (congresso, economia, governo, outros, etc.)
- Análise de sentimentos (positivo, negativo, neutro)
- Divisão de textos em orações para análise detalhada
- Estatísticas sobre notícias coletadas
- Previsão direta de aspectos e sentimentos usando modelos pré-treinados

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/api_candidatos.git
cd api_candidatos
```

2. Instale as dependências:
```bash
pip install -r api/requirements.txt
```

3. Execute o script de inicialização para baixar recursos necessários:
```bash
python -m api.run
```

## Uso

### Executar a API

```bash
python -m api.run
```

A API estará disponível em `http://localhost:8000`. A documentação interativa estará disponível em `http://localhost:8000/docs`.

### Endpoints Principais

- **GET /noticias/**: Lista as notícias coletadas com filtros opcionais
- **GET /noticias/coletar**: Coleta novas notícias de todas as fontes
- **GET /noticias/analise**: Lista notícias com análise de aspecto e sentimento
- **POST /noticias/analisar-texto**: Analisa um texto fornecido pelo usuário
- **GET /noticias/por-aspecto/{aspecto}**: Lista notícias filtradas por aspecto
- **GET /noticias/por-sentimento/{sentimento}**: Lista notícias filtradas por sentimento
- **GET /noticias/estatisticas**: Retorna estatísticas sobre as notícias coletadas
- **GET /noticias/fontes**: Lista as fontes de notícias disponíveis
- **GET /noticias/aspectos**: Lista os aspectos disponíveis
- **GET /noticias/sentimentos**: Lista os sentimentos disponíveis

### Endpoints de Previsão com Modelos

- **POST /modelos/prever**: Realiza previsão de aspecto e sentimento usando os modelos pré-treinados
- **POST /modelos/prever-aspecto**: Realiza previsão apenas do aspecto
- **POST /modelos/prever-sentimento**: Realiza previsão apenas do sentimento
- **GET /modelos/info**: Retorna informações sobre os modelos carregados

## Exemplos de Uso

### Coletar notícias
```bash
curl -X GET "http://localhost:8000/noticias/coletar"
```

### Listar notícias com análise
```bash
curl -X GET "http://localhost:8000/noticias/analise?limit=10"
```

### Analisar um texto específico
```bash
curl -X POST "http://localhost:8000/noticias/analisar-texto?texto=O%20governo%20federal%20anunciou%20hoje%20novas%20medidas%20econ%C3%B4micas"
```

### Prever aspecto e sentimento com modelos
```bash
curl -X POST "http://localhost:8000/modelos/prever" \
     -H "Content-Type: application/json" \
     -d '{"texto": "O governo federal anunciou hoje novas medidas econômicas", "preprocessar": true}'
```

### Obter estatísticas
```bash
curl -X GET "http://localhost:8000/noticias/estatisticas"
```

### Obter informações dos modelos
```bash
curl -X GET "http://localhost:8000/modelos/info"
```

## Arquitetura

A API é construída com FastAPI e utiliza os seguintes componentes:

- **NoticiaService**: Responsável pela coleta, processamento e análise de notícias
- **SpaCy**: Para processamento de linguagem natural
- **Modelos de classificação**: Para identificação de aspectos e sentimentos
- **Léxicos enriquecidos**: Para análise baseada em regras quando necessário

## Observações

- A API salva os dados coletados em um arquivo CSV no diretório `data/`
- Os modelos de classificação são carregados do diretório da API
- A API tenta usar modelos pré-treinados primeiro, mas tem fallback para análise baseada em regras 