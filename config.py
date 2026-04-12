import os
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = "openrouter/free"  # Auto selects best free model


def get_model(model: str = None):
    """Zwraca model OpenRouter - używa tylko darmowych modeli."""
    return OpenRouterModel(
        model_name=model or DEFAULT_MODEL,
        provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
    )
