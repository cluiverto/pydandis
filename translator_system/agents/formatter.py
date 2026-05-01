from ..models import FileStructure, TranslationResult
from ..utils.file_handler import FileHandler

class Formatter:
    def __init__(self):
        self.file_handler = FileHandler()

    def assemble(self, structure: FileStructure, results: list[TranslationResult], output_path: str):
        page_translations = {}
        for r in results:
            if r.page_numbers:
                for page_num in r.page_numbers:
                    page_translations[page_num] = r.translated_text
            elif r.chunk_id.startswith("page_"):
                try:
                    page_num = int(r.chunk_id[5:])
                    page_translations[page_num] = r.translated_text
                except ValueError:
                    print(f"[WARNING] Invalid chunk_id: {r.chunk_id}")
            else:
                try:
                    page_num = int(r.chunk_id)
                    page_translations[page_num] = r.translated_text
                except ValueError:
                    print(f"[WARNING] Invalid chunk_id: {r.chunk_id}")

        translated_pages = []
        for page in structure.pages:
            if page.page_number in page_translations:
                page.raw_text = page_translations[page.page_number]
            translated_pages.append(page)

        translated_structure = FileStructure(
            pages=translated_pages,
            total_pages=structure.total_pages,
            markers_preserved=structure.markers_preserved
        )

        self.file_handler.write_translated(output_path, results, translated_structure)
