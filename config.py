import os
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = "google/gemini-2.0-flash-001"


def get_model(model: str = None):
    """Zwraca model OpenRouter."""
    return OpenRouterModel(
        model_name=model or DEFAULT_MODEL,
        provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
    )
