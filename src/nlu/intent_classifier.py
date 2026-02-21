"""
Natural Language Understanding Module
Rule-based intent classification untuk Irma
"""

import re
import logging
from typing import Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Jenis intent yang dapat dideteksi"""
    CURHAT = "empathy"
    FILE_OPERATION = "file_operation"
    SCREEN_READ = "screen_read"
    WEB_SEARCH = "web_search"
    SYSTEM_INFO = "system_info"
    WEATHER = "weather"
    TIME_QUERY = "time_query"
    CALCULATION = "calculation"
    SHUTDOWN = "shutdown"
    GREETING = "greeting"
    BROWSER_NAVIGATION = "browser_navigation"
    FILE_GENERATION = "file_generation"
    UNKNOWN = "unknown"


class IntentClassifier:
    """Classifier untuk mendeteksi intent dari user input"""
    
    def __init__(self):
        # Define patterns untuk setiap intent
        self.intent_patterns = {
            IntentType.CURHAT: [
                r'\b(sedih|senang|kesal|marah|bingung|takut|cemas|stress|lelah|capek|jenuh)\b',
                r'\b(curhat|cerita|dengar|sharing)\b',
                r'\b(aku merasa|aku lagi|rasanya|perasaan)\b',
                r'\b(bad mood|good mood)\b',
            ],
            IntentType.FILE_OPERATION: [
                r'\b(buka|open|tutup|close|hapus|delete|pindah|move|copy|salin|rename)\b.*\b(file|folder|dokumen)\b',
                r'\b(cari|search|find)\b.*\b(file|folder)\b',
                r'\b(buat|create|bikin)\b.*\b(file|folder)\b',
            ],
            IntentType.SCREEN_READ: [
                r'\b(baca|bacakan|read)\b.*\b(layar|screen|tampilan)\b',
                r'\b(apa|apakah)\b.*\b(di layar|on screen|tertampil)\b',
                r'\b(lihat|cek)\b.*\b(layar|screen)\b',
                r'apa yang.*\b(tertulis|tampil|muncul)\b',
            ],
            IntentType.WEB_SEARCH: [
                r'\b(cari|search|google|browsing)\b.*\b(di internet|online)\b',
                r'\b(informasi|info)\b.*\b(tentang|mengenai|about)\b',
                r'apa itu\b',
                r'siapa\b.*\b(adalah|itu)\b',
            ],
            IntentType.SYSTEM_INFO: [
                r'\b(memory|ram|cpu|disk|storage|processor)\b',
                r'\b(berapa|cek)\b.*\b(memory|ram|penyimpanan)\b',
                r'\b(spek|spesifikasi|specification)\b',
            ],
            IntentType.WEATHER: [
                r'\b(cuaca|weather|hujan|panas|dingin|mendung)\b',
                r'\b(temperatur|suhu|temperature)\b',
            ],
            IntentType.TIME: [
                r'\b(jam|waktu|time|tanggal|date|hari|bulan|tahun)\b.*\b(sekarang|now|berapa)\b',
            ],
            IntentType.CALCULATION: [
                r'\b(hitung|calculate|kalkulasi|berapa hasil)\b',
                r'\d+\s*[\+\-\*\/]\s*\d+',
            ],
            IntentType.SHUTDOWN: [
                r'\b(shutdown|restart|sleep|matikan|nyalakan ulang)\b.*\b(komputer|laptop|pc)\b',
            ],
            IntentType.GREETING: [
                r'\b(hai|halo|hi|hello|selamat pagi|selamat siang|selamat malam)\b',
                r'\b(apa kabar|how are you|gimana kabar)\b',
            ],
            IntentType.BROWSER_NAVIGATION: [
                r'\b(buka|open|pergi ke|go to|akses)\b.*(youtube|google|facebook|instagram|twitter|github|website|browser)\b',
                r'\b(redirect|pindah ke|navigate)\b',
                r'(https?://|www\.)\S+',
            ],
            IntentType.FILE_GENERATION: [
                r'\b(buatkan|bikin|generate|create)\b.*(file|folder|kode|code|program|script)\b',
                r'\b(generate|buatkan)\b.*(dengan isi|berisi|yang isinya)\b',
                r'\b(bikinkan|buatin)\b.*(project|aplikasi|app)\b',
            ],
        }
        
        # Compile all patterns
        self.compiled_patterns = {}
        for intent, patterns in self.intent_patterns.items():
            self.compiled_patterns[intent] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def classify(self, text: str) -> Dict:
        """
        Klasifikasi intent dari text
        
        Args:
            text: Input text dari user
            
        Returns:
            Dict dengan keys: intent, confidence, entities
        """
        if not text:
            return {
                'intent': IntentType.UNKNOWN,
                'confidence': 0.0,
                'entities': {},
                'original_text': text
            }
        
        text = text.strip().lower()
        
        # Score untuk setiap intent
        scores = {intent: 0 for intent in IntentType}
        
        # Hitung score berdasarkan pattern matching
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    scores[intent] += 1
        
        # Ambil intent dengan score tertinggi
        max_score = max(scores.values())
        
        if max_score == 0:
            detected_intent = IntentType.UNKNOWN
            confidence = 0.0
        else:
            detected_intent = max(scores.items(), key=lambda x: x[1])[0]
            confidence = min(max_score / len(self.compiled_patterns[detected_intent]), 1.0)
        
        # Extract entities (simplified)
        entities = self._extract_entities(text, detected_intent)
        
        result = {
            'intent': detected_intent,
            'confidence': confidence,
            'entities': entities,
            'original_text': text
        }
        
        logger.info(f"Intent classified: {detected_intent.value} (confidence: {confidence:.2f})")
        return result
    
    def _extract_entities(self, text: str, intent: IntentType) -> Dict:
        """Extract entities berdasarkan intent"""
        entities = {}
        
        # Extract file path jika ada
        if intent == IntentType.FILE_OPERATION:
            # Simple path extraction
            path_match = re.search(r'[a-zA-Z]:\\[^\s]+', text)
            if path_match:
                entities['path'] = path_match.group(0)
            
            # Extract operation type
            if re.search(r'\b(buat|create|bikin)\b', text, re.IGNORECASE):
                entities['operation'] = 'create'
            elif re.search(r'\b(hapus|delete)\b', text, re.IGNORECASE):
                entities['operation'] = 'delete'
            elif re.search(r'\b(baca|read|show)\b', text, re.IGNORECASE):
                entities['operation'] = 'read'
        
        # Extract calculation jika ada
        if intent == IntentType.CALCULATION:
            calc_match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', text)
            if calc_match:
                entities['operand1'] = int(calc_match.group(1))
                entities['operator'] = calc_match.group(2)
                entities['operand2'] = int(calc_match.group(3))
        
        # Extract URL untuk browser navigation
        if intent == IntentType.BROWSER_NAVIGATION:
            url_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', text, re.IGNORECASE)
            if url_match:
                entities['url'] = url_match.group(0)
            else:
                # Extract website name
                for site in ['youtube', 'google', 'facebook', 'instagram', 'twitter', 'github']:
                    if site in text.lower():
                        entities['url'] = f'https://{site}.com'
                        break
        
        # Extract file generation details
        if intent == IntentType.FILE_GENERATION:
            # Extract file type
            file_types = {'python': 'py', 'javascript': 'js', 'html': 'html', 'css': 'css', 'json': 'json', 'txt': 'txt'}
            for ftype, ext in file_types.items():
                if ftype in text.lower():
                    entities['file_type'] = ext
                    break
            
            # Extract file name if mentioned
            name_match = re.search(r'nama[\s]*["\']?([a-zA-Z0-9_\-]+)["\']?', text, re.IGNORECASE)
            if name_match:
                entities['file_name'] = name_match.group(1)
        
        # Extract query for web search
        if intent == IntentType.WEB_SEARCH:
            # Remove trigger words to get pure query
            query = text
            for trigger in ['cari', 'search', 'google', 'info tentang', 'apa itu']:
                query = re.sub(r'\b' + trigger + r'\b', '', query, flags=re.IGNORECASE)
            entities['query'] = query.strip()
        
        # Extract system info type
        if intent == IntentType.SYSTEM_INFO:
            if any(word in text.lower() for word in ['memory', 'ram']):
                entities['info_type'] = 'memory'
            elif 'cpu' in text.lower():
                entities['info_type'] = 'cpu'
            else:
                entities['info_type'] = 'general'
        
        return entities


class NLUManager:
    """Singleton manager untuk NLU"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'classifier'):
            self.classifier = IntentClassifier()
    
    def understand(self, text: str) -> Dict:
        """Understand user input wrapper"""
        return self.classifier.classify(text)
