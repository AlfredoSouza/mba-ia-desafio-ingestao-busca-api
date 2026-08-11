from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import get_settings
from src.services.document_service import get_document
from src.vectorstore import get_vectorstore


FALLBACK_ANSWER = "Não tenho informações necessárias para responder sua pergunta."

SYSTEM_PROMPT = """Você responde perguntas exclusivamente com base no CONTEXTO fornecido.

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda exatamente:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.
"""


def answer_question(document_id: UUID, question: str) -> dict:
    document = get_document(document_id)
    if not document:
        raise LookupError("Documento não encontrado.")
    if document["status"] != "ready":
        raise RuntimeError(f"Documento ainda não está pronto. Status: {document['status']}.")

    results = get_vectorstore().similarity_search_with_score(
        question,
        k=10,
        filter={"document_id": {"$eq": str(document_id)}},
    )
    if not results:
        return {"document_id": document_id, "answer": FALLBACK_ANSWER, "sources": []}

    context_parts = []
    sources = []
    for doc, score in results:
        page = doc.metadata.get("page")
        context_parts.append(f"[Página {page + 1 if isinstance(page, int) else '?'}]\n{doc.page_content}")
        sources.append(
            {
                "page": page + 1 if isinstance(page, int) else None,
                "chunk_index": doc.metadata.get("chunk_index"),
                "score": float(score),
                "content": doc.page_content,
            }
        )

    prompt = f'''CONTEXTO:
{chr(10).join(context_parts)}

PERGUNTA DO USUÁRIO:
{question}

RESPONDA A "PERGUNTA DO USUÁRIO"'''
    settings = get_settings()
    llm = ChatOpenAI(model=settings.chat_model, api_key=settings.openai_api_key)
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
    return {"document_id": document_id, "answer": str(response.content).strip(), "sources": sources}
