from pydantic_ai import Agent
from ..config import config
from ..models import TextChunk, TranslationResult
from .base_agent import BasePydanticAgent

TRANSLATOR_SYSTEM_PROMPT = f"""
Jesteś profesjonalnym tłumaczem literatury prowokacyjnej i filozoficznej.
Tłumaczysz tekst z {config.translator.source_lang} na {config.translator.target_lang}.
{config.translator.style_instructions}
Zachowaj oryginalną strukturę, styl, wulgarności i ton autora. Nie dodawaj komentarzy.
"""

class TranslatorAgent(BasePydanticAgent):
    def __init__(self):
        super().__init__(
            system_prompt=TRANSLATOR_SYSTEM_PROMPT,
            output_type=str
        )

    async def translate_chunk(self, chunk: TextChunk) -> TranslationResult:
        prompt = f"""
Tłumacz poniższy tekst na język polski:

{chunk.combined_text}

Zwróć tylko przetłumaczony tekst, bez dodatkowych wyjaśnień.
"""

        result = await self.run(prompt)
        translated_text = result.output

        tokens = 0
        if hasattr(result, 'usage') and result.usage:
            tokens = getattr(result.usage, 'total_tokens', 0)

        return TranslationResult(
            chunk_id=chunk.chunk_id,
            translated_text=translated_text,
            source_lang=config.translator.source_lang,
            target_lang=config.translator.target_lang,
            tokens_used=tokens
        )
