import os
import sys
from pathlib import Path
import base64
from jinja2 import Template
import tempfile
from datetime import datetime
from fpdf import FPDF, HTMLMixin
import html
import pdfkit
import re
import time

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from src.data.loader import DataLoader
from src.data.embeddings import EmbeddingManager
from src.chatbot.engine import RealEstateChatbot
from src.config import Config

# Definir la clase PDF personalizada
class PDF(FPDF):
    def header(self):
        # Encabezado de página
        self.set_font('Arial', 'B', 9)
        self.cell(0, 10, 'STRTGY - Historial de Conversación', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        # Pie de página
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'R')

    def chapter_title(self, title):
        # Título de capítulo
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        # Contenido del capítulo
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_message(self, timestamp, role, content):
        # Agregar un mensaje con formato
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, f'[{timestamp}] {role}:', 0, 1)
        
        self.set_font('Arial', '', 10)
        # Limpiar HTML y mantener formato básico
        content = html.unescape(content)
        content = content.replace('<br>', '\n').replace('<br/>', '\n')
        content = content.replace('</p>', '\n').replace('<p>', '')
        content = content.replace('</h1>', '\n').replace('<h1>', '')
        content = content.replace('</h2>', '\n').replace('<h2>', '')
        content = content.replace('</h3>', '\n').replace('<h3>', '')
        content = content.replace('</li>', '\n').replace('<li>', '• ')
        content = content.replace('<ul>', '\n').replace('</ul>', '\n')
        content = content.replace('<strong>', '').replace('</strong>', '')
        content = content.replace('<em>', '').replace('</em>', '')
        
        # Escribir contenido con formato
        self.multi_cell(0, 10, content)
        self.ln(5)
        
        # Línea separadora
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

def init_authentication():
    """Initialize authentication"""
    # Load authentication config
    auth_file = Path(Config.BASE_DIR) / 'config' / 'auth.yaml'
    with open(auth_file) as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Create authenticator object with plain text passwords
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        preauthorized=None,
        validator=None  # This disables password hashing
    )
    
    return authenticator

def apply_theme():
    """Apply theme based on session state at startup"""
    theme_mode = st.session_state.get('theme_mode', "Claro")
    
    if theme_mode == "Oscuro":
        st.markdown("""
            <style>
            /* Dark theme styles */
            .stApp {
                background-color: #111827 !important;
                color: #F3F4F6 !important;
            }
            
            /* Login form container dark theme */
            [data-testid="stForm"] {
                background-color: #1E293B !important;
                border: 1px solid #334155 !important;
                border-radius: 12px !important;
                padding: 2rem !important;
            }
            
            /* Login form elements dark theme */
            .element-container[data-testid="stFormSubmitter"] {
                background-color: #1E293B !important;
                color: #F3F4F6 !important;
            }
            
            /* Input fields in dark mode */
            .stTextInput input {
                background-color: #0f172a !important;
                border-color: #334155 !important;
                color: #f1f5f9 !important;
            }
            
            /* Radio buttons in dark mode */
            .stRadio > div {
                background-color: #1F2937 !important;
                color: #F3F4F6 !important;
            }
            
            /* Slider in dark mode */
            .stSlider > div > div > div {
                background-color: #4B5563 !important;
            }
            
            /* Chat messages */
            .stChatMessage {
                background-color: #1F2937 !important;
                color: #F3F4F6 !important;
                border: 1px solid #374151 !important;
            }
            
            /* User message */
            .stChatMessage.user {
                background-color: #2563EB !important;
                color: white !important;
            }
            
            /* Assistant message */
            .stChatMessage.assistant {
                background-color: #1F2937 !important;
            }
            
            /* Buttons */
            .stButton > button {
                background-color: #3B82F6 !important;
                color: white !important;
                border: none !important;
            }
            .stButton > button:hover {
                background-color: #2563EB !important;
            }
            
            /* Text elements */
            h1, h2, h3, h4, h5, h6, p, span, div, label {
                color: #F3F4F6 !important;
            }
            
            /* Links */
            a {
                color: #60A5FA !important;
            }
            a:hover {
                color: #93C5FD !important;
            }
            
            /* Bottom block container fix */
            [data-testid="stBottomBlockContainer"] {
                background-color: #111827 !important;
            }
            
            /* Chat input styling */
            [data-testid="stChatInput"] {
                background-color: #1F2937 !important;
                border-color: #374151 !important;
            }
            
            /* Ensure consistent dark theme */
            .stChatFloatingInputContainer {
                background-color: #111827 !important;
            }
            
            .stChatInput textarea {
                background-color: #1F2937 !important;
                color: #F3F4F6 !important;
            }
            
            /* Ensure all containers are dark */
            [data-testid="stAppViewContainer"],
            [data-testid="stHeader"],
            [data-testid="stToolbar"],
            [data-testid="stDecoration"] {
                background-color: #111827 !important;
            }
            
            /* Scrollbars */
            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            ::-webkit-scrollbar-track {
                background: #1F2937;
            }
            ::-webkit-scrollbar-thumb {
                background: #4B5563;
                border-radius: 5px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #6B7280;
            }
            
            /* Main menu popover dark theme - Enhanced */
            [data-testid="stMainMenuPopover"] {
                background-color: #1F2937 !important;
                color: #F3F4F6 !important;
                border: 1px solid #374151 !important;
            }
            
            /* Menu items and all nested elements */
            [data-testid="stMainMenuPopover"] *,
            [data-testid="stMainMenuPopover"] span,
            [data-testid="stMainMenuPopover"] p,
            [data-testid="stMainMenuPopover"] div,
            [data-testid="stMainMenuPopover"] a,
            [data-testid="stMainMenuPopover"] button {
                background-color: #1F2937 !important;
                color: #F3F4F6 !important;
            }
            
            /* Menu item hover state */
            [data-testid="stMainMenuPopover"] button:hover,
            [data-testid="stMainMenuPopover"] a:hover {
                background-color: #374151 !important;
            }
            
            /* Menu dividers */
            [data-testid="stMainMenuPopover"] hr {
                border-color: #374151 !important;
            }
            
            /* Menu icons */
            [data-testid="stMainMenuPopover"] svg {
                fill: #F3F4F6 !important;
            }
            
            /* Dropdown sections */
            [data-testid="stMainMenuPopover"] section {
                background-color: #1F2937 !important;
                border-color: #374151 !important;
            }
            
            /* Settings dialog */
            [data-testid="stMainMenuPopover"] dialog {
                background-color: #1F2937 !important;
                color: #F3F4F6 !important;
            }
            
            /* Sidebar boxes and containers in dark mode */
            .stSidebar [data-testid="stExpander"] {
                background-color: #1F2937 !important;
                border: 1px solid #374151 !important;
                border-radius: 6px !important;
            }
            
            /* User info box in sidebar */
            .stSidebar div[style*="background: var(--background-light)"] {
                background-color: #1F2937 !important;
                border: 1px solid #374151 !important;
            }
            
            /* Expander content */
            .stSidebar .streamlit-expanderContent {
                background-color: #1F2937 !important;
                border-top: 1px solid #374151 !important;
            }
            
            /* Radio buttons container */
            .stSidebar .row-widget.stRadio > div {
                background-color: #1F2937 !important;
                border: 1px solid #374151 !important;
                border-radius: 6px !important;
                padding: 0.5rem !important;
            }
            
            /* Slider container */
            .stSidebar .row-widget.stSlider > div {
                background-color: #1F2937 !important;
                border-radius: 6px !important;
            }
            
            /* Export buttons in sidebar - Keep original blue */
            .stSidebar .stButton button[kind="primary"] {
                background-color: #4F46E5 !important;
                color: white !important;
                border: none !important;
                transition: background-color 0.2s !important;
            }
            
            .stSidebar .stButton button[kind="primary"]:hover {
                background-color: #4338CA !important;
            }
            
            /* Logout button - Keep original red */
            .stSidebar button[kind="secondary"] {
                background-color: #4F46E5 !important;
                color: white !important;
                border: none !important;
                transition: background-color 0.2s !important;
            }
            
            .stSidebar button[kind="secondary"]:hover {
                background-color: #4338CA !important;
            }
                               
            /* Dark theme styles */
            .stApp {
                background-color: #111827 !important;
                color: #F3F4F6 !important;
            }
            /* Login form container dark theme */
            [data-testid="stForm"] {
                background-color: #0F172A !important; /* Darker background */
                border: 1px solid #1E293B !important; /* Darker border */

            }
            [data-testid="stTextInputRootElement"] {
                color: #F3F4F6 !important;
                background-color: #0F172A !important; /* Darker background */
            }

            [data-testid="stBaseButton-secondaryFormSubmit"] {
                background-color: #2563EB !important; /* Vibrant blue */
  
                color: #FFFFFF !important;
            }
            
            [data-testid="stBaseButton-secondaryFormSubmit"]:hover {
                background-color: #1D4ED8 !important; /* Darker blue on hover */
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important;
            }
                    
            [data-testid="stBaseButton-secondary"] {
                background-color: #4F46E5 !important; /* Indigo */
                border: none !important;
                color: #FFFFFF !important;
            }

            [data-testid="stBaseButton-secondary"]:hover {
                background-color: #4338CA !important; /* Darker indigo on hover */
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2) !important;
            }
            /* Login form elements dark theme */
            .element-container[data-testid="stFormSubmitter"] {
                background-color: #1E293B !important;
                color: #F3F4F6 !important;
            }
            
            /* Input fields in dark mode */
            .stTextInput input {
                background-color: #0f172a !important;
                border-color: #334155 !important;
                color: #f1f5f9 !important;
            }
            /* Sidebar content dark theme */
            [data-testid="stSidebarContent"] {
                background-color: #1E293B !important; /* Dark blue-gray */
                border-right: 1px solid #334155 !important;
            }

            [data-testid="stSidebarContent"] .block-container {
                padding: 2rem 1rem !important;
            }

            [data-testid="stSidebarContent"] h1 {
                color: #F3F4F6 !important;
                font-size: 1.25rem !important;
                margin-bottom: 1.5rem !important;
            }

            [data-testid="stSidebarContent"] .stSelectbox label,
            [data-testid="stSidebarContent"] .stSlider label {
                color: #E5E7EB !important;
            }

            [data-testid="stSidebarContent"] select,
            [data-testid="stSidebarContent"] .stSlider [role="slider"] {
                background-color: #0F172A !important;
                border-color: #334155 !important;
                color: #F3F4F6 !important;
            }

            [data-testid="stSidebarContent"] select:hover,
            [data-testid="stSidebarContent"] .stSlider [role="slider"]:hover {
                border-color: #4F46E5 !important;
            }
            </style>
        """, unsafe_allow_html=True)

def update_logo():
    """Update logo based on current theme"""
    logo_path = Path(Config.BASE_DIR) / 'src' / 'assets' / 'strtgy-logo.png'
    logo_dark_path = Path(Config.BASE_DIR) / 'src' / 'assets' / 'strtgy-logo2.png'
    
    # Select logo based on theme
    current_logo_path = logo_dark_path if st.session_state.get('theme_mode') == "Oscuro" else logo_path
    
    if current_logo_path.exists():
        with open(current_logo_path, "rb") as f:
            st.session_state.logo_base64 = base64.b64encode(f.read()).decode()
    else:
        st.error(f"Logo file not found: {current_logo_path}")

def main():
    # Initialize theme and font size if not present
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = "Claro"
        st.session_state.current_font_size = "Normal"  # Initialize font size
        st.session_state.slider_key = "font_size_slider_1"  # Initialize slider key

    # Must be the first Streamlit command
    st.set_page_config(
        page_title="STRTGY | Industrial Real Estate",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'mailto:support@strtgy.com',
            'Report a bug': 'mailto:bugs@strtgy.com',
            'About': 'STRTGY - Asistente de Bienes Raíces Industriales'
        }
    )

    # Apply theme based on session state
    apply_theme()

    # Custom CSS for consistent styling
    st.markdown("""
        <style>
        /* Main container styles */
        .stApp {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }
        
        /* Sidebar styles */
        .sidebar-logo {
            padding: 1rem;
            text-align: center;
            border-bottom: 1px solid rgba(49, 51, 63, 0.1);
        }
        
        .sidebar-logo img {
            max-width: 150px;
            margin: 0 auto;
        }

        /* Widget styles */
        .stButton>button {
            width: 100%;
        }

        /* Text styles */
        h1, h2, h3 {
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

    # CSS for enhanced login page with better positioning
    st.markdown("""
        <style>
        /* Theme toggle switch */
        .theme-toggle {
            position: fixed;
            top: 0.75rem;
            right: 0.75rem;
            z-index: 1000;
            padding: 4px;
            border-radius: 20px;
            background: transparent;
        }
        
        .theme-toggle button {
            background-color: var(--theme-toggle-bg) !important;
            color: var(--theme-toggle-text) !important;
            border: 1px solid var(--theme-toggle-border) !important;
            border-radius: 16px !important;
            padding: 0.35rem 0.75rem !important;
            font-size: 1rem !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 0.35rem !important;
            transition: all 0.2s ease !important;
            min-width: auto !important;
            width: auto !important;
            cursor: pointer !important;
        }
        
        .theme-toggle button:hover {
            background-color: var(--theme-toggle-hover) !important;
            transform: translateY(-1px);
        }
        
        /* Main container */
        .login-page {
            display: flex;
            flex-direction: column;
            align-items: center;
            max-width: 420px;
            margin: 0 auto;
            padding-top: 4rem;
        }
        
        /* Theme-specific variables */
        [data-theme="light"] {
            --theme-toggle-bg: #f8fafc;
            --theme-toggle-text: #1E293B;
            --theme-toggle-border: #e2e8f0;
            --theme-toggle-hover: #f1f5f9;
        }
        
        [data-theme="dark"] {
            --theme-toggle-bg: #1e1e1e;
            --theme-toggle-text: #ffffff;
            --theme-toggle-border: #2d2d2d;
            --theme-toggle-hover: #2d2d2d;
        }
        </style>
    """, unsafe_allow_html=True)

    # Theme toggle with icon
    st.markdown("""
        <div class="theme-toggle">
    """, unsafe_allow_html=True)
    
    if st.session_state.theme_mode == "Claro":
        if st.button("🌙", key="theme_toggle", help="Cambiar a modo oscuro"):
            st.session_state.theme_mode = "Oscuro"
            update_logo()
            st.rerun()
    else:
        if st.button("🌞", key="theme_toggle", help="Cambiar a modo claro"):
            st.session_state.theme_mode = "Claro"
            update_logo()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Inicialización de autenticación primero
    authenticator = init_authentication()

    # Verificar estado de autenticación
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None

    # Initialize logo in session state if not present
    if 'logo_base64' not in st.session_state:
        update_logo()
    

    # Manejo de la interfaz según el estado de autenticación
    if st.session_state.authentication_status != True:
        # Enhanced login interface
        st.markdown('<div class="login-page">', unsafe_allow_html=True)
        
        # Logo
        if 'logo_base64' in st.session_state:
            st.markdown(
                f"""
                <div class="login-logo" style="max-width: 200px; margin: 0 auto;">
                    <img src="data:image/png;base64,{st.session_state.logo_base64}" alt="STRTGY" style="width: 100%; height: auto;">
                </div>
                <h1 class="app-title" style="font-size: 1.5rem; margin: 1rem 0;">Asistente de Bienes Raíces Industriales</h1>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Login form with enhanced styling
        try:
            authenticator.login('main')
            
            if st.session_state.get('authentication_status') == False:
                st.error('❌ Usuario o contraseña incorrectos')
            elif st.session_state.get('authentication_status') == None:
                st.info('👋 Bienvenido, por favor ingresa tus credenciales')
            elif st.session_state.get('authentication_status'):
                st.rerun()
        except Exception as e:
            st.error(f'Error de autenticación: {str(e)}')
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    else:
        # Interfaz principal post-login
        # Logo en sidebar para usuarios autenticados
        with st.sidebar:
            # 1. Logo y título
            if 'logo_base64' in st.session_state:
                st.markdown(
                    f"""
                    <div class="sidebar-logo" style="text-align: center; padding: 1rem 0;">
                        <img src="data:image/png;base64,{st.session_state.logo_base64}" 
                            alt="STRTGY" 
                            style="max-width: 150px; margin: 0 auto;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # 2. Información del usuario con estilo mejorado
            st.markdown(
                f"""
                <div style='
                    padding: 1rem;
                    background: var(--background-light);
                    border-radius: 8px;
                    margin: 1rem 0;
                    border: 1px solid rgba(49, 51, 63, 0.1);
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);'>
                    <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-size: 1.5em; margin-right: 0.5rem;'>👤</span>
                        <h3 style='margin: 0; font-size: 1.1rem;'>{st.session_state["name"]}</h3>
                    </div>
                    <p style='margin: 0; color: var(--text-color); font-size: 0.9rem;'>
                        <span style='color: #00CA4E;'>●</span> Sesión activa
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Personalización funcional
            with st.expander("🎨 Personalización"):
                # Theme selector
                theme_mode = st.radio(
                    "🌓 Modo",
                    options=["Claro", "Oscuro"],
                    horizontal=True,
                    index=0 if st.session_state.theme_mode == "Claro" else 1,
                )
                
                if theme_mode != st.session_state.theme_mode:
                    st.session_state.theme_mode = theme_mode
                    st.session_state.current_font_size = "Normal"
                    # Change slider key to force re-render
                    st.session_state.slider_key = f"font_size_slider_{time.time()}"
                    update_logo()
                    st.rerun()
                
                # Font size handling with dynamic key
                size_map = {
                    "Muy pequeño": "11px",
                    "Pequeño": "14px",
                    "Normal": "16px",
                    "Grande": "20px",
                    "Muy grande": "24px"
                }
                
                font_size = st.select_slider(
                    "Tamaño de texto",
                    options=list(size_map.keys()),
                    value=st.session_state.current_font_size,
                    key=st.session_state.slider_key  # Use dynamic key
                )
                
                # Update current font size in session state
                st.session_state.current_font_size = font_size
                
                # Apply comprehensive text scaling
                st.markdown(
                    f"""
                    <style>
                    /* Base text size for all elements */
                    .stApp, 
                    .stApp p,
                    .stApp div,
                    .stApp span,
                    .stApp label,
                    .stApp button,
                    .stApp input,
                    .stApp textarea,
                    .stApp select,
                    .stApp li,
                    .stMarkdown,
                    .stMarkdown p,
                    .stMarkdown div,
                    .stMarkdown span,
                    .stMarkdown li,
                    .stChatMessage,
                    .stChatMessage div,
                    .stChatMessage p,
                    .element-container,
                    .element-container p,
                    .stTextInput input,
                    .stTextInput textarea,
                    .stSelectbox select,
                    .stButton button {{
                        font-size: {size_map[font_size]} !important;
                        line-height: 1.6 !important;
                    }}
                    
                    /* Headers with proportional scaling */
                    .stMarkdown h1,
                    .stApp h1 {{
                        font-size: calc({size_map[font_size]} * 2) !important;
                        line-height: 1.2 !important;
                    }}
                    
                    .stMarkdown h2,
                    .stApp h2 {{
                        font-size: calc({size_map[font_size]} * 1.5) !important;
                        line-height: 1.3 !important;
                    }}
                    
                    .stMarkdown h3,
                    .stApp h3 {{
                        font-size: calc({size_map[font_size]} * 1.25) !important;
                        line-height: 1.4 !important;
                    }}
                    
                    /* Chat specific styling */
                    .stChatMessage {{
                        padding: calc({size_map[font_size]} * 0.8) calc({size_map[font_size]} * 1.2) !important;
                    }}
                    
                    /* Button and input padding */
                    .stButton button,
                    .stTextInput input,
                    .stTextInput textarea {{
                        padding: calc({size_map[font_size]} * 0.5) calc({size_map[font_size]} * 0.8) !important;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )
            
            # Exportar conversación (funcional)
            col1, col2 = st.columns([1,1])
            with col1:
                if st.button("📥 Exportar TXT", use_container_width=True):
                    if 'messages' in st.session_state and st.session_state.messages:
                        # Código existente para exportar TXT
                        export_content = "Historial de Conversación STRTGY\n\n"
                        for msg in st.session_state.messages:
                            role = "Usuario" if msg["role"] == "user" else "Asistente"
                            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', 
                                                   time.localtime(msg["timestamp"]))
                            export_content += f"[{timestamp}] {role}:\n{msg['content']}\n\n"
                        
                        b64 = base64.b64encode(export_content.encode()).decode()
                        filename = f"STRTGY_chat_{time.strftime('%Y%m%d_%H%M%S')}.txt"
                        href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">📥 Descargar TXT</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.success("✅ Archivo TXT listo para descargar")
                    else:
                        st.warning("No hay mensajes para exportar")

            with col2:
                if st.button("📄 Exportar PDF", use_container_width=True):
                    if 'messages' in st.session_state and st.session_state.messages:
                        try:
                            # Template HTML usando Jinja2
                            html_template = """
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="UTF-8">
                                <style>
                                    @page {
                                        size: letter;
                                        margin: 2.5cm;
                                    }
                                    body {
                                        font-family: Arial, sans-serif;
                                        margin: 0;
                                        padding: 20px;
                                        color: #1E293B;
                                        line-height: 1.6;
                                    }
                                    .header {
                                        text-align: center;
                                        margin-bottom: 30px;
                                    }
                                    .header h1 {
                                        font-size: 24px;
                                        margin-bottom: 10px;
                                        color: #000;
                                    }
                                    .header h2 {
                                        font-size: 20px;
                                        font-weight: normal;
                                        margin-bottom: 15px;
                                        color: #000;
                                    }
                                    .header p {
                                        font-size: 14px;
                                        color: #666;
                                        margin-bottom: 20px;
                                    }
                                    .divider {
                                        border-bottom: 1px solid #000;
                                        margin: 20px 0;
                                    }
                                    .message {
                                        margin: 15px 0;
                                        padding: 10px;
                                        background-color: #F8F9FA;
                                    }
                                    .timestamp {
                                        color: #666;
                                        font-size: 12px;
                                        margin-bottom: 5px;
                                    }
                                    .role {
                                        color: #1E3A8A;
                                        font-weight: bold;
                                        margin-bottom: 5px;
                                    }
                                    .content {
                                        margin-left: 15px;
                                    }
                                    .content ul {
                                        margin: 5px 0;
                                        padding-left: 20px;
                                    }
                                    .content li {
                                        margin: 3px 0;
                                    }
                                    .footer {
                                        text-align: center;
                                        font-size: 12px;
                                        color: #666;
                                        margin-top: 30px;
                                    }
                                </style>
                            </head>
                            <body>
                                <div class="header">
                                    <h1>STRTGY</h1>
                                    <h2>Historial de Conversación</h2>
                                    <p>Generado el {{ current_time }}</p>
                                </div>
                                <div class="divider"></div>

                                {% for message in messages %}
                                <div class="message">
                                    <div class="timestamp">{{ message.timestamp }}</div>
                                    <div class="role">{{ message.role_display }}</div>
                                    <div class="content">{{ message.content | safe }}</div>
                                </div>
                                {% endfor %}

                                <div class="footer">
                                    <p>STRTGY - Asistente de Bienes Raíces Industriales</p>
                                </div>
                            </body>
                            </html>
                            """

                            # Preparar datos para el template
                            template_data = {
                                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'messages': [{
                                    'role': msg['role'],
                                    'role_display': "Usuario" if msg['role'] == "user" else "Asistente",
                                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', 
                                                            time.localtime(msg["timestamp"])),
                                    'content': msg['content']
                                } for msg in st.session_state.messages]
                            }

                            # Renderizar template
                            template = Template(html_template)
                            html_content = template.render(**template_data)

                            # Configuración de pdfkit
                            options = {
                                'page-size': 'Letter',
                                'margin-top': '2.5cm',
                                'margin-right': '2.5cm',
                                'margin-bottom': '2.5cm',
                                'margin-left': '2.5cm',
                                'encoding': 'UTF-8',
                                'header-center': 'STRTGY - Historial de Conversación',
                                'footer-right': '[page]',
                                'header-font-size': '9',
                                'footer-font-size': '9',
                                'header-spacing': '35',
                                'footer-spacing': '15',
                                'enable-local-file-access': True
                            }

                            # Crear archivo temporal para el HTML
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
                                f.write(html_content)
                                html_path = f.name

                            # Crear PDF
                            pdf_path = html_path.replace('.html', '.pdf')
                            config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
                            pdfkit.from_file(html_path, pdf_path, options=options, configuration=config)

                            # Leer el PDF y convertir a base64
                            with open(pdf_path, 'rb') as pdf_file:
                                pdf_data = pdf_file.read()
                                b64_pdf = base64.b64encode(pdf_data).decode()

                            # Limpiar archivos temporales
                            os.unlink(html_path)
                            os.unlink(pdf_path)

                            # Crear link de descarga
                            filename = f"STRTGY_chat_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
                            href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{filename}">📄 Descargar PDF</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            st.success("✅ Archivo PDF listo para descargar")

                        except Exception as e:
                            st.error(f"Error al generar PDF: {str(e)}")
                            st.error("Asegúrate de tener instalado wkhtmltopdf en tu sistema")
                    else:
                        st.warning("No hay mensajes para exportar")
            # Mover el separador y botón de logout al final del sidebar
            st.sidebar.markdown("<div style='position:fixed; bottom:0; left:0; right:0; background:#1E293B; padding:1rem;'>", unsafe_allow_html=True)
            st.sidebar.markdown("<hr style='margin: 0 0 1rem 0;'>", unsafe_allow_html=True)
            authenticator.logout('🚪 Cerrar sesión', 'sidebar', key='unique_key')
            st.sidebar.markdown("</div>", unsafe_allow_html=True)
            



        # Inicializar chatbot si es necesario
        if "chatbot" not in st.session_state:
            with st.spinner("Inicializando chatbot..."):
                data_loader = DataLoader(Config.DATA_PATH)
                df = data_loader.load_data()
                embedding_manager = EmbeddingManager()
                vectorstore = embedding_manager.create_property_embeddings(df)
                st.session_state.chatbot = RealEstateChatbot(vectorstore)
 # Main chat interface
        st.title("🏢 Asistente de Bienes Raíces Industriales")
        
        # Initialize messages if needed
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            welcome_msg = {
                "role": "assistant",
                "content": f"""<h1>👋 ¡Bienvenido {st.session_state["name"]}!</h1>
                
                <h2>🤝 ¿Cómo puedo ayudarte?</h2>
                
                <h3>📋 Servicios disponibles:</h3>
                <ul>
                    <li>🔍 <strong>Búsqueda de propiedades:</strong> Encuentra propiedades industriales por ubicación</li>
                    <li>🔍 <strong>Información detallada:</strong> Obtén datos específicos de propiedades</li>
                    <li>📈 <strong>Análisis comparativo:</strong> Compara propiedades y mercados</li>
                    <li>📉 <strong>Tendencias:</strong> Analiza el comportamiento del mercado</li>
                    <li>💰 <strong>Precios:</strong> Consulta disponibilidad y condiciones comerciales</li>
                </ul>

                <hr>

                <h3>💡 Ejemplos de preguntas:</h3>
                <ul>
                    <li><em>"¿Qué propiedades hay disponibles en Monterrey?"</em></li>
                    <li><em>"Muestra naves industriales mayores a 5000m²"</em></li>
                    <li><em>"Compara precios entre Guadalajara y Ciudad de México"</em></li>
                    <li><em>"¿Cuáles son las tendencias del mercado en Querétaro?"</em></li>
                </ul>
                
                <p><strong>¡Adelante! Hazme cualquier pregunta sobre propiedades industriales.</strong></p>
                """,
                "timestamp": time.time()
            }
            st.session_state.messages.append(welcome_msg)

        # Display messages with proper HTML rendering
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # Ensure content is a string and clean it
                content = str(message["content"]).strip()
                
                # Remove any extra quotes at the start/end if present
                content = content.strip('"\'')
                
                # Add container for better HTML rendering
                st.markdown(
                    f"""
                    <div class="chat-message">
                        {content}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

        # Chat input with HTML support
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
                        "content": response.strip(),
                        "timestamp": time.time()
                    }
                    st.session_state.messages.append(assistant_msg)
                    
                    # Render HTML response
                    st.markdown(
                        f"""
                        <div class="chat-message">
                            {response}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

def get_base64_encoded_image(image_path):
    """Get base64 encoded image"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

if __name__ == "__main__":
    main() 