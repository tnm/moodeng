from typing import Any, Dict
import yt_dlp

def get_latest_stream_url(channel_id: str = "ZoodioThailand") -> str:
    """Get the latest stream URL from a YouTube channel"""
    channel_id = channel_id.replace('@', '')
    
    try:
        print(f"🔍 Looking for live stream from @{channel_id}...")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            channel_url = f'https://www.youtube.com/@{channel_id}/live'
            try:
                info = ydl.extract_info(channel_url, download=False)
                if info and 'id' in info:
                    video_url = f"https://www.youtube.com/watch?v={info['id']}"
                    print(f"✨ Found live stream: {info.get('title', 'Untitled')}")
                    return video_url
            except:
                print("❌ No live stream currently active")
                return None
                
    except Exception as e:
        print(f"⚠️  Error checking stream: {e}")
        return None

DEFAULT_CONFIG = {
    "youtube_url": None,
    "min_confidence": 0.10,
    "alert_cooldown": 300,
}

def get_config(custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get configuration with custom overrides"""
    config = DEFAULT_CONFIG.copy()
    if custom_config:
        # Only update if we have non-None values
        config.update({k: v for k, v in custom_config.items() if v is not None})
    
    # If no URL provided, get the latest
    if not config.get("youtube_url"):
        config["youtube_url"] = get_latest_stream_url()
        
    return config