import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from ..data.loader import DataLoader
from ..data.embeddings import EmbeddingManager
from ..chatbot.engine import RealEstateChatbot
from ..config import Config
import time
from datetime import datetime
from pathlib import Path

def format_timestamp(timestamp):
    """Format timestamp for messages"""
    return datetime.fromtimestamp(timestamp).strftime("%H:%M")

def init_authentication():
    """Initialize authentication"""
    # Load authentication config
    auth_file = Path(Config.BASE_DIR) / 'config' / 'auth.yaml'
    with open(auth_file) as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Create authenticator object
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    
    return authenticator

def main():
    # Page config
    st.set_page_config(
        page_title="Asistente de Bienes Raíces Industriales",
        page_icon="🏢",
        layout="wide"
    )

    # Initialize authentication
    authenticator = init_authentication()

    # Show authentication status in sidebar
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None
    
    # Authentication form
    if st.session_state.authentication_status != True:
        st.title("🏢 Asistente de Bienes Raíces Industriales")
        st.markdown("---")
        name, authentication_status, username = authenticator.login('Iniciar Sesión', 'main')
        st.session_state.authentication_status = authentication_status
        
        if authentication_status == False:
            st.error('Usuario o contraseña incorrectos')
        elif authentication_status == None:
            st.warning('Por favor ingresa tus credenciales')
        return
    
    # If we get here, user is authenticated
    st.sidebar.success(f'Bienvenido *{st.session_state.name}*')
    authenticator.logout('Cerrar sesión', 'sidebar')
    
    # Initialize chatbot if needed
    if "chatbot" not in st.session_state:
        with st.spinner("Inicializando chatbot..."):
            data_loader = DataLoader(Config.DATA_PATH)
            df = data_loader.load_data()
            embedding_manager = EmbeddingManager()
            vectorstore = embedding_manager.create_property_embeddings(df)
            st.session_state.chatbot = RealEstateChatbot(vectorstore)

    # Sidebar configuration
    with st.sidebar:
        st.title("⚙️ Configuración")
        
        theme = st.selectbox(
            "🎨 Tema",
            ["Claro", "Oscuro"],
            key="theme"
        )
        
        font_size = st.select_slider(
            "📝 Tamaño de texto",
            options=["Pequeño", "Mediano", "Grande"],
            value="Mediano"
        )
        
        if st.button("📥 Exportar conversación"):
            pass
            
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

    # Main chat interface (only shown when authenticated)
    st.title("🏢 Asistente de Bienes Raíces Industriales")
    
    # Initialize messages if needed
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        welcome_msg = {
            "role": "assistant",
            "content": f"👋 ¡Hola {st.session_state.name}! Soy tu asistente de bienes raíces industriales. ¿En qué puedo ayudarte?",
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

    # Chat input
    if prompt := st.chat_input("Escribe tu mensaje"):
        user_msg = {
            "role": "user",
            "content": prompt,
            "timestamp": time.time()
        }
        st.session_state.messages.append(user_msg)
        
        with st.chat_message("assistant"):
            with st.spinner("Procesando..."):
                response = st.session_state.chatbot.get_response(
                    prompt,
                    st.session_state.messages[:-1]
                )
                
                assistant_msg = {
                    "role": "assistant", 
                    "content": response,
                    "timestamp": time.time()
                }
                st.session_state.messages.append(assistant_msg)
                st.markdown(response)

if __name__ == "__main__":
    main() 