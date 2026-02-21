"""
Irma Virtual Assistant - Web Interface
Flask application dengan Tailwind CSS untuk GUI yang modern dan beautiful.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
import json
import threading
import base64
from datetime import datetime
from pathlib import Path
import webbrowser
from werkzeug.utils import secure_filename
import signal
import atexit
import time
import logging
from functools import wraps

# Add parent directory to path untuk import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio.text_to_speech import TTSManager
from src.audio.speech_recognition import SpeechRecognizer
from src.nlu.intent_classifier import IntentClassifier
from src.nlu.empathy_module import EmpathyModule
from src.security.file_access_validator import FileAccessValidator
from src.security.audit_logger import AuditLogger
from src.executors.file_operations import FileOperator
from src.executors.web_scraper import WebScraper
from src.executors.system_info import SystemInfoProvider
from src.executors.screen_reader import ScreenReader
from src.utils.memory_manager import MemoryManager
from src.utils.resource_monitor import ResourceMonitor
from src.utils.conversation_history import ConversationHistory
from src.utils.training_manager import TrainingDataManager
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'irma-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app)

# Rate limiting storage
request_counts = {}
RATE_LIMIT = 30  # requests per minute
RATE_WINDOW = 60  # seconds

def rate_limit(func):
    """Rate limiting decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr
        current_time = time.time()
        
        # Clean old entries
        request_counts[client_ip] = [
            timestamp for timestamp in request_counts.get(client_ip, [])
            if current_time - timestamp < RATE_WINDOW
        ]
        
        # Check rate limit
        if len(request_counts.get(client_ip, [])) >= RATE_LIMIT:
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded. Please slow down.'
            }), 429
        
        # Add current request
        if client_ip not in request_counts:
            request_counts[client_ip] = []
        request_counts[client_ip].append(current_time)
        
        return func(*args, **kwargs)
    return wrapper

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed extensions for image upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}


class IrmaWebAssistant:
    """Main web assistant class with all modules integrated."""
    
    def __init__(self):
        """Initialize all components."""
        print("Initializing Irma Web Assistant...")
        
        # Load configuration
        self.config = Config()
        
        # Initialize managers
        self.tts = TTSManager()
        self.intent_classifier = IntentClassifier()
        self.empathy_module = EmpathyModule()
        self.file_validator = FileAccessValidator(
            whitelist_dirs=self.config.WHITELIST_DIRS,
            blocked_paths=self.config.BLOCKED_PATHS
        )
        self.audit_logger = AuditLogger()
        
        # Initialize executors
        self.file_operator = FileOperator(self.file_validator, self.audit_logger)
        self.web_scraper = WebScraper(
            allowed_domains=self.config.ALLOWED_DOMAINS,
            rate_limit=self.config.WEB_SCRAPER_RATE_LIMIT
        )
        self.system_info = SystemInfoProvider()
        self.screen_reader = ScreenReader()
        
        # Initialize utility managers
        self.memory_manager = MemoryManager(
            gc_threshold=self.config.GC_THRESHOLD,
            auto_cleanup=self.config.AUTO_CLEANUP_ENABLED
        )
        self.resource_monitor = ResourceMonitor(
            warning_threshold=self.config.RESOURCE_WARNING_THRESHOLD
        )
        
        # Initialize conversation history
        history_file = os.path.join(self.config.DATABASE_DIR, "conversation_history.json")
        self.history = ConversationHistory(
            history_file=history_file,
            max_context=10
        )
        
        # Initialize training manager
        self.training_manager = TrainingDataManager(self.config.TRAINING_DIR)
        
        # Language mode: 'gen-z' or 'formal'
        self.language_mode = 'gen-z'  # Default mode
        
        print("Irma Web Assistant initialized successfully!")
    
    def set_language_mode(self, mode: str):
        """Set language mode: 'gen-z' or 'formal'."""
        if mode in ['gen-z', 'formal']:
            self.language_mode = mode
            print(f"Language mode changed to: {mode}")
            return True
        return False
    
    def process_command(self, user_input: str, image_path: str = None) -> dict:
        """
        Process user command (text or voice) and return response.
        
        Args:
            user_input: User's command text
            image_path: Optional path to uploaded image
            
        Returns:
            dict: Response with text, emotion, and metadata
        """
        try:
            # Load recent context from history
            context = self.history.get_recent_context(count=5)
            
            # Classify intent
            result = self.intent_classifier.classify(user_input)
            intent = result['intent']
            entities = result['entities']
            confidence = result['confidence']
            
            response_text = ""
            emotion = "neutral"
            metadata = {
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'timestamp': datetime.now().isoformat()
            }
            
            # Handle different intents
            if intent == 'empathy':
                emotion = self.empathy_module.detect_emotion(user_input)
                response_text = self.empathy_module.generate_response(
                    emotion=emotion,
                    context=user_input,
                    training_manager=self.training_manager,
                    language_mode=self.language_mode
                )
                metadata['emotion'] = emotion
            
            elif intent == 'file_operation':
                # File operations
                operation = entities.get('operation', 'unknown')
                response_text = self._handle_file_operation(operation, entities)
            
            elif intent == 'web_search':
                # Web search and scraping
                query = entities.get('query', user_input)
                response_text = self._handle_web_search(query)
            
            elif intent == 'system_info':
                # System information
                info_type = entities.get('info_type', 'general')
                response_text = self._handle_system_info(info_type)
            
            elif intent == 'screen_read':
                # Screen reading
                response_text = self._handle_screen_read()
            
            elif intent == 'time_query':
                # Time query
                from datetime import datetime
                now = datetime.now()
                if self.language_mode == 'gen-z':
                    response_text = f"Sekarang jam {now.strftime('%H:%M')} nih! Tanggal {now.strftime('%d %B %Y')}."
                else:
                    response_text = f"Sekarang pukul {now.strftime('%H:%M')}, tanggal {now.strftime('%d %B %Y')}."
            
            elif intent == 'greeting':
                # Greeting
                if self.language_mode == 'gen-z':
                    response_text = "Halo! Apa kabar? Ada yang bisa aku bantuin?"
                else:
                    response_text = "Selamat datang. Ada yang bisa saya bantu?"
            
            elif intent == 'browser_navigation':
                # Navigate to website
                url = entities.get('url', '')
                response_text = self._handle_browser_navigation(url, user_input)
            
            elif intent == 'file_generation':
                # Generate files/folders with content
                response_text = self._handle_file_generation(user_input, entities)
            
            else:
                # Unknown intent
                if self.language_mode == 'gen-z':
                    response_text = "Hmm, aku kurang ngerti nih maksudnya. Bisa dijelasin lagi gak?"
                else:
                    response_text = "Maaf, saya belum memahami permintaan Anda. Bisa dijelaskan lebih detail?"
            
            # Apply language mode styling
            response_text = self._apply_language_mode(response_text)
            
            # Save to conversation history
            self.history.add_conversation(
                user_input=user_input,
                assistant_response=response_text,
                emotion=emotion
            )
            
            # Cleanup memory
            self.memory_manager.cleanup()
            
            return {
                'success': True,
                'response': response_text,
                'emotion': emotion,
                'metadata': metadata
            }
            
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            print(f"{error_msg}")
            return {
                'success': False,
                'response': error_msg if self.language_mode == 'formal' else f"Yah error nih: {str(e)}",
                'emotion': 'neutral',
                'metadata': {'error': str(e)}
            }
    
    def _handle_file_operation(self, operation: str, entities: dict) -> str:
        """Handle file operations."""
        try:
            file_path = entities.get('path', entities.get('file_path', ''))
            
            if operation == 'create':
                self.file_operator.create_file(file_path)
                return f"File berhasil dibuat: {file_path}"
            
            elif operation == 'delete':
                self.file_operator.delete_file(file_path)
                return f"File berhasil dihapus: {file_path}"
            
            elif operation == 'read':
                content = self.file_operator.read_file(file_path)
                return f"Isi file:\n{content[:500]}..." if len(content) > 500 else f"📄 Isi file:\n{content}"
            
            else:
                return "Operasi file tidak dikenali."
                
        except Exception as e:
            return f"Error operasi file: {str(e)}"
    
    def _handle_web_search(self, query: str) -> str:
        """Handle web search."""
        try:
            # Open Google search in browser
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            
            if self.language_mode == 'gen-z':
                return f"Oke, aku buka Google buat nyari '{query}' ya!"
            else:
                return f"Membuka pencarian Google untuk: {query}"
                
        except Exception as e:
            return f"Error web search: {str(e)}"
    
    def _handle_system_info(self, info_type: str) -> str:
        """Handle system information queries."""
        try:
            if info_type == 'memory':
                info = self.system_info.get_memory_info()
                used_gb = info['used'] / (1024**3)
                total_gb = info['total'] / (1024**3)
                
                if self.language_mode == 'gen-z':
                    return f"Memory yang kepake: {used_gb:.1f}GB dari {total_gb:.1f}GB ({info['percent']}%)"
                else:
                    return f"Penggunaan memori: {used_gb:.1f}GB dari {total_gb:.1f}GB ({info['percent']}%)"
            
            elif info_type == 'cpu':
                info = self.system_info.get_cpu_info()
                if self.language_mode == 'gen-z':
                    return f"CPU usage sekarang: {info['percent']}%"
                else:
                    return f"Penggunaan CPU saat ini: {info['percent']}%"
            
            else:
                info = self.system_info.get_general_info()
                return f"System: {info['system']}\n📊 CPU: {info['cpu']['percent']}%\n💾 Memory: {info['memory']['percent']}%"
                
        except Exception as e:
            return f"Error system info: {str(e)}"
    
    def _handle_screen_read(self) -> str:
        """Handle screen reading."""
        try:
            text = self.screen_reader.read_screen()
            if text:
                if self.language_mode == 'gen-z':
                    return f"Oke, ini yang aku baca dari layar:\n{text[:300]}..."
                else:
                    return f"Teks dari layar:\n{text[:300]}..."
            else:
                return "Tidak ada teks yang bisa dibaca dari layar."
                
        except Exception as e:
            return f"Error reading screen: {str(e)}"
    
    def _handle_browser_navigation(self, url: str, user_input: str) -> str:
        """Navigate to website atau app."""
        try:
            # Extract URL if not explicit
            if not url:
                # Simple URL extraction
                words = user_input.lower().split()
                for word in words:
                    if 'youtube' in word:
                        url = 'https://youtube.com'
                    elif 'facebook' in word:
                        url = 'https://facebook.com'
                    elif 'instagram' in word:
                        url = 'https://instagram.com'
                    elif 'twitter' in word or 'x.com' in word:
                        url = 'https://twitter.com'
                    elif 'github' in word:
                        url = 'https://github.com'
            
            # Add https if no protocol
            if url and not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            if url:
                webbrowser.open(url)
                if self.language_mode == 'gen-z':
                    return f"Siap! Aku buka {url} di browser ya~"
                else:
                    return f"Membuka {url} di browser."
            else:
                return "URL tidak ditemukan dalam perintah."
                
        except Exception as e:
            return f"Error opening browser: {str(e)}"
    
    def _handle_file_generation(self, user_input: str, entities: dict) -> str:
        """Generate file based on user command."""
        try:
            # Extract file details from entities
            file_name = entities.get('file_name', 'generated_file')
            file_type = entities.get('file_type', 'txt')
            content = entities.get('content', '')
            
            # Ensure safe filename
            safe_name = secure_filename(file_name)
            if not safe_name.endswith(f'.{file_type}'):
                safe_name = f"{safe_name}.{file_type}"
            
            # Generate file
            file_path = self.file_generator.generate(
                file_name=safe_name,
                file_type=file_type,
                template_type='basic',
                details={'content': content, 'description': user_input}
            )
            
            if file_path:
                if self.language_mode == 'gen-z':
                    return f"File '{safe_name}' berhasil dibuat sesuai instruksi."
                else:
                    return f"File '{safe_name}' berhasil dibuat sesuai instruksi."
                
        except Exception as e:
            return f"Error generating file: {str(e)}"
    
    def _apply_language_mode(self, text: str) -> str:
        """Apply language mode styling to response."""
        # This can be enhanced later with more sophisticated transformations
        return text


# Global assistant instance
assistant = IrmaWebAssistant()


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })


@app.route('/api/process', methods=['POST'])
@rate_limit
def process_command():
    """Process user command (text or voice)."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        user_input = data.get('input', '').strip()
        
        if not user_input:
            return jsonify({
                'success': False,
                'error': 'Input tidak boleh kosong'
            }), 400
        
        # Log request
        logger.info(f"Processing command: {user_input[:50]}...")
        
        # Process command
        result = assistant.process_command(user_input)
        
        logger.info(f"Command processed successfully")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing command: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/process-voice', methods=['POST'])
def process_voice():
    """Process voice input (placeholder for future implementation)."""
    try:
        data = request.get_json()
        user_input = data.get('input', '').strip()
        
        if not user_input:
            return jsonify({
                'success': False,
                'error': 'Input tidak boleh kosong'
            }), 400
        
        # Process command
        result = assistant.process_command(user_input)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Handle image upload."""
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file'
            }), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No selected file'
            }), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'path': filepath
            })
        
        return jsonify({
            'success': False,
            'error': 'File type not allowed'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/language-mode', methods=['POST'])
def change_language_mode():
    """Change language mode (gen-z / formal)."""
    try:
        data = request.get_json()
        mode = data.get('mode', 'gen-z')
        
        if assistant.set_language_mode(mode):
            return jsonify({
                'success': True,
                'mode': mode
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid mode'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/conversation-history', methods=['GET'])
def get_conversation_history():
    """Get conversation history."""
    try:
        history = assistant.history.get_recent_context(count=20)
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system stats."""
    try:
        stats = {
            'memory': assistant.system_info.get_memory_info(),
            'cpu': assistant.system_info.get_cpu_info(),
            'conversation_stats': assistant.history.get_stats()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def open_browser():
    """Open browser after short delay."""
    time.sleep(1.5)
    try:
        webbrowser.open('http://localhost:5000')
        logger.info("Browser opened successfully")
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")


def cleanup():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down Irma Web Interface...")
    try:
        # Cleanup assistant resources
        assistant.memory_manager.cleanup()
        logger.info("Resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    cleanup()
    sys.exit(0)


if __name__ == '__main__':
    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Irma Web Interface...")
    print("\n" + "="*60)
    print("  IRMA VIRTUAL ASSISTANT - WEB INTERFACE")
    print("="*60)
    print(f"\nServer running at: http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")
    
    # Open browser in separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Flask app
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        cleanup()
def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def open_browser():
    """Open browser after short delay."""
    import time
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    print("Starting Irma Web Interface...")
    print("Server akan berjalan di: http://localhost:5000")
    print("Tekan Ctrl+C untuk stop server")
    
    # Open browser in separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
