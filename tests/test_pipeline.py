import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import chat
import ingest
import search
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


SETTINGS = {
    "api_key": "test-key",
    "embedding_model": "test-embeddings",
    "chat_model": "test-chat",
    "database_url": "postgresql+psycopg://postgres:postgres@localhost:5432/rag",
    "collection_name": "desafio_integration_test",
    "pdf_path": "document.pdf",
}


class PipelineTests(unittest.TestCase):
    def test_ingest_splits_with_required_overlap_and_stores_all_chunks(self):
        store = Mock()
        content = "a" * 1800
        loader = Mock()
        loader.load.return_value = [Document(page_content=content)]
        with patch.object(ingest, "get_settings", return_value=SETTINGS), \
             patch.object(ingest, "PyPDFLoader", return_value=loader), \
             patch.object(ingest, "get_vectorstore", return_value=store), \
             redirect_stdout(io.StringIO()):
            count = ingest.ingest_pdf()
        chunks = store.add_documents.call_args.args[0]
        self.assertEqual(count, 2)
        self.assertEqual([len(chunk.page_content) for chunk in chunks], [1000, 950])
        self.assertEqual(chunks[1].metadata["start_index"], 850)
        self.assertEqual(store.add_documents.call_args.kwargs["ids"], ["pdf-chunk-0", "pdf-chunk-1"])

    def test_empty_pdf_does_not_clear_existing_collection(self):
        loader = Mock()
        loader.load.return_value = []
        with patch.object(ingest, "get_settings", return_value=SETTINGS), \
             patch.object(ingest, "PyPDFLoader", return_value=loader), \
             patch.object(ingest, "get_vectorstore") as store:
            with self.assertRaisesRegex(ValueError, "texto extraível"):
                ingest.ingest_pdf()
            store.assert_not_called()

    def test_search_requests_ten_chunks_and_uses_complete_prompt(self):
        store = Mock()
        store.similarity_search_with_score.return_value = [
            (Document(page_content="Faturamento: 10 milhões."), 0.2)
        ]
        llm = Mock()
        llm.invoke.return_value = SimpleNamespace(content="10 milhões.")
        with patch.object(search, "get_settings", return_value=SETTINGS), \
             patch.object(search, "get_vectorstore", return_value=store), \
             patch.object(search, "ChatOpenAI", return_value=llm):
            answer = search.search_prompt("Qual o faturamento?")
        self.assertEqual(answer, "10 milhões.")
        store.similarity_search_with_score.assert_called_once_with("Qual o faturamento?", k=10)
        prompt = llm.invoke.call_args.args[0]
        self.assertIn("CONTEXTO:\nFaturamento: 10 milhões.", prompt)
        self.assertIn("EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:", prompt)
        self.assertIn("Nunca invente ou use conhecimento externo.", prompt)
        self.assertIn("PERGUNTA DO USUÁRIO:\nQual o faturamento?", prompt)

    def test_no_results_returns_required_answer_without_llm_call(self):
        store = Mock()
        store.similarity_search_with_score.return_value = []
        with patch.object(search, "get_settings", return_value=SETTINGS), \
             patch.object(search, "get_vectorstore", return_value=store), \
             patch.object(search, "ChatOpenAI") as llm:
            answer = search.search_prompt("Qual é a capital da França?")
        self.assertEqual(answer, search.FALLBACK_ANSWER)
        llm.return_value.invoke.assert_not_called()

    def test_chat_asks_question_directly_without_document_id(self):
        chain = Mock()
        chain.invoke.return_value = "Resposta do PDF"
        output = io.StringIO()
        with patch.object(chat, "search_prompt", return_value=chain), \
             patch("builtins.input", side_effect=["", "Minha pergunta", "sair"]) as user_input, \
             redirect_stdout(output):
            chat.main()
        chain.invoke.assert_called_once_with("Minha pergunta")
        self.assertTrue(all(call.args == ("PERGUNTA: ",) for call in user_input.call_args_list))
        self.assertIn("RESPOSTA: Resposta do PDF", output.getvalue())


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [[1.0, float(len(text) % 100) / 100.0, 0.5] for text in texts]

    def embed_query(self, text):
        return self.embed_documents([text])[0]


@unittest.skipUnless(os.getenv("RUN_DB_TESTS") == "1", "Requer PostgreSQL e RUN_DB_TESTS=1")
class DatabaseIntegrationTests(unittest.TestCase):
    def test_pdf_ingestion_reingestion_and_search_with_real_pgvector(self):
        settings = dict(SETTINGS)
        settings["database_url"] = os.getenv("TEST_DATABASE_URL", SETTINGS["database_url"])
        with patch.object(ingest, "get_settings", return_value=settings), \
             patch.object(search, "OpenAIEmbeddings", return_value=FakeEmbeddings()), \
             redirect_stdout(io.StringIO()):
            count = ingest.ingest_pdf()
            store = search.get_vectorstore(settings)
            try:
                before = store.similarity_search_with_score("documento", k=count + 1)
                self.assertEqual(len(before), count)
                ingest.ingest_pdf()
                after = store.similarity_search_with_score("documento", k=count + 1)
                self.assertEqual(len(after), count)
                self.assertEqual(len(store.similarity_search_with_score("documento", k=10)), min(count, 10))
                llm = Mock()
                llm.invoke.return_value = SimpleNamespace(content="Resposta simulada")
                with patch.object(search, "get_settings", return_value=settings), \
                     patch.object(search, "ChatOpenAI", return_value=llm):
                    self.assertEqual(search.search_prompt("Qual o conteúdo?"), "Resposta simulada")
                self.assertTrue(any(doc.page_content in llm.invoke.call_args.args[0] for doc, _ in after))
            finally:
                store.delete_collection()


if __name__ == "__main__":
    unittest.main()
