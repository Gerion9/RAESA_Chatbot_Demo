import pickle
from pathlib import Path
import faiss
from typing import List, Dict
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config import Config
import pickle
import pandas as pd

class EmbeddingManager:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.cache_dir = Config.CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        
    def create_service_embeddings(self, df) -> FAISS:
        """Create or load cached embeddings for RAESA services"""
        if Config.EMBEDDINGS_CACHE.exists():
            print("Loading embeddings from cache...")
            try:
                return FAISS.load_local(
                    folder_path=str(Config.EMBEDDINGS_CACHE),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Error loading cache: {e}")
                print("Creating new embeddings instead...")
                Config.EMBEDDINGS_CACHE.unlink(missing_ok=True)
        
        print("Creating new embeddings...")
        
        # Create combined descriptions of services and content
        texts = self._create_service_descriptions(df)
        
        # Create vectorstore
        vectorstore = FAISS.from_texts(
            texts,
            self.embeddings,
            metadatas=[{"source": str(i)} for i in range(len(texts))]
        )
        
        # Cache embeddings
        try:
            vectorstore.save_local(str(Config.EMBEDDINGS_CACHE))
            print("Embeddings cached successfully")
        except Exception as e:
            print(f"Error caching embeddings: {e}")
        
        return vectorstore
    
    def _create_service_descriptions(self, df) -> List[str]:
        """
        Creates textual descriptions combining document content and metadata.
        """
        descriptions = []
        
        for _, row in df.iterrows():
            # Combine all relevant characteristics into text
            description_parts = []
            
            # Add each available field to description
            for column in df.columns:
                if pd.notna(row[column]):
                    value = str(row[column])
                    description_parts.append(f"{column}: {value}")
            
            # Join all parts into complete description
            full_description = "\n".join(description_parts)
            descriptions.append(full_description)
        
        return descriptions
