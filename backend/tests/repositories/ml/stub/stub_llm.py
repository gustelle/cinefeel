# mock the LLM response
class MockMessage:
    content: str

    def __init__(self, content):
        self.content = content


class MockChoice:
    message: MockMessage

    def __init__(self, message):
        self.message = message


class MockChat:

    message: str
    choices: list[MockChoice]

    def __init__(self, message):
        self.choices = [MockChoice(MockMessage(message))]

    def parse(self, *args, **kwargs):
        return self


class StubMistral:

    message: str

    def __init__(self, message):
        self.message = message

    @property
    def chat(self):
        return MockChat(self.message)


class OllamaMessage:
    content: str

    def __init__(self, content):
        self.content = content


class StubOllama:
    message: OllamaMessage

    def __init__(self, message):
        self.message = message
