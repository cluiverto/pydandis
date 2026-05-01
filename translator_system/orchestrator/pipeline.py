import asyncio
import json
from pathlib import Path
from typing import List, Dict
from ..models import FileStructure, TextChunk, TranslationResult, TranslationJob
from ..agents.text_processor import TextProcessor
from ..agents.translator import TranslatorAgent
from ..agents.reviewer import ReviewerAgent
from ..agents.formatter import Formatter
from ..observability.langfuse_tracer import LangfuseTracer
from ..config import config

class TranslationPipeline:
    def __init__(self):
        self.processor = TextProcessor()
        self.translator = TranslatorAgent()
        self.reviewer = ReviewerAgent()
        self.formatter = Formatter()
        self.tracer = LangfuseTracer()

    def _get_progress_file(self, output_file: str) -> str:
        p = Path(output_file)
        return str(p.parent / f"{p.stem}.progress.json")

    def _load_progress(self, progress_file: str) -> Dict[str, TranslationResult]:
        if not Path(progress_file).exists():
            return {}
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: TranslationResult(**v) for k, v in data.get("results", {}).items()}
        except Exception as e:
            print(f"[WARNING] Nie udało się wczytać postępu: {e}")
            return {}

    def _save_progress(self, progress_file: str, results: Dict[str, TranslationResult], chunks_done: int, chunks_total: int):
        data = {
            "chunks_done": chunks_done,
            "chunks_total": chunks_total,
            "results": {k: v.model_dump() for k, v in results.items()}
        }
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def run(self, input_file: str, output_file: str, review: bool = False) -> TranslationJob:
        job = TranslationJob(input_file=input_file, output_file=output_file)
        progress_file = self._get_progress_file(output_file)

        structure, chunks = self.processor.process_file(input_file)
        job.chunks_total = len(chunks)
        job.status = "processing"

        print(f"[DEBUG] Wczytano {len(chunks)} fragmentów, start tłumaczenia...")

        existing_results = self._load_progress(progress_file)
        results_dict = {k: v for k, v in existing_results.items()}
        job.chunks_done = len(results_dict)

        if job.chunks_done > 0:
            print(f"[DEBUG] Wczytano postęp: {job.chunks_done}/{job.chunks_total} fragmentów już przetłumaczone")

        for i, chunk in enumerate(chunks, 1):
            if chunk.chunk_id in results_dict:
                print(f"[DEBUG] Fragment {i}/{len(chunks)} (ID: {chunk.chunk_id}) już przetłumaczony, pomijam...")
                continue

            print(f"[DEBUG] Tłumaczenie fragmentu {i}/{len(chunks)} (ID: {chunk.chunk_id})...")
            try:
                result = await self.translator.translate_chunk(chunk)
                result.page_numbers = [p.page_number for p in chunk.pages]
                print(f"[DEBUG] Fragment {i} zakończony")
                
                # Logowanie do Langfuse
                self.tracer.trace_chunk(
                    chunk.chunk_id,
                    chunk.combined_text,
                    result.translated_text,
                    metadata={"page_numbers": result.page_numbers, "chunk_index": i, "total_chunks": len(chunks)}
                )
                
                results_dict[chunk.chunk_id] = result
                job.chunks_done += 1
                self._save_progress(progress_file, results_dict, job.chunks_done, job.chunks_total)
                print(f"[DEBUG] Zapisano postęp: {job.chunks_done}/{job.chunks_total}")
                print(f"[DEBUG] Aktualizacja pliku wyjściowego...")
                self.formatter.assemble(structure, list(results_dict.values()), output_file)
            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR] Błąd przy fragmencie {i} (ID: {chunk.chunk_id}): {e}")

                is_moderation = "403" in error_msg or "moderation" in error_msg.lower() or "flagged" in error_msg.lower()

                if is_moderation:
                    print(f"[WARNING] Fragment {i} odrzucony przez moderację - pomijam i idę dalej...")
                else:
                    print(f"[WARNING] Pomijam fragment {i} z powodu błędu i kontynuuję...")

                result = TranslationResult(
                    chunk_id=chunk.chunk_id,
                    translated_text=f"[POMINIĘTO - {'MODERACJA' if is_moderation else 'BŁĄD'}]",
                    source_lang=config.translator.source_lang,
                    target_lang=config.translator.target_lang,
                    tokens_used=0,
                    quality_score=0.0,
                    page_numbers=[p.page_number for p in chunk.pages]
                )
                results_dict[chunk.chunk_id] = result
                job.chunks_done += 1
                self._save_progress(progress_file, results_dict, job.chunks_done, job.chunks_total)
                self.formatter.assemble(structure, list(results_dict.values()), output_file)
                continue

            if review:
                feedback = await self.reviewer.review(
                    chunk.combined_text, result.translated_text, result.chunk_id
                )
                if not feedback.approved and feedback.suggested_fixes:
                    result.translated_text = feedback.suggested_fixes
                    self._save_progress(progress_file, results_dict, job.chunks_done, job.chunks_total)

        job.results = list(results_dict.values())
        job.status = "assembling"
        print(f"[DEBUG] Składanie pliku wyjściowego...")

        self.formatter.assemble(structure, job.results, output_file)
        job.status = "completed"

        if Path(progress_file).exists():
            Path(progress_file).unlink()
            print(f"[DEBUG] Usunięto plik postępu")

        self.tracer.flush()
        return job
