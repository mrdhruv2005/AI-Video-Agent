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
    if hasattr(st, "secrets") and key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, default)

def download_via_rapidapi(url: str) -> str:
    """
    Downloads audio using the configured RapidAPI YouTube-to-MP3 API.
    Scans various endpoints and parses JSON responses dynamically to support multiple API formats.
    """
    api_key = get_secret("RAPIDAPI_KEY")
    api_host = get_secret("RAPIDAPI_HOST")
    
    if not api_key or not api_host:
        raise Exception("RAPIDAPI_KEY or RAPIDAPI_HOST is not configured in Streamlit Secrets.")
        
    print(f"Bypassing YouTube IP block via RapidAPI Host: {api_host}")
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
        "Accept": "application/json"
    }
    
    video_id = extract_video_id(url)
    
    # Try common endpoint layouts in popular RapidAPI downloaders
    endpoints = [
        (f"https://{api_host}/", {"url": url}),
        (f"https://{api_host}/get", {"url": url}),
        (f"https://{api_host}/download", {"url": url}),
        (f"https://{api_host}/dl", {"url": url}),
        (f"https://{api_host}/", {"id": video_id}),
        (f"https://{api_host}/get", {"id": video_id}),
        (f"https://{api_host}/download", {"id": video_id}),
    ]
    
    response_json = None
    last_error = None
    
    for endpoint_url, params in endpoints:
        try:
            print(f"Trying RapidAPI endpoint: {endpoint_url} with params {params}")
            r = requests.get(endpoint_url, headers=headers, params=params, timeout=15)
            if r.status_code == 200:
                response_json = r.json()
                print(f"Success from {endpoint_url}. Response: {response_json}")
                break
            else:
                last_error = f"Status {r.status_code}: {r.text[:150]}"
        except Exception as e:
            last_error = str(e)
            
    if not response_json:
        raise Exception(f"Failed to query RapidAPI endpoints. Last error: {last_error}")
        
    # Standard JSON keys that return the direct download URL
    download_link = None
    keys_to_check = ["link", "downloadUrl", "download_url", "url", "download", "mp3", "audio"]
    
    # Check top-level keys
    for key in keys_to_check:
        if key in response_json and isinstance(response_json[key], str) and response_json[key].startswith("http"):
            download_link = response_json[key]
            break
            
    # Check nested keys (e.g. {"result": {"link": "..."}})
    if not download_link:
        for parent_key in ["result", "data", "info", "output"]:
            if parent_key in response_json and isinstance(response_json[parent_key], dict):
                sub_dict = response_json[parent_key]
                for key in keys_to_check:
                    if key in sub_dict and isinstance(sub_dict[key], str) and sub_dict[key].startswith("http"):
                        download_link = sub_dict[key]
                        break
                if download_link:
                    break
                    
    # Check if we need to poll for background processing (some APIs do this)
    if not download_link and response_json.get("status") == "processing":
        job_id = response_json.get("job_id") or response_json.get("id")
        if job_id:
            print(f"Job processing (ID: {job_id}). Polling status...")
            for _ in range(6):
                time.sleep(3)
                poll_url = f"https://{api_host}/status"
                try:
                    r = requests.get(poll_url, headers=headers, params={"id": job_id}, timeout=10)
                    if r.status_code == 200:
                        poll_json = r.json()
                        for key in keys_to_check:
                            if key in poll_json and isinstance(poll_json[key], str) and poll_json[key].startswith("http"):
                                download_link = poll_json[key]
                                break
                        if download_link:
                            break
                except Exception as e:
                    print(f"Polling error: {e}")
                    
    if not download_link:
        raise Exception(f"Unable to parse direct download URL from RapidAPI response: {response_json}")
        
    print(f"Bypassed URL successfully. Downloading MP3 stream from: {download_link}")
    
    # Download the MP3 file from the direct CDN link
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