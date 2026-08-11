import argparse
from uuid import UUID

from src.services.question_service import answer_question


def search(document_id: UUID, question: str) -> str:
    return answer_question(document_id, question)["answer"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Faz uma pergunta sobre um PDF ingerido.")
    parser.add_argument("document_id", type=UUID)
    parser.add_argument("question")
    args = parser.parse_args()
    print(search(args.document_id, args.question))

