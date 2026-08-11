# Ingestão e busca semântica de PDFs

Projeto em Python com LangChain, PostgreSQL e pgVector. Um PDF pode ser enviado por API, é dividido em chunks de 1000 caracteres com sobreposição de 150, convertido em embeddings e usado para responder perguntas sem recorrer a conhecimento externo.

## Requisitos

- Python 3.11+
- Docker e Docker Compose
- Chave da API OpenAI

## Configuração

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instale as dependências e configure o ambiente:

```bash
pip install -r requirements.txt
cp .env.example .env
```

Preencha `OPENAI_API_KEY` no arquivo `.env`.

## Execução

Suba o PostgreSQL com pgVector:

```bash
docker compose up -d
```

Inicie a API:

```bash
uvicorn src.api:app --reload
```

A documentação interativa estará em `http://localhost:8000/docs`.

## Enviar um PDF pela API

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@document.pdf"
```

Guarde o `document_id`. Consulte o estado do processamento:

```bash
curl http://localhost:8000/documents/SEU_DOCUMENT_ID
```

Quando o estado for `ready`, faça uma pergunta:

```bash
curl -X POST http://localhost:8000/questions \
  -H "Content-Type: application/json" \
  -d '{"document_id":"SEU_DOCUMENT_ID","question":"Qual foi o faturamento?"}'
```

## CLI obrigatória

Com a API em execução:

```bash
python src/chat.py
```

Também é possível executar a ingestão diretamente, preservando o fluxo pedido no desafio:

```bash
python src/ingest.py document.pdf
```

## Testes

```bash
pytest
```

## Garantia de contexto

A busca utiliza `similarity_search_with_score(query, k=10)` filtrada pelo `document_id`. O prompt instrui o modelo a responder somente com base nos trechos recuperados. Quando a informação não estiver disponível, a resposta esperada é:

> Não tenho informações necessárias para responder sua pergunta.

