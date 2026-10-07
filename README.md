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

O PDF incluído é o exemplo do repositório da faculdade. Os diretórios
`tests/` e `.github/` contêm apenas a verificação automática.

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
Não envie o `.env` para o GitHub.

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

## Banco e atualização da versão anterior

Esta versão usa `faculdade_postgres_data`, um novo volume para PostgreSQL 17.
O volume PostgreSQL 16 da versão com API é preservado. Não é feita migração
dos documentos antigos; execute a ingestão do PDF novamente.

Se a versão anterior estiver rodando, execute `docker compose down` nela
antes de mudar de branch, para liberar a porta 5432.
Não use `down -v` se quiser preservar os dados antigos.

Para parar esta versão:

```bash
docker compose down
```

Se trocar o modelo de embeddings por outro com dimensão diferente, use um banco
novo ou recrie o volume desta versão e execute a ingestão novamente.
`docker compose down -v` apaga os dados desta versão.

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
O GitHub Actions executa esses testes automaticamente.

## Entrega acadêmica

O enunciado pede um **fork público** do repositório da faculdade.
Esta implementação foi preparada no repositório existente para revisão;
isso não altera sua visibilidade nem o transforma em fork.
Para a entrega, crie um fork público do repositório base e leve os arquivos
desta versão para ele.
