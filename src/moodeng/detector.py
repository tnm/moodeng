import cv2
import time
from datetime import datetime
from typing import Optional
import yt_dlp
import warnings
from ultralytics import YOLO
from .alerters import Alerter, LogAlerter
from .config import get_config
from .exceptions import ModelError
import sys
import subprocess
import os

# Mute any CUDA warnings
warnings.filterwarnings("ignore", category=FutureWarning)

class Monitor:
    """
    Moo Deng monitor for hippo detection
    """
    def __init__(
        self,
        alerter: Optional[Alerter] = None,
        youtube_url: Optional[str] = None,
        min_confidence: float = 0.10,
        alert_cooldown: int = 300
    ):
        print("🎥 Loading detector...")
        
        self.config = get_config({
            "youtube_url": youtube_url,
            "min_confidence": min_confidence,
            "alert_cooldown": alert_cooldown
        })
        
        if not self.config.get("youtube_url"):
            raise ValueError("No YouTube URL provided! This shouldn't happen - please report this bug on GitHub.")
        
        self.alerter = alerter or LogAlerter()
        self.model = self._load_model()
        self.last_alert_time = 0
        
    def _load_model(self):
        """Load and optimize model for detection"""
        print("🦛 Loading Moo Deng detection model...")
        try:
            # First ensure we have ultralytics up to date
            print("🔄 Updating ultralytics...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "ultralytics"], check=True)
            
            print("🔄 Downloading OpenImages model...")
            model = YOLO('yolov8x-oiv7.pt')  # OpenImages V7 model
            
            print("\n🔍 Confirming that hippos are in the model...")
            for class_id, name in model.names.items():
                if 'hippopotamus' in name.lower():
                    self.hippo_class = class_id
                    break
            if self.hippo_class is None:
                raise ModelError("Couldn't find hippopotamus class in the model!")
            
            print(f"✨ Found hippo detection (class {self.hippo_class})")
            return model
            
        except Exception as e:
            print(f"Failed to load OpenImages model: {e}")
            raise ModelError("Couldn't find hippopotamus class in the model!")

    def _get_stream_url(self, youtube_url: str) -> str:
        """Get direct stream URL using yt-dlp"""
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(youtube_url, download=False)
                return info['url']
            except Exception as e:
                raise RuntimeError(f"Failed to get stream URL: {str(e)}")

    def start(self):
        """Start monitoring the stream"""
        print(f"\n📡 Connecting to stream: {self.config['youtube_url']}")
        
        try:
            stream_url = self._get_stream_url(self.config['youtube_url'])
            cap = cv2.VideoCapture(stream_url)
            
            print("👀 Connected! Watching for hippos. (note: model trained on common hippos, not pygmy hippos.)")
            check_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("📺 Failed to grab frame, retrying...")
                    time.sleep(1)
                    continue
                
                check_count += 1
                if check_count % 10 == 0:
                    print(f"\n🔍 Check #{check_count}. Looking for hippos...")
                
                # Process detections
                current_time = time.time()
                results = self.model(frame, verbose=False)
                
                for result in results:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = self.model.names[class_id]
                        
                        # Show any hippo detection above 10% confidence
                        # and only show on every 10th check  
                        if class_id == self.hippo_class and confidence > 0.10:
                            if check_count % 4 == 0:
                                print(f"   🦛 Possible hippo! {confidence:.2%} confidence")
                        # Show other animals only if high confidence
                        elif 'animal' in class_name.lower() and confidence > 0.6:
                            if check_count % 10 == 0:
                                print(f"   Found {class_name} with {confidence:.2%} confidence")
                        
                        # Alert on hippos with our configured confidence
                        if (class_id == self.hippo_class 
                            and confidence >= self.config["min_confidence"]
                            and current_time - self.last_alert_time > self.config["alert_cooldown"]):
                            
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            message = f"🦛 Hippo detected at {timestamp}! (Confidence: {confidence:.2f})"
                            self.alerter.send_alert(message)
                            self.last_alert_time = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping monitor...")
        finally:
            if 'cap' in locals():
                cap.release()