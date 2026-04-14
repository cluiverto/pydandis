from pydantic_ai import Agent


import os , sys
# Pobierz katalog główny bam wzgledem obecnego folderu roboczego
bam_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.insert(0, bam_dir)
from config import get_model


agent = Agent(get_model(), instructions='You always respond in Italian.')
agent.to_cli_sync()