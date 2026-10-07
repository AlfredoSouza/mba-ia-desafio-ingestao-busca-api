from uuid import UUID

import httpx

from src.config import get_settings


def main() -> None:
    settings = get_settings()
    with httpx.Client(base_url=settings.api_url, timeout=60) as client:
        try:
            response = client.get("/documents")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"Não foi possível listar os documentos: {exc}")
            return

        documents = response.json()
        print("Documentos disponíveis:")
        if not documents:
            print("Nenhum documento cadastrado. Envie um PDF pela API antes de consultar.")
            return
        for document in documents:
            print(
                f"ID: {document['document_id']} | "
                f"Arquivo: {document['filename']} | "
                f"Status: {document['status']}"
            )
        print("\nDocumentos com status 'ready' estão prontos para consulta.\n")
        try:
            document_id = UUID(input("ID do documento: ").strip())
        except ValueError:
            print("ID inválido. Copie o ID de um documento listado acima.")
            return
        print("Digite 'sair' para encerrar.\n")
        while True:
            question = input("PERGUNTA: ").strip()
            if question.lower() in {"sair", "exit", "quit"}:
                break
            if not question:
                continue
            response = client.post(
                "/questions",
                json={"document_id": str(document_id), "question": question},
            )
            if response.is_success:
                print(f"RESPOSTA: {response.json()['answer']}\n")
            else:
                print(f"ERRO: {response.json().get('detail', response.text)}\n")


if __name__ == "__main__":
    main()

