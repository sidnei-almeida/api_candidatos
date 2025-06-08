# Instruções para Execução da API

## Requisitos

Certifique-se de ter instalado:

- Python 3.8+
- pip (gerenciador de pacotes Python)
- Bibliotecas necessárias (listadas em requirements.txt)

## Instalação

1. Instale as dependências:

```bash
cd api
pip install -r requirements.txt
```

2. Certifique-se de que o modelo spaCy está instalado:

```bash
python -m spacy download pt_core_news_lg
```

## Modos de Execução

Há três formas de executar a API:

### 1. Usando o script run.py (dentro da pasta api)

Este é o método recomendado para desenvolvimento local.

```bash
cd api
python run.py
```

### 2. Usando o script start_api.py (na raiz do projeto)

Este método é útil para iniciar a API a partir da raiz do projeto.

```bash
python start_api.py
```

### 3. Usando diretamente o uvicorn (para produção)

```bash
cd api
uvicorn main:app --host=0.0.0.0 --port=8000
```

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