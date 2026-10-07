# Ingestão e busca semântica de PDFs

Projeto em Python com LangChain, PostgreSQL e pgVector. Um PDF pode ser enviado por API, e dividido em chunks de 1000 caracteres com sobreposicao de 150, convertido em embeddings e usado para responder perguntas sem recorrer a conhecimento externo.

## Requisitos

- Docker com Docker Compose v2 (por exemplo, Docker Desktop)
- Chave da API OpenAI para ingestão e perguntas

Não é necessário instalar Python, criar um ambiente virtual ou executar `pip` na sua máquina.

## Configuração inicial

Copie `.env.example` para `.env`:

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Preencha `OPENAI_API_KEY` no arquivo `.env`. Essa configuração é feita uma única vez.
A API pode iniciar sem a chave, mas ingestão e perguntas precisam de uma chave válida.

## Execução

Com o Docker em execução, na raiz do projeto:

```bash
docker compose up
```

Na primeira execução, o Compose constrói a imagem Python e instala as dependências de
`requirements.txt`, sobe o PostgreSQL com pgVector e inicia a API depois que o banco
estiver pronto. A API cria automaticamente a extensão e a tabela de documentos.
Nas próximas execuções, a imagem já construída é reutilizada.

A documentação interativa estará em http://localhost:8000/docs.
O endpoint http://localhost:8000/health informa se a API está respondendo.

Para executar em segundo plano:

```bash
docker compose up -d
```

Para acompanhar os logs e parar os serviços:

```bash
docker compose logs -f api
docker compose down
```

O banco e os PDFs enviados são mantidos em volumes Docker, mesmo após
`docker compose down`. `docker compose down -v` também remove esses dados.

Após alterar o código ou as dependências, reconstrua a imagem:

```bash
docker compose up --build
```

Dentro do container, a API usa o endereço `postgres:5432` para acessar o banco.
O Compose define esse endereço automaticamente, mesmo que o `.env` contenha
`DATABASE_URL` com `localhost` para execução local. O diretório de uploads no
container é `/app/uploads`, persistido pelo volume `uploads_data`.

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
docker compose exec api python -m src.chat
```

Também é possível executar a ingestão diretamente, preservando o fluxo pedido no desafio:

```bash
docker compose cp document.pdf api:/app/uploads/document.pdf
docker compose exec api python -m src.ingest uploads/document.pdf
```

## Testes

```bash
docker compose exec api python -m pytest
```

## Garantia de contexto

A busca utiliza `similarity_search_with_score(query, k=10)` filtrada pelo `document_id`. O prompt instrui o modelo a responder somente com base nos trechos recuperados. Quando a informação não estiver disponível, a resposta esperada é:

> Não tenho informações necessárias para responder sua pergunta.

