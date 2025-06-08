# Instruções de Execução da API de Candidatos

Este documento explica como configurar e executar a API de análise de sentimentos para notícias políticas.

## Arquitetura

A API está construída da seguinte forma:

- `main.py`: Contém a definição da API FastAPI e seus endpoints
- `services.py`: Contém a lógica de negócio para processamento e análise de notícias
- `models.py`: Contém os modelos Pydantic para validação de dados
- `news_collector.py`: Contém a lógica para coleta de notícias
- `run.py`: Script para executar a API localmente

## Preparação do Ambiente

### Requisitos

- Python 3.10 ou superior
- Bibliotecas listadas em `requirements.txt`

### Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/api_candidatos.git
   cd api_candidatos
   ```

2. Crie e ative um ambiente virtual (recomendado):
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

## Execução

Para executar a API localmente:

```
python run.py
```

Isto irá:
1. Baixar recursos do NLTK necessários
2. Verificar o modelo spaCy
3. Iniciar o servidor na porta 8000

## Carregamento de Modelos e Dados

A API foi projetada para funcionar de forma flexível com os modelos e arquivos de dados:

1. **Carregamento Inteligente**: A API tenta primeiro carregar os arquivos localmente e, se não encontrar, busca diretamente do GitHub.

2. **Arquivos Carregados Dinamicamente**:
   - `modelo_aspectos.joblib` - Modelo para classificação de aspectos políticos
   - `modelo_sentimentos.joblib` - Modelo para classificação de sentimentos
   - `data/aspectos_politicos.json` - Dicionário de aspectos políticos
   - `data/lexico_politico.json` - Léxico político para análise de sentimentos
   - `data/candidatos.json` - Lista de candidatos políticos
   - `data/noticias_cache.csv` - Cache de notícias coletadas

3. **Deploy no Render**: Para implantação no Render, não é necessário baixar os arquivos previamente, pois a API vai carregá-los diretamente do GitHub durante a execução.

## Endpoints Principais

- `GET /`: Informações sobre a API
- `GET /noticias/`: Obter notícias coletadas
- `GET /noticias/coletar`: Acionar coleta de novas notícias
- `POST /noticias/analisar-texto`: Analisar um texto enviado
- `GET /noticias/por-aspecto/{aspecto}`: Obter notícias por aspecto
- `GET /noticias/por-sentimento/{sentimento}`: Obter notícias por sentimento
- `GET /noticias/candidato/{candidato}/analise`: Obter análise de um candidato

Para mais detalhes, acesse a documentação interativa em `/docs` após iniciar a API.

## Resolução de Problemas

### Se você encontrar problemas com o spaCy

Certifique-se de que o modelo do spaCy está instalado:

```
python -m spacy download pt_core_news_lg
```

### Se os modelos não carregarem

Verifique se os arquivos `modelo_aspectos.joblib` e `modelo_sentimentos.joblib` estão na pasta raiz. Se não estiverem, a API tentará baixá-los do GitHub automaticamente.

## Teste da API

Para testar se a API está funcionando corretamente:

1. Inicie a API usando um dos métodos acima
2. Execute o script de teste simples:

```bash
cd api
python teste_simples.py
```

O script testará os principais endpoints da API e mostrará se tudo está funcionando corretamente.

Para testes mais detalhados, você pode usar o script completo:

```bash
cd api
python test_api.py
```

## Documentação da API

Uma vez que a API esteja em execução, você pode acessar a documentação interativa em:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment

Para deploy no Render.com:

1. Configure seu repositório Git no Render
2. Crie um novo Web Service apontando para a pasta `api`
3. Use as seguintes configurações:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host=0.0.0.0 --port=$PORT`

A configuração também pode ser feita através do arquivo `render.yaml` presente na pasta `api`.

## Solução de Problemas

### Erro: ModuleNotFoundError: No module named 'services'

Se você encontrar o erro `ModuleNotFoundError: No module named 'services'`, significa que está tentando executar a API com um contexto de importação incorreto. Certifique-se de estar executando o script a partir do diretório correto (dentro da pasta `api` ou usando o script `start_api.py` da raiz).

### Erro: AttributeError: 'NoticiaService' object has no attribute '_carregar_dicionario_aspectos'

Este erro indica que está faltando um método na classe `NoticiaService`. Se encontrar este erro, verifique se os métodos `_carregar_dicionario_aspectos` e `_carregar_lexico_politico` estão implementados corretamente no arquivo `services.py`.

### Erro: 422 Unprocessable Entity em /noticias/analisar-texto

Se o endpoint `/noticias/analisar-texto` retornar um erro 422, verifique se está enviando o parâmetro `texto` no formato correto. O endpoint espera um JSON com a estrutura:

```json
{
  "texto": "Seu texto para análise aqui"
}
```

Certifique-se de estar enviando a requisição como `POST` e usando o cabeçalho `Content-Type: application/json`.

Para outros problemas, verifique o log de erros e consulte a documentação das bibliotecas usadas. 