"""
Test Whisper Indonesian Speech Recognition
Run pertama akan download model (~488MB)
"""

from src.audio.whisper_recognition import WhisperRecognizer
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_basic_recognition():
    """Test basic Indonesian recognition"""
    print("\n" + "="*60)
    print("🎤 TEST WHISPER INDONESIAN RECOGNITION")
    print("="*60)
    
    print("\nInitializing Whisper (model: small, language: Indonesian)...")
    print("⚠️  First run will download model (~488MB)")
    print("⚠️  This may take 2-5 minutes depending on internet speed")
    
    try:
        recognizer = WhisperRecognizer(
            model_name='small',     # 488MB, 85-90% accuracy
            language='id'            # Indonesian
        )
        
        print("\n✅ Whisper initialized successfully!")
        print("\n📢 SPEAK NOW (5 seconds):")
        print("   Contoh: 'Halo Irma, buka YouTube'")
        print("   Contoh: 'Tolong cari informasi tentang Python'")
        
        text = recognizer.listen_once(duration=5)
        
        if text:
            print(f"\n✅ RECOGNIZED: {text}")
            print(f"   Length: {len(text)} characters")
        else:
            print("\n❌ No speech detected")
            print("   Tips:")
            print("   - Pastikan microphone connected")
            print("   - Bicara lebih keras")
            print("   - Check audio settings")
        
        recognizer.cleanup()
        print("\n✅ Test complete!")
        
    except ImportError as e:
        print("\n❌ ERROR: Whisper not installed")
        print(f"   {e}")
        print("\n🔧 SOLUTION:")
        print("   pip install openai-whisper torch torchaudio")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


def test_multiple_languages():
    """Test multiple languages"""
    print("\n" + "="*60)
    print("🌍 TEST MULTI-LANGUAGE RECOGNITION")
    print("="*60)
    
    try:
        recognizer = WhisperRecognizer(model_name='small', language='id')
        
        # Test Indonesian
        print("\n🇮🇩 INDONESIAN - Speak in 5 seconds:")
        text_id = recognizer.listen_once(duration=5)
        print(f"   Result: {text_id}")
        
        # Test English
        print("\n🇬🇧 ENGLISH - Switching language...")
        recognizer.switch_language('en')
        print("   Speak in 5 seconds:")
        text_en = recognizer.listen_once(duration=5)
        print(f"   Result: {text_en}")
        
        # Test Auto-detect
        print("\n🌍 AUTO-DETECT - Switching to auto mode...")
        recognizer.switch_language('auto')
        print("   Speak in any language (5 seconds):")
        text_auto = recognizer.listen_once(duration=5)
        print(f"   Result: {text_auto}")
        
        recognizer.cleanup()
        print("\n✅ Multi-language test complete!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


def test_different_models():
    """Test different model sizes"""
    print("\n" + "="*60)
    print("📦 TEST DIFFERENT MODEL SIZES")
    print("="*60)
    
    models = [
        ('tiny', 75, '70-75%'),
        ('base', 145, '75-80%'),
        ('small', 488, '85-90%')
    ]
    
    print("\nTesting 3 model sizes for comparison:")
    
    for model_name, size_mb, accuracy in models:
        print(f"\n📦 Model: {model_name} ({size_mb}MB, accuracy: {accuracy})")
        
        try:
            recognizer = WhisperRecognizer(model_name=model_name, language='id')
            print(f"   ✅ Loaded successfully")
            print(f"   🎤 Speak now (3 seconds):")
            
            import time
            start = time.time()
            text = recognizer.listen_once(duration=3)
            elapsed = time.time() - start
            
            print(f"   📝 Result: {text}")
            print(f"   ⏱️  Time: {elapsed:.2f}s")
            
            recognizer.cleanup()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")


def compare_vosk_vs_whisper():
    """Compare Vosk vs Whisper untuk Indonesian"""
    print("\n" + "="*60)
    print("⚔️  VOSK vs WHISPER COMPARISON (Indonesian)")
    print("="*60)
    
    test_phrase = "Halo Irma, buka YouTube sekarang"
    print(f"\nTest phrase: '{test_phrase}'")
    print("Speak this phrase twice for comparison:")
    
    # Test Vosk
    print("\n1️⃣  VOSK (English model with Indonesian speech):")
    try:
        from src.audio.speech_recognition import SpeechRecognizer
        vosk_rec = SpeechRecognizer(default_language='en')
        
        print("   🎤 Speak now:")
        vosk_text = vosk_rec.listen_once()
        print(f"   📝 Vosk result: {vosk_text}")
        print(f"   ⏱️  Latency: ~0.1s (real-time)")
        
    except Exception as e:
        print(f"   ❌ Vosk error: {e}")
    
    # Test Whisper
    print("\n2️⃣  WHISPER (Indonesian model):")
    try:
        whisper_rec = WhisperRecognizer(model_name='small', language='id')
        
        print("   🎤 Speak now:")
        import time
        start = time.time()
        whisper_text = whisper_rec.listen_once(duration=5)
        elapsed = time.time() - start
        
        print(f"   📝 Whisper result: {whisper_text}")
        print(f"   ⏱️  Latency: {elapsed:.2f}s")
        
        whisper_rec.cleanup()
        
    except Exception as e:
        print(f"   ❌ Whisper error: {e}")
    
    print("\n" + "="*60)
    print("COMPARISON SUMMARY:")
    print("  Vosk:    Fast (0.1s) but moderate accuracy for Indonesian (60-70%)")
    print("  Whisper: Slower (2-3s) but excellent accuracy for Indonesian (85-90%)")
    print("="*60)


if __name__ == "__main__":
    print("\n🚀 WHISPER TESTING SUITE")
    print("Choose test:")
    print("1. Basic Indonesian recognition")
    print("2. Multi-language recognition")
    print("3. Different model sizes")
    print("4. Vosk vs Whisper comparison")
    print("5. Run all tests")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == '1':
        test_basic_recognition()
    elif choice == '2':
        test_multiple_languages()
    elif choice == '3':
        test_different_models()
    elif choice == '4':
        compare_vosk_vs_whisper()
    elif choice == '5':
        test_basic_recognition()
        test_multiple_languages()
        test_different_models()
        compare_vosk_vs_whisper()
    else:
        print("Invalid choice. Running basic test...")
        test_basic_recognition()
    
    print("\n✅ Testing complete!")
