import cv2
import time
import re
import json
from pathlib import Path
from difflib import get_close_matches
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import yt_dlp
import warnings
import numpy as np
from ultralytics import YOLO
from .alerters import Alerter, LogAlerter
from .config import get_config
from .exceptions import ConfigurationError, ModelError
import sys
import subprocess
import os

# Mute any CUDA warnings
warnings.filterwarnings("ignore", category=FutureWarning)

TARGET_LABEL_ALIASES = {
    "stellar sea lion": "steller sea lion",
    "stellar sea lions": "steller sea lion",
    "steller sea lions": "steller sea lion",
}

HTTP_HEADERS = {
    "User-Agent": "moodeng/0.1 (+https://github.com/tnm/moodeng)",
}


def _normalize_label(label: str) -> str:
    """Normalize a class label for resilient matching."""
    return re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()


def _label_candidates(label: str) -> list[str]:
    """Build normalized label candidates, including common aliases."""
    normalized = _normalize_label(label)
    candidates = [normalized]

    aliased = TARGET_LABEL_ALIASES.get(normalized)
    if aliased:
        candidates.append(aliased)

    expanded = []
    for candidate in candidates:
        expanded.append(candidate)
        if candidate.endswith("s"):
            expanded.append(candidate[:-1])
        else:
            expanded.append(f"{candidate}s")

    return list(dict.fromkeys(part for part in expanded if part))


def _normalize_remote_url(url: str) -> str:
    """Normalize scheme-relative URLs returned by remote player configs."""
    if url.startswith("//"):
        return f"https:{url}"
    return url


def _http_get_bytes(url: str) -> bytes:
    """Fetch bytes from a remote URL with a stable user agent."""
    request = Request(url, headers=HTTP_HEADERS)
    with urlopen(request, timeout=30) as response:
        return response.read()


def _http_get_text(url: str) -> str:
    """Fetch text content from a remote URL."""
    return _http_get_bytes(url).decode("utf-8", errors="replace")


def _http_get_json(url: str):
    """Fetch JSON from a remote URL."""
    return json.loads(_http_get_text(url))


class ReferenceMatcher:
    """Match detections against one or more reference images of a specific animal."""

    def __init__(self, reference_paths: list[str]):
        self.orb = cv2.ORB_create(nfeatures=1000)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.references = []

        for reference_path in reference_paths:
            image = cv2.imread(reference_path)
            if image is None:
                raise ConfigurationError(f"Failed to load reference image: {reference_path}")

            descriptors, keypoint_count = self._compute_descriptors(image)
            if descriptors is None or keypoint_count == 0:
                raise ConfigurationError(
                    f"Reference image has no usable visual features: {reference_path}"
                )

            self.references.append({
                "path": reference_path,
                "descriptors": descriptors,
                "keypoint_count": keypoint_count,
            })

        if not self.references:
            raise ConfigurationError("At least one valid reference image is required")

    def _compute_descriptors(self, image) -> tuple[Optional[cv2.typing.MatLike], int]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape[:2]
        longest_side = max(height, width)
        if longest_side > 512:
            scale = 512 / longest_side
            gray = cv2.resize(gray, (int(width * scale), int(height * scale)))

        keypoints, descriptors = self.orb.detectAndCompute(gray, None)
        return descriptors, len(keypoints)

    def score(self, image) -> float:
        """Return the best normalized ORB match score across the references."""
        descriptors, keypoint_count = self._compute_descriptors(image)
        if descriptors is None or keypoint_count == 0:
            return 0.0

        best_score = 0.0
        for reference in self.references:
            raw_matches = self.matcher.knnMatch(reference["descriptors"], descriptors, k=2)
            good_matches = []
            for pair in raw_matches:
                if len(pair) < 2:
                    continue
                first, second = pair
                if first.distance < 0.75 * second.distance:
                    good_matches.append(first)

            denominator = max(1, min(reference["keypoint_count"], keypoint_count))
            score = len(good_matches) / denominator
            best_score = max(best_score, score)

        return best_score


class HDRelayLiveFrameSource:
    """Poll live frames from an HDRelay camera using its public frame endpoints."""

    def __init__(self, camera_id: str, host: str, position: str):
        self.camera_id = camera_id
        self.host = _normalize_remote_url(host).rstrip("/") + "/"
        self.position = position
        self.last_timestamp = None

    def _info_url(self) -> str:
        return (
            f"{self.host}api/frames/info"
            f"?camera={self.camera_id}&position={self.position}"
        )

    def _frame_url(self, timestamp: int) -> str:
        return f"{self.host}frames/{self.camera_id}/{self.position}/{timestamp}"

    def read(self):
        """Return the newest available frame, or None if no new frame exists yet."""
        info = _http_get_json(self._info_url())
        latest_timestamp = int(info["last"])
        if self.last_timestamp == latest_timestamp:
            return None

        frame_bytes = _http_get_bytes(self._frame_url(latest_timestamp))
        frame = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise RuntimeError(
                f"Failed to decode HDRelay frame for {self.camera_id} at {latest_timestamp}"
            )

        self.last_timestamp = latest_timestamp
        return frame

    def release(self):
        """Mirror the OpenCV VideoCapture interface."""
        return None

class Monitor:
    """
    Monitor live streams for detections from a configured target class.
    """
    def __init__(
        self,
        alerter: Optional[Alerter] = None,
        source_url: Optional[str] = None,
        youtube_url: Optional[str] = None,
        target_label: str = "hippopotamus",
        reference_name: Optional[str] = None,
        reference_images: Optional[list[str]] = None,
        reference_match_threshold: float = 0.08,
        min_confidence: float = 0.10,
        alert_cooldown: int = 300
    ):
        print("🎥 Loading detector...")

        self.config = get_config({
            "source_url": source_url,
            "youtube_url": youtube_url,
            "target_label": target_label,
            "reference_name": reference_name,
            "reference_images": reference_images,
            "reference_match_threshold": reference_match_threshold,
            "min_confidence": min_confidence,
            "alert_cooldown": alert_cooldown
        })

        if not self.config.get("source_url"):
            raise ValueError("No source URL provided! This shouldn't happen - please report this bug on GitHub.")

        self.alerter = alerter or LogAlerter()
        self.model = self._load_model()
        self.reference_matcher = self._load_reference_matcher()
        self.last_alert_time = 0

    def _load_model(self):
        """Load and optimize model for detection"""
        print("Loading detection model...")
        try:
            print("Loading OpenImages model...")
            model = YOLO('yolov8x-oiv7.pt')  # OpenImages V7 model

            requested_label = self.config["target_label"]
            print(f"\n🔍 Confirming that {requested_label} is in the model...")
            self.target_class, self.target_model_label = self._find_target_class(
                model,
                requested_label,
            )

            print(f"✨ Found {self.target_model_label} detection (class {self.target_class})")
            return model

        except ModelError:
            raise
        except Exception as e:
            print(f"Failed to load OpenImages model: {e}")
            raise ModelError(f"Couldn't find {self.config['target_label']} in the model!")

    def _find_target_class(self, model, requested_label: str) -> tuple[int, str]:
        """Resolve a requested class label against model class names."""
        normalized_names = {
            class_id: _normalize_label(name)
            for class_id, name in model.names.items()
        }
        candidates = _label_candidates(requested_label)

        for candidate in candidates:
            for class_id, normalized_name in normalized_names.items():
                if normalized_name == candidate:
                    return class_id, model.names[class_id]

        suggestions = get_close_matches(
            candidates[0],
            list(normalized_names.values()),
            n=5,
            cutoff=0.6,
        )
        suggestion_names = [
            model.names[class_id]
            for class_id, normalized_name in normalized_names.items()
            if normalized_name in suggestions
        ]
        suggestion_text = ""
        if suggestion_names:
            suggestion_text = f" Close matches: {', '.join(suggestion_names)}."

        raise ModelError(
            f"Couldn't find a model class for '{requested_label}'.{suggestion_text}"
        )

    def _get_stream_url(self, source_url: str) -> str:
        """Resolve a direct media URL from a supported page URL using yt-dlp."""
        ydl_opts = {
            'format': 'best',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(source_url, download=False)
                return info['url']
            except Exception as e:
                print(f"\n❌ Stream error: {str(e)}")
                print("💡 Tip: The stream might be offline. Try again later.")
                raise RuntimeError(f"Failed to get stream URL: {str(e)}")

    def _resolve_hdrelay_page_source(self, page_url: str) -> dict:
        """Resolve an HDRelay-backed page into a live frame polling source."""
        page_html = _http_get_text(page_url)
        match = re.search(r"HDRelay\.create\(\{[^}]*id:\s*['\"]([^'\"]+)['\"]", page_html)
        if not match:
            raise RuntimeError(f"Couldn't find an HDRelay camera on {page_url}")

        camera_id = match.group(1)
        player_config = _http_get_json(f"https://manage.hdrelay.com/player/{camera_id}")
        camera_status = player_config.get("camera", {}).get("status", {})
        if camera_status.get("online") is False:
            raise RuntimeError(f"HDRelay camera {camera_id} is currently offline")

        position = player_config.get("image", {}).get("position", "panorama")
        host = player_config.get("host")
        if not host:
            raise RuntimeError(f"HDRelay player config for {camera_id} did not include a frame host")

        return {
            "kind": "hdrelay_frames",
            "camera_id": camera_id,
            "host": host,
            "position": position,
            "page_url": page_url,
        }

    def _resolve_source(self, source_url: str) -> dict:
        """Resolve the configured source into either a video capture URL or a live frame source."""
        parsed = urlparse(source_url)
        if parsed.scheme in {"rtsp", "rtsps"}:
            return {"kind": "video_capture", "capture_url": source_url}

        lower_url = source_url.lower()
        if lower_url.endswith((".m3u8", ".mp4", ".mjpeg", ".jpg", ".jpeg")):
            return {"kind": "video_capture", "capture_url": source_url}

        if "pier39.com/sealions" in lower_url or "hdrelay.com" in lower_url:
            return self._resolve_hdrelay_page_source(source_url)

        capture_url = self._get_stream_url(source_url)
        return {"kind": "video_capture", "capture_url": capture_url}

    def _load_reference_matcher(self) -> Optional[ReferenceMatcher]:
        """Load reference images for individual-animal matching, if configured."""
        reference_images = self.config.get("reference_images")
        if not reference_images:
            return None

        normalized_paths = []
        for reference_image in reference_images:
            resolved = Path(reference_image).expanduser().resolve()
            if not resolved.exists():
                raise ConfigurationError(f"Reference image does not exist: {resolved}")
            normalized_paths.append(str(resolved))

        reference_name = self.config.get("reference_name") or "reference target"
        print(f"🖼️ Loading {len(normalized_paths)} reference images for {reference_name}...")
        matcher = ReferenceMatcher(normalized_paths)
        print(
            f"✨ Loaded reference matcher for {reference_name} "
            f"(threshold {self.config['reference_match_threshold']:.2f})"
        )
        return matcher

    def _crop_detection(self, frame, box) -> Optional[cv2.typing.MatLike]:
        """Crop a detection box from the current frame."""
        x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
        height, width = frame.shape[:2]
        x1 = max(0, min(x1, width))
        x2 = max(0, min(x2, width))
        y1 = max(0, min(y1, height))
        y2 = max(0, min(y2, height))
        if x2 <= x1 or y2 <= y1:
            return None
        return frame[y1:y2, x1:x2]

    def _process_frame(self, frame, check_count: int, target_label: str, subject_name: str):
        """Run detection logic for a single frame."""
        if check_count % 10 == 0:
            print(f"\n🔍 Check #{check_count}. Looking for {subject_name}...")

        current_time = time.time()
        results = self.model(frame, verbose=False)

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.model.names[class_id]

                match_score = None
                is_reference_match = True
                if class_id == self.target_class and confidence >= self.config["min_confidence"]:
                    if self.reference_matcher:
                        crop = self._crop_detection(frame, box)
                        if crop is not None:
                            match_score = self.reference_matcher.score(crop)
                        else:
                            match_score = 0.0
                        is_reference_match = (
                            match_score >= self.config["reference_match_threshold"]
                        )

                    if check_count % 4 == 0:
                        if match_score is None:
                            print(f"   🎯 Possible {target_label}! {confidence:.2%} confidence")
                        else:
                            print(
                                f"   🎯 {target_label} detected "
                                f"({confidence:.2%}, ref score {match_score:.2f})"
                            )
                elif "animal" in class_name.lower() and confidence > 0.6:
                    if check_count % 10 == 0:
                        print(f"   Found {class_name} with {confidence:.2%} confidence")

                if (
                    class_id == self.target_class
                    and confidence >= self.config["min_confidence"]
                    and is_reference_match
                    and current_time - self.last_alert_time > self.config["alert_cooldown"]
                ):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if match_score is None:
                        message = (
                            f"🎯 {target_label} detected at {timestamp}! "
                            f"(Confidence: {confidence:.2f})"
                        )
                    else:
                        message = (
                            f"🎯 {subject_name} matched at {timestamp}! "
                            f"(Detection: {confidence:.2f}, Reference: {match_score:.2f})"
                        )
                    self.alerter.send_alert(message)
                    self.last_alert_time = current_time

    def _monitor_video_capture(self, stream_url: str, target_label: str, subject_name: str):
        """Monitor a direct video stream via OpenCV."""
        cap = cv2.VideoCapture(stream_url)
        try:
            print(f"👀 Connected! Watching for {target_label} on {self.config['source_url']}")
            if self.reference_matcher:
                print(f"🧭 Reference matching is enabled for {subject_name}")

            check_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("📺 Failed to grab frame, retrying...")
                    time.sleep(60)
                    continue

                check_count += 1
                self._process_frame(frame, check_count, target_label, subject_name)
                time.sleep(1)
        finally:
            cap.release()

    def _monitor_hdrelay_frames(self, source: dict, target_label: str, subject_name: str):
        """Monitor an HDRelay page by polling for the latest live frame."""
        frame_source = HDRelayLiveFrameSource(
            camera_id=source["camera_id"],
            host=source["host"],
            position=source["position"],
        )
        print(
            f"👀 Connected! Polling live frames for {target_label} from "
            f"{source['page_url']} ({source['camera_id']})"
        )
        if self.reference_matcher:
            print(f"🧭 Reference matching is enabled for {subject_name}")

        check_count = 0
        while True:
            try:
                frame = frame_source.read()
            except Exception as e:
                print(f"📺 Failed to fetch live HDRelay frame, retrying soon... ({e})")
                time.sleep(5)
                continue

            if frame is None:
                time.sleep(1)
                continue

            check_count += 1
            self._process_frame(frame, check_count, target_label, subject_name)
            time.sleep(0.2)

    def start(self):
        """Start monitoring the stream"""
        print(f"\n📡 Connecting to stream: {self.config['source_url']}")
        target_label = self.target_model_label.title()
        subject_name = self.config.get("reference_name") or target_label

        try:
            source = self._resolve_source(self.config["source_url"])
            if source["kind"] == "hdrelay_frames":
                self._monitor_hdrelay_frames(source, target_label, subject_name)
            else:
                self._monitor_video_capture(source["capture_url"], target_label, subject_name)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping monitor...")
