if __package__:
    from .search import search_prompt
else:
    from search import search_prompt


def main() -> None:
    try:
        chain = search_prompt()
    except Exception as exc:
        print(f"Não foi possível iniciar o chat: {exc}")
        return
    print("Faça sua pergunta. Digite 'sair' para encerrar.")
    while True:
        try:
            question = input("PERGUNTA: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nChat encerrado.")
            break
        if question.lower() in {"sair", "exit", "quit"}:
            break
        if not question:
            continue
        try:
            print(f"RESPOSTA: {chain.invoke(question)}\n")
        except Exception as exc:
            print(f"Erro na consulta: {exc}\n")


if __name__ == "__main__":
    main()
