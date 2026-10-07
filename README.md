# Ingestão e Busca Semântica com LangChain e Postgres

Implementação do [desafio da Full Cycle](https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca):
ler um PDF, dividir seu texto, armazenar embeddings no PostgreSQL com pgVector e
responder perguntas pelo terminal com base somente nos trechos recuperados.

## Estrutura

```text
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py
│   ├── search.py
│   └── chat.py
├── document.pdf
└── README.md
```

O PDF incluído é o exemplo do repositório da faculdade. O diretório `tests/`
contém testes que podem ser executados manualmente.

## Requisitos e configuração

- Python 3.11 ou superior.
- Docker com Docker Compose v2.
- Uma chave OpenAI válida com acesso aos modelos configurados.

Crie e ative o ambiente virtual na raiz do projeto:

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
Copy-Item .env.example .env
pip install -r requirements.txt
```

Preencha `OPENAI_API_KEY` no `.env`. O projeto utiliza apenas OpenAI.
Os modelos de embeddings e de chat podem ser alterados por
`OPENAI_EMBEDDING_MODEL` e `OPENAI_CHAT_MODEL`.

Exemplo de configuração (substitua apenas a chave da API):

```dotenv
OPENAI_API_KEY=sua_chave_openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_CHAT_MODEL=gpt-6-luna
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag
PG_VECTOR_COLLECTION_NAME=pdf_desafio
PDF_PATH=document.pdf
```

Use `#` para comentar uma linha no `.env`. A chave precisa ter acesso aos modelos
configurados. `OPENAI_EMBEDDING_MODEL` gera os vetores; `OPENAI_CHAT_MODEL` gera
as respostas. O nome da collection pode ser mantido como `pdf_desafio` e é criado
automaticamente. `PDF_PATH` aponta para o PDF que será ingerido.

As demais variáveis são:

| Variável | Uso |
| --- | --- |
| `DATABASE_URL` | Conexão PostgreSQL com driver psycopg |
| `PG_VECTOR_COLLECTION_NAME` | Collection dedicada ao PDF do desafio |
| `PDF_PATH` | Caminho do PDF, relativo à raiz do projeto ou absoluto |

## Ordem de execução obrigatória

### 1. Subir o banco

```bash
docker compose up -d
```

O Compose segue o exemplo da faculdade: PostgreSQL 17 com pgVector e um
serviço que habilita a extensão após o banco ficar saudável.
Antes da ingestão, confira:

```bash
docker compose ps -a
```

O PostgreSQL deve estar saudável e `bootstrap_vector_ext` deve terminar com
código 0. As credenciais do exemplo são para desenvolvimento local.

### 2. Executar a ingestão

```bash
python src/ingest.py
```

O script lê `PDF_PATH` (por padrão, `document.pdf`), carrega o texto com
`PyPDFLoader` e o divide com `RecursiveCharacterTextSplitter` em chunks de
1000 caracteres, com overlap de 150. Cada chunk recebe um embedding e é
armazenado com `PGVector`.

A ingestão **substitui os vetores da collection configurada** para manter as
respostas restritas ao PDF atual. Use uma collection dedicada ao desafio.
Outras collections não são removidas. PDFs sem texto extraível precisam de OCR,
que não faz parte deste projeto.

Para testar outro PDF:

```bash
python src/ingest.py outro-documento.pdf
```

### 3. Rodar o chat

```bash
python src/chat.py
```

Exemplo de interação:

```text
PERGUNTA: Qual informação consta no documento?
RESPOSTA: ...

PERGUNTA: Qual é a capital da França?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

Digite `sair` para encerrar. A resposta de exemplo fora do contexto é esperada
quando essa informação não consta no PDF.

O chat chama `search.py` diretamente. A pergunta é vetorizada, a busca usa
`similarity_search_with_score(query, k=10)`, os trechos são concatenados no
prompt completo fornecido pela faculdade e a LLM produz a resposta.
Se não houver trechos, o script retorna a frase obrigatória sem chamar a LLM.
As regras do prompt orientam o modelo; valide também perguntas fora do contexto
com uma chave real antes da entrega.

A busca também pode ser chamada diretamente:

```bash
python src/search.py "Sua pergunta sobre o PDF"
```

## Reiniciar e testar novamente

O banco persiste seus dados no volume `faculdade_postgres_data`.
Para reiniciar os containers, sem apagar esse volume:

```bash
docker compose down
docker compose up -d
docker compose ps -a
```

Com o ambiente virtual ativo e o banco saudável, refaça a ingestão e abra o chat:

```bash
python src/ingest.py
python src/chat.py
```

Teste perguntas respondidas explicitamente pelo PDF e perguntas fora do contexto.
A ingestão substitui os vetores da collection configurada em cada execução.
Se houver falha ao gerar os embeddings depois da exclusão, execute a ingestão
novamente antes de consultar.

Ao trocar o modelo de embeddings, refaça a ingestão antes de abrir o chat.
Se houver erro de dimensão no banco, use um banco novo ou recrie o volume.
`docker compose down -v` apaga os dados do volume desta versão.

## Testes

Com o ambiente virtual ativo:

```bash
python -m unittest discover -s tests -v
```

Para incluir o teste de integração, suba o banco e defina `RUN_DB_TESTS=1`:

Linux/macOS:

```bash
RUN_DB_TESTS=1 python -m unittest discover -s tests -v
```

PowerShell:

```powershell
$env:RUN_DB_TESTS = "1"
python -m unittest discover -s tests -v
```

Os testes usam embeddings e LLM simulados, sem consumir a API OpenAI.
O teste de integração usa uma collection de teste separada, PostgreSQL real e
o PDF incluído. Ele verifica gravação, reingestão sem duplicatas e busca.
Não há execução automática pelo GitHub Actions; os testes são executados
pelos comandos acima.

## Referência do desafio

Requisitos e estrutura base:
[Ingestão e Busca Semântica com LangChain e Postgres — Full Cycle](https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca).

Código desta implementação:
[AlfredoSouza/mba-ia-desafio-ingestao-busca-api](https://github.com/AlfredoSouza/mba-ia-desafio-ingestao-busca-api).
