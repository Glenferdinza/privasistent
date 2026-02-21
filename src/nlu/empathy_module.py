"""
Empathy Module untuk fitur curhat Irma
Memberikan respon empatik berdasarkan sentimen yang terdeteksi
"""

import re
import random
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EmotionType:
    """Tipe emosi yang dapat dideteksi"""
    SEDIH = "sedih"
    SENANG = "senang"
    MARAH = "marah"
    CEMAS = "cemas"
    LELAH = "lelah"
    BINGUNG = "bingung"
    NETRAL = "netral"


class EmpathyModule:
    """Module untuk memberikan respon empatik"""
    
    def __init__(self):
        # Keyword untuk deteksi emosi
        self.emotion_keywords = {
            EmotionType.SEDIH: [
                'sedih', 'galau', 'kecewa', 'putus asa', 'menyesal',
                'kehilangan', 'ditinggal', 'patah hati', 'terluka'
            ],
            EmotionType.SENANG: [
                'senang', 'bahagia', 'gembira', 'excited', 'sukses',
                'berhasil', 'lulus', 'menang', 'suka'
            ],
            EmotionType.MARAH: [
                'marah', 'kesal', 'jengkel', 'bete', 'dongkol',
                'sebel', 'frustrasi', 'annoying'
            ],
            EmotionType.CEMAS: [
                'cemas', 'takut', 'khawatir', 'nervous', 'panik',
                'stress', 'overthinking', 'gelisah'
            ],
            EmotionType.LELAH: [
                'lelah', 'capek', 'tired', 'exhausted', 'burnout',
                'jenuh', 'bosan', 'mengantuk'
            ],
            EmotionType.BINGUNG: [
                'bingung', 'confused', 'ragu', 'tidak tahu', 'galau',
                'dilema', 'stuck'
            ],
        }
        
        # Response templates untuk setiap emosi
        self.empathy_responses = {
            EmotionType.SEDIH: [
                "Aku ngerti kamu lagi sedih. Tidak apa-apa untuk merasa seperti ini, semua orang pernah mengalaminya.",
                "Terima kasih sudah mau berbagi. Aku di sini buat dengerin kamu. Perasaan sedih itu normal kok.",
                "Aku paham ini pasti berat buat kamu. Tapi ingat, masa-masa sulit ini akan berlalu.",
                "Kadang memang hidup itu berat ya. Tapi kamu sudah sangat kuat bisa sampai di sini. Aku bangga sama kamu.",
            ],
            EmotionType.SENANG: [
                "Wah, senang banget denger kamu happy! Aku ikut senang!",
                "Mantap! Kebahagiaan kamu itu hasil dari usaha kamu. Kamu pantas dapetin ini!",
                "Yeay! Semoga kebahagiaan ini terus berlanjut ya!",
                "Aku turut bahagia mendengarnya! Keep up the good vibes!",
            ],
            EmotionType.MARAH: [
                "Aku ngerti kenapa kamu marah. Wajar kok kalau kamu merasa seperti ini.",
                "Sepertinya ada sesuatu yang bikin kamu kesal ya. Mau cerita lebih banyak?",
                "Kadang emang ada hal yang bikin kita frustrasi. Take a deep breath dulu ya.",
                "Aku paham perasaan kamu. Marah itu normal, yang penting gimana kita kelola emosinya.",
            ],
            EmotionType.CEMAS: [
                "Aku tahu ini bikin kamu cemas. Tapi coba tarik napas dulu, satu langkah pada satu waktu.",
                "Kecemasan itu wajar, tapi jangan biarkan dia mengontrol kamu ya. Kamu lebih kuat dari yang kamu kira.",
                "Aku di sini buat kamu. Coba fokus ke hal-hal yang bisa kamu kontrol dulu.",
                "Its okay to feel anxious. Tapi ingat, kebanyakan hal yang kita cemaskan nggak pernah terjadi kok.",
            ],
            EmotionType.LELAH: [
                "Kedengarannya kamu butuh istirahat. Jangan terlalu keras sama diri sendiri ya.",
                "Aku ngerti kamu capek. Mungkin saatnya untuk recharge tenaga. Self-care itu penting!",
                "Sepertinya kamu sudah bekerja keras banget. Ingat untuk kasih waktu buat diri sendiri juga.",
                "Burnout itu nyata. Jangan lupa istirahat yang cukup ya. Kesehatan kamu prioritas.",
            ],
            EmotionType.BINGUNG: [
                "Aku ngerti kamu lagi bingung. Coba kita breakdown masalahnya satu-satu.",
                "Wajar kok kalau bingung. Kadang kita butuh waktu buat mikir jernih.",
                "Kalau lagi bingung, coba tulis semua pilihan dan konsekuensinya. Mungkin bisa lebih clear.",
                "Tidak ada keputusan yang sempurna. Yang penting kamu sudah mempertimbangkan dengan baik.",
            ],
            EmotionType.NETRAL: [
                "Terima kasih sudah berbagi. Aku di sini kalau kamu butuh.",
                "Aku mendengarkan. Ada yang bisa aku bantu?",
                "Kadang berbicara dengan seseorang itu membantu. Aku di sini buat kamu.",
            ],
        }
    
    def detect_emotion(self, text: str) -> str:
        """
        Deteksi emosi dari text
        
        Args:
            text: Text dari user
            
        Returns:
            EmotionType yang terdeteksi
        """
        text_lower = text.lower()
        
        # Score untuk setiap emosi
        scores = {emotion: 0 for emotion in self.emotion_keywords.keys()}
        
        # Hitung score berdasarkan keyword
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[emotion] += 1
        
        # Ambil emosi dengan score tertinggi
        max_score = max(scores.values())
        
        if max_score == 0:
            return EmotionType.NETRAL
        
        detected_emotion = max(scores.items(), key=lambda x: x[1])[0]
        logger.info(f"Emotion detected: {detected_emotion}")
        
        return detected_emotion
    
    def generate_response(self, emotion: str = None, context: str = "", training_manager=None, language_mode: str = 'gen-z') -> str:
        """
        Generate empathetic response dengan custom training data
        
        Args:
            emotion: Detected emotion (if None, will detect from context)
            context: Context text dari user
            training_manager: TrainingDataManager instance untuk custom responses
            language_mode: 'gen-z' atau 'formal'
            
        Returns:
            Empathetic response string
        """
        if not emotion:
            emotion = self.detect_emotion(context)
        
        # Try custom response dari training data dulu
        response = None
        if training_manager:
            try:
                # Coba dapatkan custom response
                custom_response = training_manager.get_response_for_emotion(emotion)
                if custom_response:
                    response = custom_response
                    logger.info(f"Using custom trained response for {emotion}")
                
                # Check personality traits dari training
                personality = training_manager.get_personality_traits()
                
                # Tambahkan endearment jika enabled
                use_endearments = personality.get('communication_style', {}).get('use_endearments', False)
                if use_endearments and random.random() > 0.5:
                    endearments = personality.get('communication_style', {}).get('endearments', [])
                    if endearments:
                        endearment = random.choice(endearments)
                        # Tambahkan endearment di awal atau akhir
                        if random.random() > 0.5:
                            response = f"{endearment}, {response[0].lower() + response[1:]}"
                        else:
                            response = f"{response} {endearment}."
                
            except Exception as e:
                logger.warning(f"Failed to use custom response: {e}")
        
        # Fallback ke default jika tidak ada custom response
        if not response:
            if emotion in self.empathy_responses:
                response = random.choice(self.empathy_responses[emotion])
            else:
                response = random.choice(self.empathy_responses[EmotionType.NETRAL])
        
        # Apply language mode styling
        response = self._apply_language_mode(response, language_mode)
        
        # Tambahkan follow-up question
        follow_up = None
        if training_manager:
            try:
                follow_up = training_manager.get_follow_up_question(emotion)
            except Exception as e:
                logger.warning(f"Failed to get custom follow-up: {e}")
        
        if not follow_up:
            # Default follow-ups based on language mode
            if language_mode == 'gen-z':
                follow_ups = [
                    " Mau cerita lebih lanjut gak?",
                    " Ada yang bisa aku bantuin lagi?",
                    "",
                    "",
                ]
            else:
                follow_ups = [
                    " Apakah Anda ingin bercerita lebih lanjut?",
                    " Ada yang bisa saya bantu?",
                    "",
                    "",
                ]
            follow_up = random.choice(follow_ups)
        else:
            follow_up = f" {follow_up}"
        
        response += follow_up
        
        logger.info(f"Generated empathy response for emotion: {emotion} (mode: {language_mode})")
        return response
    
    def _apply_language_mode(self, text: str, mode: str) -> str:
        """Apply language mode transformations to text."""
        if mode == 'formal':
            # Transform Gen-Z/informal to formal
            replacements = {
                r'\baku\b': 'saya',
                r'\bkamu\b': 'Anda',
                r'\bkok\b': '',
                r'\bsih\b': '',
                r'\bnih\b': '',
                r'\bgak\b': 'tidak',
                r'\bnggak\b': 'tidak',
                r'\benggak\b': 'tidak',
                r'\bbanget\b': 'sangat',
                r'\bdong\b': '',
                r'\bdeh\b': '',
            }
            
            for pattern, replacement in replacements.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            
            # Clean extra spaces
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text


class EmpathyManager:
    """Singleton manager untuk empathy module"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'empathy'):
            self.empathy = EmpathyModule()
    
    def respond(self, text: str) -> str:
        """Generate empathy response wrapper"""
        return self.empathy.generate_response(text)
