import yt_dlp
from pydub import AudioSegment
import os

# Spelling typo theek kar di 'downloades' se 'downloads'
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_youtube_audio(url: str) -> str:
    """Download YouTube video as an MP3 audio file with bot-bypass headers."""
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",  # Convert output to MP3
                "preferredquality": "128", # 128kbps is optimal for Whisper
            }
        ],
        "quiet": True,
        # ── Bot-Bypass Options ──
        "nocheckcertificate": True,       # Bypass SSL certification checks
        "referer": "https://www.youtube.com/",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "web"] # Android client is more resistant to IP blocks
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        filename = os.path.splitext(filename)[0] + ".mp3"
    return filename

def convert_to_mp3(input_path: str) -> str:
    """Convert any local audio/video file to MP3 format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.mp3"
    audio = AudioSegment.from_file(input_path)
    # Channels 1 (Mono) karke aur MP3 mein export karne se file size optimize hoga
    audio = audio.set_channels(1).set_frame_rate(16000) 
    audio.export(output_path, format="mp3", bitrate="64k") 
    return output_path

def chunk_audio(audio_path: str, chunk_minutes: int = 10) -> list:
    """Split the audio file into 10-minute MP3 chunks."""
    audio = AudioSegment.from_file(audio_path)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{os.path.splitext(audio_path)[0]}_chunk_{i}.mp3"
        # Chunks ko bhi compress karke MP3 mein save karenge
        chunk.export(chunk_path, format="mp3", bitrate="64k")

        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        audio_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to MP3...")
        audio_path = convert_to_mp3(source)

    print("Chunking audio...")
    chunks = chunk_audio(audio_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks