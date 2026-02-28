import cowsay


def greet(message: str) -> str:
    return cowsay.get_output_string("cow", message)
