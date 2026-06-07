from dotenv import load_dotenv
load_dotenv()   # MUST be before any core/ imports

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions

# Ek chota YouTube video test ke liye
source = "https://www.youtube.com/watch?v=K_-oWRYBkmE"

# Yahan se 'language' variable hata diya gaya hai kyunki Groq ab sab auto-handle karta hai

print("Audio process ho rahi hai...")
chunks = process_input(source)

# Function call se bhi language argument hata diya
transcript = transcribe_all(chunks)

print("\n" + "=" * 60)
print("📝 TRANSCRIPT")
print("=" * 60)
# Pura transcript print karne ki jagah thoda sa dikha rahe hain
print(transcript[:500] + "..." if len(transcript) > 500 else transcript)


title = generate_title(transcript)
summary = summarize(transcript)

print("\n" + "=" * 60)
print(f"📌 TITLE: {title}")
print("=" * 60)
print("\n📋 SUMMARY")
print("-" * 60)
print(summary)


action_items = extract_action_items(transcript)
decisions = extract_key_decisions(transcript)
questions = extract_questions(transcript)

print("\n" + "=" * 60)
print("✅ ACTION ITEMS")
print("=" * 60)
print(action_items)

print("\n" + "=" * 60)
print("🔑 KEY DECISIONS")
print("=" * 60)
print(decisions)

print("\n" + "=" * 60)
print("❓ OPEN QUESTIONS")
print("=" * 60)
print(questions)