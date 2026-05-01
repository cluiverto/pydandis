from ..utils.file_handler import FileHandler
from ..utils.chunker import PageAwareChunker
from ..models import FileStructure, TextChunk
from ..config import config

class TextProcessor:
    def __init__(self):
        self.file_handler = FileHandler()
        self.chunker = PageAwareChunker(max_chunk_size=config.translator.chunk_size)

    def process_file(self, filepath: str) -> tuple[FileStructure, list[TextChunk]]:
        structure = self.file_handler.read_with_structure(filepath)
        chunks = self.chunker.chunk_pages(structure.pages)
        return structure, chunks
