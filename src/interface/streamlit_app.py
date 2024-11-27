import streamlit as st
from ..data.loader import DataLoader
from ..data.embeddings import EmbeddingManager
from ..chatbot.engine import RealEstateChatbot
from ..config import Config
import time
from datetime import datetime

def format_timestamp(timestamp):
    """Format timestamp for messages"""
    return datetime.fromtimestamp(timestamp).strftime("%H:%M")

def main():
    # Page config
    st.set_page_config(
        page_title="Industrial Real Estate Assistant",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced styling
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
            
            /* Main container */
            .stApp {
                background: linear-gradient(135deg, #e8f0f7 0%, #d4e5f1 100%);
            }
            
            /* Chat container */
            .chat-container {
                max-width: 1200px;
                margin: 2rem auto;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
            }
            
            /* Message styling */
            .message {
                padding: 1.5rem;
                margin: 1rem 0;
                border-radius: 15px;
                font-family: 'Inter', sans-serif;
                line-height: 1.6;
                max-width: 90%;
            }
            
            .message.user {
                background: #145da0;
                color: white;
                margin-left: auto;
                margin-right: 1rem;
                box-shadow: 0 4px 15px rgba(20, 93, 160, 0.2);
            }
            
            .message.assistant {
                background: white;
                color: #2d3748;
                margin-right: auto;
                margin-left: 1rem;
                border: 1px solid #e2e8f0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            }
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Poppins', sans-serif;
                color: #145da0;
                font-weight: 600;
                margin-bottom: 1rem;
            }
            
            /* Property card styling */
            .property-card {
                background: white;
                padding: 2rem;
                border-radius: 15px;
                margin: 1rem 0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
                border: 1px solid #e2e8f0;
            }
            
            /* Highlights section */
            .highlights {
                background: #f8fafc;
                padding: 1.5rem;
                border-radius: 12px;
                margin: 1rem 0;
                border: 1px solid #e2e8f0;
            }
            
            /* Feature list */
            .feature-list {
                list-style: none;
                padding: 0;
                margin: 1rem 0;
            }
            
            .feature-list li {
                padding: 0.75rem 0;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .feature-list li:last-child {
                border-bottom: none;
            }
            
            /* Metrics grid */
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0;
            }
            
            .metric-card {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                text-align: center;
                border: 1px solid #e2e8f0;
                transition: transform 0.2s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
            }
            
            /* Emoji styling */
            .emoji {
                font-size: 1.5rem;
                margin-right: 0.5rem;
            }
            
            /* Input container */
            .input-container {
                background: white;
                padding: 1.5rem;
                border-radius: 15px;
                margin-top: 2rem;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
                border: 1px solid #e2e8f0;
            }
            
            /* Timestamp */
            .timestamp {
                font-size: 0.75rem;
                color: #718096;
                text-align: right;
                margin-top: 0.5rem;
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #f1f5f9;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #145da0;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #0f4c8a;
            }
            
            /* Code blocks */
            pre {
                background: #1a202c;
                color: #e2e8f0;
                padding: 1rem;
                border-radius: 8px;
                overflow-x: auto;
                margin: 1rem 0;
            }
            
            /* Tables */
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 1rem 0;
                background: white;
                border-radius: 8px;
                overflow: hidden;
            }
            
            th {
                background: #145da0;
                color: white;
                padding: 1rem;
                text-align: left;
            }
            
            td {
                padding: 1rem;
                border-top: 1px solid #e2e8f0;
            }
            
            /* Links */
            a {
                color: #145da0;
                text-decoration: none;
                transition: color 0.2s ease;
            }
            
            a:hover {
                color: #0f4c8a;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Main container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Title
    st.markdown("""
        <h1 style='text-align: center; margin-bottom: 2rem;'>
            🏭 Industrial Real Estate Assistant
        </h1>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Configuración")
        
        # Theme selection
        theme = st.selectbox(
            "🎨 Tema",
            ["Claro", "Oscuro"],
            key="theme"
        )
        
        # Font size
        font_size = st.select_slider(
            "📝 Tamaño de texto",
            options=["Pequeño", "Mediano", "Grande"],
            value="Mediano"
        )
        
        # Export options
        if st.button("📥 Exportar conversación"):
            # Add export functionality
            pass
            
        # Help section
        with st.expander("❓ Ayuda"):
            st.markdown("""
                ### Atajos de teclado:
                - `Enter`: Enviar mensaje
                - `Ctrl + K`: Búsqueda
                - `Esc`: Cancelar
                
                ### Comandos disponibles:
                - `/buscar`: Búsqueda de propiedades
                - `/comparar`: Comparar propiedades
                - `/estadisticas`: Ver estadísticas
            """)
    
    # Main chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Messages container
    st.markdown('<div class="messages-container">', unsafe_allow_html=True)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        welcome_msg = {
            "role": "assistant",
            "content": "👋 ¡Hola! Soy tu asistente de bienes raíces industriales. ¿En qué puedo ayudarte?",
            "timestamp": time.time()
        }
        st.session_state.messages.append(welcome_msg)
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f"""
                <div class="message {message['role']}">
                    {message['content']}
                    <div class="timestamp">{format_timestamp(message['timestamp'])}</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input container
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    # Chat input with suggestions
    if prompt := st.chat_input(
        "Escribe tu mensaje o usa /comandos",
        key="chat_input"
    ):
        # Add user message
        user_msg = {
            "role": "user",
            "content": prompt,
            "timestamp": time.time()
        }
        st.session_state.messages.append(user_msg)
        
        # Show typing indicator
        with st.chat_message("assistant"):
            st.markdown("""
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            """, unsafe_allow_html=True)
            
            # Generate response
            response = st.session_state.chatbot.get_response(
                prompt,
                st.session_state.messages[:-1]
            )
            
            # Add assistant message
            assistant_msg = {
                "role": "assistant",
                "content": response,
                "timestamp": time.time()
            }
            st.session_state.messages.append(assistant_msg)
            
            # Display response
            st.markdown(f"""
                <div class="message assistant">
                    {response}
                    <div class="timestamp">{format_timestamp(assistant_msg['timestamp'])}</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 