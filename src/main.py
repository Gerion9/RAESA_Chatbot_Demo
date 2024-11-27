import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

import streamlit as st
from src.data.loader import DataLoader
from src.data.embeddings import EmbeddingManager
from src.chatbot.engine import RealEstateChatbot
from src.config import Config

def main():
    st.set_page_config(
        page_title="Asistente de Bienes Raíces Industriales",
        page_icon="🏭",
        layout="wide"
    )
    
    # Enhanced CSS for better visual presentation
    st.markdown("""
        <style>
        /* General styles */
        .stMarkdown {
            max-width: 100% !important;
        }
        
        /* Property card styling */
        .property-card {
            background: var(--color-white);
            border: 1px solid var(--color-pale-sky-blue);
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: var(--color-dark-navy);
            transition: all 300ms ease-in-out;
        }
        
        .property-card:hover {
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        
        /* Headers styling */
        .property-card h2 {
            color: var(--color-medium-blue);
            font-family: 'Poppins', sans-serif;
            font-size: 24px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--color-light-blue);
        }
        
        .property-card h3 {
            color: var(--color-medium-blue);
            font-family: 'Poppins', sans-serif;
            font-size: 18px;
            margin-top: 20px;
            margin-bottom: 12px;
        }
        
        /* Table styling */
        .property-card table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            background: var(--color-white);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .property-card th {
            background: var(--color-medium-blue);
            color: var(--color-white);
            padding: 12px;
            text-align: left;
        }
        
        .property-card td {
            padding: 12px;
            border-top: 1px solid var(--color-pale-sky-blue);
        }
        
        /* List styling */
        .property-card ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .property-card li {
            padding: 8px 0;
            border-bottom: 1px solid var(--color-pale-sky-blue);
        }
        
        /* Contact section styling */
        .contact-info {
            background: var(--color-white);
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
            border: 1px solid var(--color-pale-sky-blue);
        }
        
        /* Emoji icons */
        .emoji-icon {
            font-size: 24px;
            margin-right: 8px;
            vertical-align: middle;
        }
        
        /* Highlights section */
        .highlights {
            background: var(--color-pale-sky-blue);
            padding: 16px;
            border-radius: 8px;
            margin: 16px 0;
        }
        
        /* Metrics styling */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 16px 0;
        }
        
        .metric-card {
            background: var(--color-white);
            padding: 16px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid var(--color-pale-sky-blue);
            transition: all 300ms ease-in-out;
        }
        
        .metric-card:hover {
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: var(--color-medium-blue);
        }
        
        .metric-label {
            color: var(--color-dark-navy);
            font-size: 14px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Asistente de Bienes Raíces Industriales en México 🏭")
    
    # Initialize session state
    if 'chatbot' not in st.session_state:
        with st.spinner("Initializing chatbot..."):
            data_loader = DataLoader(Config.DATA_PATH)
            df = data_loader.load_data()
            embedding_manager = EmbeddingManager()
            vectorstore = embedding_manager.create_property_embeddings(df)
            st.session_state.chatbot = RealEstateChatbot(vectorstore)
    
    # Chat interface
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(f"""
                    <div class="property-card">
                        <div class="content">
                            {message["content"]}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
    # Entrada de chat
    if prompt := st.chat_input("Pregúntame sobre propiedades industriales"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Analizando mercado y propiedades..."):
                response = st.session_state.chatbot.get_response(
                    prompt, 
                    st.session_state.messages[:-1]
                )
            
            st.markdown(f"""
                <div class="property-card">
                    <div class="content">
                        {response}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 