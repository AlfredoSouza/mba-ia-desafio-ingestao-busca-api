from uuid import UUID

import httpx

from src.config import get_settings


def main() -> None:
    settings = get_settings()
    document_id = UUID(input("ID do documento: ").strip())
    print("Digite 'sair' para encerrar.\n")
    with httpx.Client(base_url=settings.api_url, timeout=60) as client:
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

