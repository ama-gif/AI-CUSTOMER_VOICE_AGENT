# llm_loader.py
import os
from typing import Optional
try:
    from llama_cpp import Llama
except Exception as e:
    Llama = None
    # raise at runtime if missing

class LLM:
    def __init__(self, model_path: str = "data/models/mistral-7b-instruct.gguf",
                 n_ctx: int = 4096, n_threads: int = 4, temp: float = 0.2):
        self.model_path = model_path
        self.model = None
        self.temp = temp
        self.use_mock = False
        
        # Try to load the model if available
        if Llama is None:
            print("Warning: llama_cpp not installed. Using mock LLM.")
            self.use_mock = True
        elif not os.path.exists(model_path):
            print(f"Warning: Model file not found at {model_path}. Using mock LLM.")
            self.use_mock = True
        else:
            try:
                self.model = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads)
            except Exception as e:
                print(f"Warning: Failed to load model: {e}. Using mock LLM.")
                self.use_mock = True

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if self.use_mock or self.model is None:
            # Return a mock response for demonstration
            return self._generate_mock_response(prompt, max_tokens)
        
        try:
            resp = self.model.create(prompt=prompt, max_tokens=max_tokens, temperature=self.temp)
            return resp['choices'][0]['text'].strip()
        except Exception as e:
            print(f"Error generating response: {e}. Using mock response.")
            return self._generate_mock_response(prompt, max_tokens)
    
    def _generate_mock_response(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate a mock response for demonstration purposes"""
        mock_responses = [
            "Thank you for your inquiry. This is a demo response from the mock LLM. Please install the actual model file to get real responses.",
            "I appreciate your question. In a production environment, this would be answered by the actual language model.",
            "That's a great question! The system is currently running in demonstration mode. Please ensure the LLM model is properly configured.",
            "Thank you for reaching out. Our support system is here to help. With the full model loaded, I could provide more detailed assistance.",
            "I understand your concern. The system is operational but running with a mock response generator for now.",
        ]
        import hashlib
        # Use hash of prompt to get consistent mock response
        idx = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % len(mock_responses)
        return mock_responses[idx]

def load_llm(model_path: str = None) -> LLM:
    model_path = model_path or "data/models/mistral-7b-instruct.gguf"
    return LLM(model_path=model_path)