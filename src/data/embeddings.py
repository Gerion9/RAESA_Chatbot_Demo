import pickle
from pathlib import Path
import faiss
from typing import List, Dict
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from ..config import Config
import pandas as pd

class EmbeddingManager:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.cache_dir = Config.CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        
    def create_property_embeddings(self, df) -> FAISS:
        """Create or load cached embeddings"""
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
        
        # Crear descripciones combinadas de las propiedades
        texts = self._create_property_descriptions(df)
        
        # Crear vectorstore
        vectorstore = FAISS.from_texts(
            texts,
            self.embeddings,
            metadatas=[{"source": str(i)} for i in range(len(texts))]
        )
        
        # Guardar en caché
        try:
            vectorstore.save_local(str(Config.EMBEDDINGS_CACHE))
            print("Embeddings cached successfully")
        except Exception as e:
            print(f"Error caching embeddings: {e}")
        
        return vectorstore
    
    def _create_property_descriptions(self, df) -> List[str]:
        """
        Crea descripciones textuales de las propiedades combinando sus características.
        """
        descriptions = []
        
        for _, row in df.iterrows():
            # Combinar todas las características relevantes en un texto
            description_parts = []
            
            # Añadir cada campo disponible a la descripción
            for column in df.columns:
                if pd.notna(row[column]):  # Solo incluir valores no nulos
                    # Formatear valores numéricos
                    if isinstance(row[column], (int, float)):
                        value = f"{row[column]:,.2f}" if isinstance(row[column], float) else str(row[column])
                    else:
                        value = str(row[column])
                    
                    description_parts.append(f"{column}: {value}")
            
            # Unir todas las partes en una descripción completa
            full_description = "\n".join(description_parts)
            descriptions.append(full_description)
        
        return descriptions