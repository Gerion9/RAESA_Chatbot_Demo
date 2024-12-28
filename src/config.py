import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    # Get the base directory (project root)
    BASE_DIR = Path(__file__).parent.parent
    
    
    # Data paths using absolute paths
    DATA_PATH = os.getenv('DATA_PATH', str(BASE_DIR / 'src' / 'data' / 'processed' / 'real_estate_data.json'))
    MARKET_ANALYSIS_PATH = os.getenv('MARKET_ANALYSIS_PATH', str(BASE_DIR / 'src' / 'data' / 'processed' / 'analisis_mercado.json'))
    RAESA_DATA_PATH = os.getenv('RAESA_DATA_PATH', str(BASE_DIR / 'src' / 'data' / 'processed' / 'RAESA_DataBook.json'))
    # Cache directory using absolute path
    CACHE_DIR = BASE_DIR / 'cache'
    MODEL_NAME = "claude-3-5-sonnet-20240620"
    MAX_TOKENS = 8192
    
    EMBEDDINGS_CACHE = CACHE_DIR / "embeddings.pkl"
    MARKET_ANALYSIS_CACHE = CACHE_DIR / "market_analysis.json"
    
    # Configuración de caché
    CACHE_TTL = 3600  # 1 hora en segundos
    PROMPT_CACHE_SIZE = 1000
    
    # Asegurar que el directorio de caché existe
    CACHE_DIR.mkdir(exist_ok=True)
    
    # Configuración de embeddings
    EMBEDDING_DIMENSION = 1536  # Dimensión de embeddings de OpenAI
    EMBEDDING_BATCH_SIZE = 100
    VECTOR_SEARCH_NPROBE = 5
    
    # Update cookie settings
    COOKIE_NAME = "raesa_chat_cookie"
    COOKIE_KEY = "raesa_chat_signature"
    COOKIE_EXPIRY_DAYS = 30