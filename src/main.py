"""
Irma Virtual Assistant - Main Orchestrator
Asisten virtual offline dengan voice control dan security ketat
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from audio import TTSManager, STTManager, WakeWordManager
from nlu import NLUManager, EmpathyManager, IntentType
from security import SecurityManager, AuditManager
from executors import (FileOpsManager, WebScraperManager, 
                      SystemInfoManager, ScreenReaderManager)
from utils import (MemoryManagerSingleton, ResourceMonitorManager,
                  HistoryManager, TrainingManager)
import gc

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.ERROR_LOG_PATH),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class IrmaAssistant:
    """Main orchestrator untuk Irma Virtual Assistant"""
    
    def __init__(self):
        """Initialize Irma dengan semua modules"""
        logger.info("="*50)
        logger.info(f"Initializing {config.APP_NAME} v{config.VERSION}")
        logger.info("="*50)
        
        # Initialize managers
        self.tts = TTSManager()
        self.stt = STTManager()
        self.wake_word = WakeWordManager()
        self.nlu = NLUManager()
        self.empathy = EmpathyManager()
        self.security = SecurityManager()
        self.audit = AuditManager()
        self.file_ops = FileOpsManager()
        self.web = WebScraperManager()
        self.system_info = SystemInfoManager()
        self.screen_reader = ScreenReaderManager()
        self.memory = MemoryManagerSingleton()
        self.resource_monitor = ResourceMonitorManager()
        
        # Add history and training managers
        self.history = HistoryManager()
        self.training = TrainingManager()
        
        # State
        self.running = False
        self.conversation_context = []
        
        logger.info("All modules initialized successfully")
    
    def greet(self):
        """Greeting saat startup"""
        greeting = (f"Halo, saya {config.APP_NAME}. "
                   "Asisten virtual kamu. Katakan 'hey irma' untuk memulai.")
        self.tts.speak(greeting)
    
    def process_command(self, command: str) -> str:
        """
        Process command dari user
        
        Args:
            command: Text command dari speech recognition
            
        Returns:
            Response text
        """
        try:
            # Understand intent
            intent_result = self.nlu.understand(command)
            intent = intent_result['intent']
            confidence = intent_result['confidence']
            
            logger.info(f"Intent: {intent.value}, Confidence: {confidence:.2f}")
            
            # Log command
            self.audit.log_command(command, intent.value, True)
            
            # Load recent conversation history untuk context
            recent_context = self.history.get_context(count=5)
            if recent_context:
                logger.info(f"Loaded {len(recent_context)} conversations for context")
            
            # Route ke handler berdasarkan intent
            if intent == IntentType.CURHAT:
                response = self._handle_curhat(command)
            
            elif intent == IntentType.FILE_OPERATION:
                response = self._handle_file_operation(command, intent_result)
            
            elif intent == IntentType.SCREEN_READ:
                response = self._handle_screen_read()
            
            elif intent == IntentType.WEB_SEARCH:
                response = self._handle_web_search(command)
            
            elif intent == IntentType.SYSTEM_INFO:
                response = self._handle_system_info(command)
            
            elif intent == IntentType.TIME:
                response = self.system_info.time()
            
            elif intent == IntentType.CALCULATION:
                response = self._handle_calculation(intent_result)
            
            elif intent == IntentType.GREETING:
                response = "Halo! Ada yang bisa aku bantu?"
            
            else:
                response = "Maaf, saya belum bisa membantu dengan itu."
            
            # Add to conversation context
            self.conversation_context.append({
                'command': command,
                'intent': intent.value,
                'response': response
            })
            
            if len(self.conversation_context) > 3:
                self.conversation_context.pop(0)
            
            # Save to persistent history
            emotion = None
            if intent == IntentType.CURHAT:
                from nlu import EmpathyModule
                emp = EmpathyModule()
                emotion = emp.detect_emotion(command)
            
            self.history.add(
                user_input=command,
                response=response,
                intent=intent.value,
                emotion=emotion
            )
            
            # Keep conversation context limited
            if len(self.conversation_context) > 10:
                self.conversation_context.pop(0)
            
            return response
            
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            return "Maaf, terjadi kesalahan saat memproses perintah."
        
        finally:
            # Cleanup memory setelah setiap operasi
            self.memory.after_operation()
    
    def _handle_curhat(self, text: str) -> str:
        """Handle curhat/empathy intent"""
        response = self.empathy.respond(text)
        return response
    
    def _handle_file_operation(self, command: str, intent_result: dict) -> str:
        """Handle file operations"""
        # Extract path dari command (simplified)
        import re
        
        # Cari pattern path Windows
        path_match = re.search(r'[a-zA-Z]:\\[^\s]+', command)
        
        if not path_match:
            return (
                "Silakan sebutkan path file secara lengkap, "
                "misalnya C:\\Users\\Downloads\\file.txt"
            )
        
        path = path_match.group(0)
        
        # Tentukan operasi
        if 'baca' in command.lower() or 'bacakan' in command.lower():
            success, result = self.file_ops.read(path)
            
            if success:
                # Limit panjang untuk dibacakan
                if len(result) > 500:
                    result = result[:500] + "... dan seterusnya"
                return f"Isi file: {result}"
            else:
                return result
        
        elif 'list' in command.lower() or 'isi' in command.lower():
            success, result = self.file_ops.list_dir(path)
            return result
        
        else:
            return "Operasi file apa yang ingin kamu lakukan? Baca, list, atau lainnya?"
    
    def _handle_screen_read(self) -> str:
        """Handle screen reading"""
        # Check resource
        available, reason = self.resource_monitor.check()
        
        if not available:
            return f"Tidak dapat membaca layar sekarang: {reason}. Coba lagi nanti."
        
        self.tts.speak("Sedang membaca layar, tunggu sebentar.")
        
        success, result = self.screen_reader.read()
        
        if success:
            # Limit untuk TTS
            if len(result) > 800:
                result = result[:800] + "... dan seterusnya"
            return f"Isi layar: {result}"
        else:
            return result
    
    def _handle_web_search(self, command: str) -> str:
        """Handle web search"""
        # Extract query
        import re
        
        # Try to extract "apa itu X" or "siapa X"
        patterns = [
            r'apa itu\s+(.+)',
            r'siapa\s+(.+)',
            r'cari\s+(.+)',
            r'informasi tentang\s+(.+)',
        ]
        
        query = None
        for pattern in patterns:
            match = re.search(pattern, command.lower())
            if match:
                query = match.group(1)
                break
        
        if not query:
            return "Apa yang ingin kamu cari?"
        
        # Try Wikipedia
        self.tts.speak("Mencari informasi, tunggu sebentar.")
        success, result = self.web.search_wiki(query)
        
        if success:
            # Limit text
            if len(result) > 1000:
                result = result[:1000] + "..."
            return result
        else:
            return f"Maaf, tidak dapat menemukan informasi tentang {query}."
    
    def _handle_system_info(self, command: str) -> str:
        """Handle system information"""
        cmd_lower = command.lower()
        
        if 'memory' in cmd_lower or 'ram' in cmd_lower:
            return self.system_info.memory()
        elif 'cpu' in cmd_lower or 'processor' in cmd_lower:
            return self.system_info.cpu()
        elif 'disk' in cmd_lower or 'storage' in cmd_lower:
            return self.system_info.disk()
        else:
            return self.system_info.all()
    
    def _handle_calculation(self, intent_result: dict) -> str:
        """Handle calculation"""
        entities = intent_result['entities']
        
        if all(k in entities for k in ['operand1', 'operator', 'operand2']):
            op1 = entities['operand1']
            operator = entities['operator']
            op2 = entities['operand2']
            
            try:
                if operator == '+':
                    result = op1 + op2
                elif operator == '-':
                    result = op1 - op2
                elif operator == '*':
                    result = op1 * op2
                elif operator == '/':
                    if op2 == 0:
                        return "Tidak bisa membagi dengan nol."
                    result = op1 / op2
                else:
                    return "Operator tidak dikenali."
                
                return f"Hasil dari {op1} {operator} {op2} adalah {result}"
                
            except Exception as e:
                logger.error(f"Calculation error: {e}")
                return "Maaf, terjadi kesalahan saat menghitung."
        else:
            return "Maaf, aku tidak bisa menghitung itu."
    
    def run_continuous(self):
        """Run dalam continuous listening mode"""
        self.running = True
        
        # Start resource monitoring
        self.resource_monitor.start()
        
        # Greet
        self.greet()
        
        logger.info("Entering continuous listening mode")
        
        try:
            # Continuous listening dengan wake word detection
            def on_speech_detected(text: str) -> bool:
                """Callback untuk setiap speech detected"""
                try:
                    # Check wake word
                    if self.wake_word.detect(text):
                        logger.info(f"Wake word detected in: {text}")
                        
                        # Extract command
                        command = self.wake_word.extract_command(text)
                        
                        if command:
                            logger.info(f"Processing command: {command}")
                            
                            # Process command
                            response = self.process_command(command)
                            
                            # Speak response
                            self.tts.speak(response)
                        else:
                            # Hanya wake word, tidak ada command
                            self.tts.speak("Ya, ada yang bisa aku bantu?")
                    
                    # Return False untuk continue listening
                    return False
                    
                except KeyboardInterrupt:
                    return True
                except Exception as e:
                    logger.error(f"Speech callback error: {e}")
                    return False
            
            # Start continuous listening
            self.stt.listen_continuous(on_speech_detected)
            
        except KeyboardInterrupt:
            logger.info("Shutting down by user")
        except Exception as e:
            logger.error(f"Runtime error: {e}")
        finally:
            self.shutdown()
    
    def run_single_command(self, command: str):
        """Run single command (untuk testing)"""
        logger.info(f"Single command mode: {command}")
        
        response = self.process_command(command)
        print(f"Response: {response}")
        self.tts.speak(response)
        
        self.shutdown()
    
    def shutdown(self):
        """Shutdown gracefully"""
        logger.info("Shutting down Irma...")
        
        self.tts.speak("Sampai jumpa!")
        
        # Stop monitoring
        self.resource_monitor.stop()
        
        # Final cleanup
        self.memory.cleanup(aggressive=True)
        
        logger.info("Shutdown complete")


def main():
    """Entry point"""
    try:
        # Create assistant
        irma = IrmaAssistant()
        
        # Check if command provided via args
        if len(sys.argv) > 1:
            command = ' '.join(sys.argv[1:])
            irma.run_single_command(command)
        else:
            # Run continuous mode
            irma.run_continuous()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
