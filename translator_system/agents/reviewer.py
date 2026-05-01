from pydantic_ai import Agent
from ..models import TranslationResult, ReviewFeedback
from .base_agent import BasePydanticAgent

REVIEWER_SYSTEM_PROMPT = """
Jesteś recenzentem tłumaczeń literackich. Sprawdź czy tłumaczenie:
1. Zachowuje sens oryginalnego tekstu
2. Jest w odpowiednim stylu (prowokacyjnym, bezpośrednim)
3. Nie pomija ważnych fragmentów

Zwróć ocenę i ewentualne uwagi.
"""

class ReviewerAgent(BasePydanticAgent):
    def __init__(self):
        super().__init__(
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            output_type=str
        )

    async def review(self, original: str, translated: str, chunk_id: str) -> ReviewFeedback:
        prompt = f"""
Oryginał:
{original}

Tłumaczenie:
{translated}

Oceń tłumaczenie. Zwróć JSON z polami: approved (bool), issues (list[str]), suggested_fixes (str lub null).
"""
        result = await self.run(prompt)
        import json
        try:
            data = json.loads(result.output)
            return ReviewFeedback(chunk_id=chunk_id, **data)
        except:
            return ReviewFeedback(
                chunk_id=chunk_id,
                approved=True,
                issues=[],
                suggested_fixes=None
            )
