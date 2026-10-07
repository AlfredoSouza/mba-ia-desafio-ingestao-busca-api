import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

ROOT = Path(__file__).resolve().parents[1]
FALLBACK_ANSWER = "Não tenho informações necessárias para responder sua pergunta."

PROMPT_TEMPLATE = """CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def get_settings() -> dict[str, str]:
    load_dotenv(ROOT / ".env")
    settings = {
        "api_key": os.getenv("OPENAI_API_KEY", "").strip(),
        "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip(),
        "chat_model": os.getenv("OPENAI_CHAT_MODEL", "gpt-5-nano").strip(),
        "database_url": os.getenv("DATABASE_URL", "").strip(),
        "collection_name": os.getenv("PG_VECTOR_COLLECTION_NAME", "").strip(),
        "pdf_path": os.getenv("PDF_PATH", "document.pdf").strip(),
    }
    required = {
        "api_key": "OPENAI_API_KEY",
        "database_url": "DATABASE_URL",
        "collection_name": "PG_VECTOR_COLLECTION_NAME",
        "embedding_model": "OPENAI_EMBEDDING_MODEL",
        "chat_model": "OPENAI_CHAT_MODEL",
    }
    missing = [env for key, env in required.items() if not settings[key]]
    if missing:
        raise ValueError("Preencha no .env: " + ", ".join(missing))
    if not settings["database_url"].startswith("postgresql+psycopg://"):
        raise ValueError("DATABASE_URL deve começar com postgresql+psycopg://.")
    return settings


def get_vectorstore(settings: dict[str, str], *, reset: bool = False) -> PGVector:
    embeddings = OpenAIEmbeddings(
        model=settings["embedding_model"], api_key=settings["api_key"]
    )
    return PGVector(
        embeddings=embeddings,
        collection_name=settings["collection_name"],
        connection=settings["database_url"],
        use_jsonb=True,
        pre_delete_collection=reset,
    )


def search_prompt(question: str | None = None):
    settings = get_settings()
    vectorstore = get_vectorstore(settings)
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
    llm = ChatOpenAI(model=settings["chat_model"], api_key=settings["api_key"])

    def answer(pergunta: str) -> str:
        # PGVector gera o embedding da pergunta antes da busca.
        results = vectorstore.similarity_search_with_score(pergunta, k=10)
        if not results:
            return FALLBACK_ANSWER
        contexto = "\n\n".join(document.page_content for document, _score in results)
        response = llm.invoke(prompt.format(contexto=contexto, pergunta=pergunta))
        return str(response.content).strip()

    chain = RunnableLambda(answer)
    return chain if question is None else chain.invoke(question)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Consulta o conteúdo do PDF ingerido.")
    parser.add_argument("question")
    args = parser.parse_args()
    try:
        print(search_prompt(args.question))
    except Exception as exc:
        parser.exit(1, f"Erro na busca: {exc}\n")
