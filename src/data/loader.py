import json
import pandas as pd
from pathlib import Path

class DataLoader:
    def __init__(self, file_path):
        self.file_path = Path(file_path).resolve()
    
    def load_data(self):
        """Load and preprocess real estate data"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found at: {self.file_path}")