from tiktoken import encoding_for_model, Encoding
from app.config import get_settings

settings = get_settings()

class Tokenizer:
    def __init__(self, for_model: str):
        self.tokenizer = encoding_for_model(model_name=for_model)
    
    def get_tokens_sum(self, input: str):
        return len(self.tokenizer.encode(input))
