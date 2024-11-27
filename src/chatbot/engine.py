from anthropic import Anthropic
from pathlib import Path
import json
from typing import List, Optional, Dict, Any
import re
from ..config import Config
from ..data.loader import DataLoader

class RealEstateChatbot:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.anthropic = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.data_loader = DataLoader(Config.DATA_PATH)
        self.df = self.data_loader.load_data()
        # self.market_analysis = DataLoader(Config.MARKET_ANALYSIS_PATH).load_data()
        # Load market analysis
        market_analysis_path = Path(Config.MARKET_ANALYSIS_PATH)
        with open(market_analysis_path, 'r', encoding='utf-8') as f:
            self.market_analysis = json.load(f)

    def get_response(self, user_input: str, message_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Get response using full context"""
        try:
            # Check for greetings first
            if self._is_greeting(user_input):
                return self.get_welcome_message()
            
            # Get relevant documents with higher k value
            relevant_docs = self.vectorstore.similarity_search(user_input, k=100)
            
            # Create rich context
            context = self._create_rich_context(relevant_docs, user_input)
            
            # Generate response using Claude
            response = self.generate_response_with_context(user_input, context, message_history)
            
            # Clean the response before returning it
            cleaned_response = self.clean_response(response)
            
            # Asegurarse de que no tenga el TextBlock wrapper
            if "TextBlock(text='" in cleaned_response:
                cleaned_response = cleaned_response.replace("TextBlock(text='", "").replace("', type='text')", "")
            
            return cleaned_response
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Lo siento, hubo un error al procesar tu solicitud. Por favor, intenta de nuevo."

    def _is_greeting(self, text: str) -> bool:
        """Check if input is a greeting"""
        greetings = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos']
        return any(greeting in text.lower() for greeting in greetings)

    def get_welcome_message(self) -> str:
        """Returns a formatted welcome message using basic HTML"""
        return """
        <h1>👋 ¡Bienvenido al Asistente de Bienes Raíces Industriales!</h1>
        
        <h2>🤝 ¿Cómo puedo ayudarte?</h2>
        
        <h3>📋 Servicios disponibles:</h3>
        <ul>
            <li>🔍 <strong>Búsqueda de propiedades:</strong> Encuentra propiedades industriales por ubicación</li>
            <li>📊 <strong>Información detallada:</strong> Obtén datos específicos de propiedades</li>
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
        
        <p><strong>¡Adelante! Hazme cualquier pregunta sobre propiedades industriales.</strong></p>"""

    def generate_response_with_context(self, user_input: str, context: str, message_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Generate initial response using Claude with full context"""
        try:
            # Get initial response
            initial_response = self._get_initial_response(user_input, context, message_history)
            
            # Format the response through the formatting layer
            formatted_response = self._format_response_with_ai(initial_response, user_input)
            
            return formatted_response

        except Exception as e:
            print(f"Error in generate_response_with_context: {e}")
            return "Lo siento, hubo un error al generar la respuesta. Por favor, intenta de nuevo."

    def _get_initial_response(self, user_input: str, context: str, message_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Get initial detailed response from Claude"""
        history_text = ""
        if message_history:
            history_text = "\n".join([
                f"User: {msg['content']}" if msg['role'] == 'user' else f"Assistant: {msg['content']}"
                for msg in message_history[-5:]
            ])

        system_prompt = """Eres un experto asistente de bienes raíces industriales.
        Proporciona respuestas detalladas y precisas incluyendo TODOS los datos relevantes disponibles.
        
        Reglas importantes:
        1. NO omitas ninguna información relevante
        2. Incluye TODOS los datos numéricos y métricas disponibles
        3. Si hay múltiples propiedades, menciona TODAS
        4. Incluye detalles específicos de ubicación, precios y características
        5. Mantén un tono profesional y técnico"""

        response = self.anthropic.messages.create(
            model=Config.MODEL_NAME,
            max_tokens=8192,
            temperature=0.7,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"""
                Historial: {history_text}
                
                Consulta: {user_input}
                
                Contexto: {context}
                
                Proporciona una respuesta completa y detallada sin omitir ninguna información.
                """
            }]
        )
        
        # Acceder al contenido correctamente para Claude 3
        return response.content[0].text

    def _format_response_with_ai(self, content: str, original_query: str) -> str:
        """Format the response using basic HTML text formatting"""
        system_prompt = """Eres un experto en presentación de información clara y atractiva.
        Tu tarea es formatear la información usando elementos HTML básicos para mejorar la legibilidad.
        
        Elementos HTML disponibles:
        - <h1>, <h2>, <h3> para títulos y subtítulos
        - <p> para párrafos
        - <ul>, <li> para listas
        - <strong> o <b> para texto importante
        - <em> o <i> para énfasis
        - <br> para saltos de línea
        - <hr> para separadores
        
        Guía de estilo:
        1. Usa encabezados (<h2>, <h3>) para organizar secciones
        2. Añade emojis relevantes junto a los títulos
        3. Utiliza listas para enumerar características o detalles
        4. Resalta números y métricas importantes con <strong>
        5. Usa párrafos cortos y bien espaciados
        6. Agrega separadores <hr> entre secciones principales
        
        Ejemplo de estructura:
        <h2>🏢 Título Principal</h2>
        <p>Descripción general con <strong>datos importantes</strong>...</p>
        
        <h3>📍 Ubicación</h3>
        <ul>
            <li><strong>Ciudad:</strong> Nombre</li>
            <li><strong>Zona:</strong> Detalles</li>
        </ul>
        
        <hr>
        
        <h3>💰 Detalles Comerciales</h3>
        <p>Información sobre precios y condiciones...</p>"""

        response = self.anthropic.messages.create(
            model=Config.MODEL_NAME,
            max_tokens=8192,
            temperature=0.7,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"""
                Consulta original: {original_query}
                
                Información a formatear:
                {content}
                
                Por favor, formatea esta información usando elementos HTML básicos para mejorar su legibilidad.
                Asegúrate de:
                1. Organizar la información en secciones claras
                2. Resaltar datos importantes
                3. Usar emojis relevantes
                4. Mantener un espaciado adecuado
                5. Crear una jerarquía visual clara
                """
            }]
        )
        
        return self.clean_response(response.content[0].text)

    def _create_rich_context(self, docs, user_input: str) -> str:
        """Create rich context from documents and market analysis"""
        properties_info = []
        for doc in docs:
            properties_info.append(doc.page_content)
        
        market_context = {
            "total_properties": len(self.df),
            "market_summary": self.market_analysis.get('resumen_general', {}),
            "city_distribution": self.market_analysis.get('propiedades_por_ciudad', {}),
            "price_stats": self.market_analysis.get('estadisticas_precio', {})
        }
        
        return f"""
        Consulta del usuario: {user_input}
        
        Información de propiedades relevantes:
        {' '.join(properties_info)}
        
        Contexto del mercado:
        - Total de propiedades: {market_context['total_properties']}
        - Resumen del mercado: {json.dumps(market_context['market_summary'], indent=2)}
        - Distribución por ciudad: {json.dumps(market_context['city_distribution'], indent=2)}
        - Estadísticas de precios: {json.dumps(market_context['price_stats'], indent=2)}
        """

    def clean_response(self, text: Any) -> str:
        """Clean and format the response text"""
        if isinstance(text, list):
            text = ' '.join(str(item) for item in text)
        elif not isinstance(text, str):
            text = str(text)
        
        # Remove TextBlock wrapper and other unwanted text
        patterns_to_remove = [
            r"TextBlock\(text='|', type='text'\)",  # Remove TextBlock wrapper
            r"Here's the formatted version of the information using HTML elements and following the guidelines:\s*",
            r"Here's the formatted version of the information using HTML elements:\s*",
            r"Aquí está el resumen formateado[^<]*",
            r"Aquí tienes[^<]*",
            r"```html",
            r"```",
            r"</div>\s*</div>\s*$",
            r"<div[^>]*>\s*$",
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        
        # Clean up whitespace and formatting
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\\n', ' ')
        text = text.replace('\\', '')
        
        return text

    # ... rest of the methods ...