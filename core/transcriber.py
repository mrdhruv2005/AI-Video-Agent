import os
from groq import Groq

client = None

def get_groq_client():
    global client
    if client is None:
        # Load dotenv just in case it wasn't loaded by the entrypoint
        from dotenv import load_dotenv
        load_dotenv()
        client = Groq()
    return client

def transcribe_chunk_groq(chunk_path: str) -> str:
    """
    Sends a single audio chunk to Groq's Whisper Large V3 translation API.
    Agar audio Hindi/Hinglish hai, toh yeh automatic English mein translate kar dega.
    Agar English hai, toh seedha English text dega.
    """
    groq_client = get_groq_client()
    with open(chunk_path, "rb") as audio_file:
        response = groq_client.audio.translations.create(
            file=(os.path.basename(chunk_path), audio_file.read()),
            model="whisper-large-v3",
            response_format="text"
        )
        return response

def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Wrapper function. Groq sab handle kar leta hai, isliye ab 'hinglish' 
    aur 'english' ke liye alag routing ki zaroorat nahi hai.
    """
    return transcribe_chunk_groq(chunk_path)

def transcribe_all(chunks: list, language: str = "english") -> str:
    """
    List of audio chunks ko process karta hai aur final transcript banata hai.
    """
    full_transcript = "" 

    print("Using Groq (Whisper-Large-V3) for Transcription & English Translation...")

    for i, chunk in enumerate(chunks):  
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")

        # Yahan language parameter pass zaroor ho raha hai (main.py compatibility ke liye),
        # lekin backend (Groq) hamesha English translation hi dega.
        text = transcribe_chunk(chunk, language=language)  

        full_transcript += text + " "  

    print("Transcription complete.")

    return full_transcript.strip()