import os
from dotenv import load_dotenv

# KLUCZOWE: Załaduj .env i ustaw zmienne PRZED jakimkolwiek importem pydantic_ai
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from ..config import config

class BasePydanticAgent:
    def __init__(self, system_prompt: str, output_type: type = str):
        self.system_prompt = system_prompt

        self.model = OpenRouterModel(
            model_name=config.llm.model,
            provider=OpenRouterProvider(api_key=config.llm.api_key),
        )

        self.agent = Agent(
            model=self.model,
            system_prompt=system_prompt
        )
        self.output_type = output_type

    async def run(self, prompt: str, **kwargs):
        result = await self.agent.run(prompt, **kwargs)
        return result
