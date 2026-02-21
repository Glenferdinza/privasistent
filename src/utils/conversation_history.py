"""
Conversation History Manager
Persistent local history dengan sliding window dan auto I/O cleanup
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import gc

logger = logging.getLogger(__name__)


class ConversationHistory:
    """
    Manager untuk persistent conversation history dengan sliding window
    Hanya load 5-10 percakapan terakhir untuk konteks
    """
    
    def __init__(self, history_file: Path, max_context: int = 10):
        """
        Args:
            history_file: Path ke file JSON history
            max_context: Maksimal conversations dalam memory (sliding window)
        """
        self.history_file = Path(history_file)
        self.max_context = max_context
        
        # Ensure parent directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize file if not exists
        if not self.history_file.exists():
            self._init_history_file()
        
        logger.info(f"Conversation history initialized: {history_file}")
    
    def _init_history_file(self):
        """Initialize empty history file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'created': datetime.now().isoformat(),
                        'total_conversations': 0
                    },
                    'conversations': []
                }, f, ensure_ascii=False, indent=2)
            
            logger.info("History file initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize history file: {e}")
    
    def add_conversation(self, user_input: str, assistant_response: str, 
                        intent: str = None, emotion: str = None) -> bool:
        """
        Tambah conversation baru ke history
        
        Args:
            user_input: Input dari user
            assistant_response: Response dari assistant
            intent: Detected intent (optional)
            emotion: Detected emotion (optional)
            
        Returns:
            True jika berhasil
        """
        try:
            # Read current history
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add new conversation
            conversation = {
                'timestamp': datetime.now().isoformat(),
                'user': user_input,
                'assistant': assistant_response,
                'intent': intent,
                'emotion': emotion
            }
            
            data['conversations'].append(conversation)
            data['metadata']['total_conversations'] += 1
            data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Write back (auto close dengan context manager)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Conversation added to history")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add conversation: {e}")
            return False
        finally:
            # Cleanup memory
            gc.collect()
    
    def get_recent_context(self, count: int = None) -> List[Dict]:
        """
        Dapatkan N conversations terakhir untuk context (sliding window)
        
        Args:
            count: Jumlah conversations (default: max_context)
            
        Returns:
            List of recent conversations
        """
        if count is None:
            count = self.max_context
        
        try:
            # Read history
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get last N conversations
            conversations = data.get('conversations', [])
            recent = conversations[-count:] if len(conversations) > count else conversations
            
            logger.info(f"Loaded {len(recent)} recent conversations for context")
            return recent
            
        except Exception as e:
            logger.error(f"Failed to get recent context: {e}")
            return []
        finally:
            # Auto cleanup
            gc.collect()
    
    def search_by_emotion(self, emotion: str, limit: int = 5) -> List[Dict]:
        """
        Cari conversations berdasarkan emotion
        Berguna untuk learning pattern response
        
        Args:
            emotion: Emotion type to search
            limit: Max results
            
        Returns:
            List of matching conversations
        """
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversations = data.get('conversations', [])
            
            # Filter by emotion
            matches = [
                conv for conv in conversations 
                if conv.get('emotion', '').lower() == emotion.lower()
            ]
            
            # Return last N matches
            return matches[-limit:] if len(matches) > limit else matches
            
        except Exception as e:
            logger.error(f"Failed to search by emotion: {e}")
            return []
        finally:
            gc.collect()
    
    def get_stats(self) -> Dict:
        """Dapatkan statistik conversation history"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversations = data.get('conversations', [])
            
            # Count by emotion
            emotion_counts = {}
            for conv in conversations:
                emotion = conv.get('emotion', 'unknown')
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # Count by intent
            intent_counts = {}
            for conv in conversations:
                intent = conv.get('intent', 'unknown')
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            stats = {
                'total_conversations': len(conversations),
                'by_emotion': emotion_counts,
                'by_intent': intent_counts,
                'metadata': data.get('metadata', {})
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
        finally:
            gc.collect()
    
    def clear_old_conversations(self, keep_latest: int = 100):
        """
        Hapus conversations lama, keep hanya N terbaru
        Untuk menghemat disk space
        
        Args:
            keep_latest: Jumlah conversations yang akan dipertahankan
        """
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversations = data.get('conversations', [])
            
            if len(conversations) > keep_latest:
                # Keep only latest N
                data['conversations'] = conversations[-keep_latest:]
                data['metadata']['cleaned'] = datetime.now().isoformat()
                data['metadata']['removed_count'] = len(conversations) - keep_latest
                
                # Write back
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Cleaned history, kept {keep_latest} latest conversations")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to clean history: {e}")
            return False
        finally:
            gc.collect()


class HistoryManager:
    """Singleton manager untuk conversation history"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'history'):
            from config import BASE_DIR
            
            # History file di folder database
            history_file = BASE_DIR / "database" / "conversation_history.json"
            
            self.history = ConversationHistory(
                history_file=history_file,
                max_context=10  # Sliding window: 10 conversations
            )
    
    def add(self, user_input: str, response: str, 
            intent: str = None, emotion: str = None) -> bool:
        """Add conversation wrapper"""
        return self.history.add_conversation(user_input, response, intent, emotion)
    
    def get_context(self, count: int = None) -> List[Dict]:
        """Get recent context wrapper"""
        return self.history.get_recent_context(count)
    
    def search_emotion(self, emotion: str, limit: int = 5) -> List[Dict]:
        """Search by emotion wrapper"""
        return self.history.search_by_emotion(emotion, limit)
    
    def stats(self) -> Dict:
        """Get stats wrapper"""
        return self.history.get_stats()
    
    def cleanup(self, keep_latest: int = 100):
        """Cleanup old conversations wrapper"""
        return self.history.clear_old_conversations(keep_latest)
