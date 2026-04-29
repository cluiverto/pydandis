import os
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

# Lokalny llama.cpp server
LLAMA_SERVER_URL = "http://localhost:3100/v1"
DEFAULT_MODEL = "unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL"


def get_model(model: str = None):
    """Zwraca lokalny model z llama.cpp server."""
    return OpenAIChatModel(
        model_name=model or DEFAULT_MODEL,
        provider=OpenAIProvider(
            base_url=LLAMA_SERVER_URL,
            api_key="none",  # brak autoryzacji
        ),
    )



OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = "openrouter/free"  # Auto selects best free model


def get_openrouter_model(model: str = None):
    """Zwraca model OpenRouter - używa tylko darmowych modeli."""
    return OpenRouterModel(
        model_name=model or DEFAULT_MODEL,
        provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
    )
