import yt_dlp
from pydub import AudioSegment
import os
import requests
import time
import urllib.parse as urlparse
import streamlit as st

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    parsed_url = urlparse.urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            p = urlparse.parse_qs(parsed_url.query)
            return p.get('v', [''])[0]
        if parsed_url.path.startswith(('/embed/', '/v/')):
            return parsed_url.path.split('/')[2]
    return ""

def get_secret(key: str, default: str = None) -> str:
    """Retrieve secret from Streamlit secrets (Cloud) or environment variables (Local)."""
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        # st.secrets raises an exception if accessed outside streamlit when secrets.toml doesn't exist
        pass
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    return os.getenv(key, default)

def download_via_rapidapi(url: str) -> str:
    """
    Downloads audio using the configured RapidAPI YouTube-to-MP3 API.
    Bypasses YouTube IP block using get_mp3_download_link and polls until the conversion is complete.
    """
    api_key = get_secret("RAPIDAPI_KEY")
    api_host = get_secret("RAPIDAPI_HOST")
    
    if not api_key or not api_host:
        raise Exception("RAPIDAPI_KEY or RAPIDAPI_HOST is not configured in Streamlit Secrets.")
        
    print(f"Bypassing YouTube IP block via RapidAPI Host: {api_host}")
    
    video_id = extract_video_id(url)
    if not video_id:
        raise Exception(f"Could not extract video ID from URL: {url}")
        
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
        "Accept": "application/json"
    }
    
    endpoint_url = f"https://{api_host}/get_mp3_download_link/{video_id}"
    print(f"Calling RapidAPI endpoint: {endpoint_url}")
    
    response = requests.get(endpoint_url, headers=headers, params={"response_mode": "default"}, timeout=15)
    if response.status_code != 200:
        raise Exception(f"RapidAPI request failed with status code {response.status_code}: {response.text}")
        
    data = response.json()
    download_link = data.get("file") or data.get("reserved_file")
    if not download_link:
        raise Exception(f"Could not find download file URL in RapidAPI response: {data}")
        
    print(f"Direct URL retrieved: {download_link}")
    print("Waiting for the audio file to be converted and ready on the API server...")
    
    # Poll the download URL using HEAD requests until status code is 200 (not 404)
    # The API mentions file will be ready in 20 to 300 seconds.
    max_retries = 60  # 60 * 5s = 300 seconds (5 minutes) max wait
    success = False
    
    for i in range(max_retries):
        time.sleep(5)
        try:
            # Send HEAD request to avoid downloading payload during checks
            check = requests.head(download_link, timeout=10)
            if check.status_code == 200:
                print(f"Audio file is ready! (Polled {i+1} times)")
                success = True
                break
            else:
                print(f"File not ready yet (Status: {check.status_code}). Retrying in 5s...")
        except Exception as e:
            print(f"Polling error: {e}. Retrying in 5s...")
            
    if not success:
        # Fallback to reserved file if main file link failed
        reserved_link = data.get("reserved_file")
        if reserved_link and reserved_link != download_link:
            print(f"Primary file link timed out. Checking reserved link: {reserved_link}")
            download_link = reserved_link
            try:
                check = requests.head(download_link, timeout=10)
                if check.status_code == 200:
                    success = True
            except Exception as e:
                print(f"Reserved file polling error: {e}")
                
        if not success:
            raise Exception("Timed out waiting for RapidAPI to generate and host the audio file.")
            
    print(f"Downloading MP3 stream from direct CDN: {download_link}")
    
    file_response = requests.get(download_link, stream=True, timeout=90)
    if file_response.status_code != 200:
        raise Exception(f"Failed to fetch MP3 stream, status: {file_response.status_code}")
        
    filename = os.path.join(DOWNLOAD_DIR, f"rapidapi_{video_id}.mp3")
    with open(filename, "wb") as f:
        for chunk in file_response.iter_content(chunk_size=16384):
            if chunk:
                f.write(chunk)
                
    print(f"Download completed. Saved to {filename}")
    return filename

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
        chunk.export(chunk_path, format="mp3", bitrate="64k")
        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        try:
            # First try direct yt-dlp download (will work locally or on unblocked servers)
            audio_path = download_youtube_audio(source)
        except Exception as direct_e:
            print(f"Direct download failed: {direct_e}. Trying RapidAPI fallback...")
            try:
                # Fallback to RapidAPI bypass endpoint
                audio_path = download_via_rapidapi(source)
            except Exception as rapid_e:
                raise Exception(
                    f"Failed to fetch YouTube audio.\n"
                    f"1. Direct Download Error: {direct_e}\n"
                    f"2. RapidAPI Bypass Error: {rapid_e}"
                )
    else:
        print("Detected local file. Converting to MP3...")
        audio_path = convert_to_mp3(source)

    print("Chunking audio...")
    chunks = chunk_audio(audio_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks