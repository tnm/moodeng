# moodeng

`moodeng` is a CLI and Python package for monitoring live animal streams with
YOLOv8-based detection.

The current code supports two source types:

- direct media or stream URLs that OpenCV or `yt-dlp` can open
- supported live pages that embed an `HDRelay` camera, including the PIER 39
  sea lion page

It can also do a second-stage reference-image match for cases where the base
detector only knows a generic class. That is the current path for identifying a
specific sea lion such as Chonkers on the PIER 39 feed.

## What It Does

- detects an OpenImages class such as `hippopotamus` or `Sea lion`
- reads live sources from YouTube-style pages, direct stream URLs, or supported
  `HDRelay` pages
- can restrict alerts to one specific animal by comparing detections against one
  or more reference images
- supports console, Twilio SMS, and Pushbullet alerts

## Current Limitations

- The underlying `yolov8x-oiv7.pt` model uses generic OpenImages labels.
  `Sea lion` exists, but species-level labels such as `Steller sea lion` do not.
- Individual-animal matching is heuristic. It depends heavily on camera angle,
  lighting, occlusion, and the quality of the reference images.
- Automated coverage is still minimal. There are basic helper/config tests, but
  validation is still mostly compile checks and smoke tests.

## Requirements

- Python 3.12
- macOS, Linux, or WSL

## Installation

```bash
git clone https://github.com/tnm/moodeng.git
cd moodeng
chmod +x install.sh
./install.sh
source .venv/bin/activate
```

## Basic Usage

If no URL is provided, the CLI tries to resolve the latest stream from
`@ZoodioThailand`.

```bash
moodeng
```

To watch a specific live page or stream:

```bash
moodeng --url "YOUR_STREAM_OR_PAGE_URL"
```

## PIER 39

The PIER 39 sea lion page is not a YouTube stream. It uses an `HDRelay` live
camera embed. The current code resolves that page to the underlying live frame
source automatically.

Generic sea lion detection:

```bash
moodeng \
  --url "https://www.pier39.com/sealions/" \
  --target-label "Sea lion"
```

Chonkers-only matching:

```bash
moodeng \
  --url "https://www.pier39.com/sealions/" \
  --target-label "Sea lion" \
  --reference-name "Chonkers" \
  --reference-image ./refs/chonkers-1.jpg \
  --reference-image ./refs/chonkers-2.jpg
```

If matching is too loose or too strict, tune the threshold:

```bash
moodeng \
  --url "https://www.pier39.com/sealions/" \
  --target-label "Sea lion" \
  --reference-name "Chonkers" \
  --reference-image ./refs/chonkers-1.jpg \
  --reference-threshold 0.12
```

The best reference images are cropped or nearly cropped views of the same
animal from the same camera, with stable lighting and pose.

The `./refs/chonkers-*.jpg` paths above are examples only. This repository does
not ship Chonkers reference images.

## CLI Options

Common options:

- `--url`: live page or stream URL
- `--target-label`: OpenImages class label to detect
- `--min-confidence`: minimum YOLO confidence for a candidate detection
- `--alert-cooldown`: minimum seconds between alerts
- `--debug`: enable debug logging

Reference matching:

- `--reference-name`: friendly label for alerts
- `--reference-image`: path to a reference image; repeat to add more images
- `--reference-threshold`: minimum reference-match score required to alert

Alerts:

- `--alert-type log`
- `--alert-type sms`
- `--alert-type push`

Twilio:

- `--twilio-sid`
- `--twilio-token`
- `--twilio-from`
- `--twilio-to`

Pushbullet:

- `--pushbullet-key`

## Alert Examples

SMS:

```bash
moodeng \
  --url "https://www.pier39.com/sealions/" \
  --target-label "Sea lion" \
  --alert-type sms \
  --twilio-sid "YOUR_SID" \
  --twilio-token "YOUR_TOKEN" \
  --twilio-from "+1234567890" \
  --twilio-to "+1234567890"
```

Pushbullet:

```bash
moodeng \
  --url "https://www.pier39.com/sealions/" \
  --target-label "Sea lion" \
  --alert-type push \
  --pushbullet-key "YOUR_KEY"
```

## Python Usage

The public Python entry point is `Monitor`.

Basic example:

```python
from moodeng import Monitor

monitor = Monitor(
    source_url="https://www.pier39.com/sealions/",
    target_label="Sea lion",
    min_confidence=0.2,
    alert_cooldown=300,
)
monitor.start()
```

Reference matching:

```python
from moodeng import Monitor

monitor = Monitor(
    source_url="https://www.pier39.com/sealions/",
    target_label="Sea lion",
    reference_name="Chonkers",
    reference_images=[
        "./refs/chonkers-1.jpg",
        "./refs/chonkers-2.jpg",
    ],
    reference_match_threshold=0.12,
)
monitor.start()
```

Custom alerts:

```python
from moodeng import Alerter, Monitor


class MyAlerter(Alerter):
    def send_alert(self, message: str) -> None:
        print(message)


monitor = Monitor(
    alerter=MyAlerter(),
    source_url="https://www.pier39.com/sealions/",
    target_label="Sea lion",
)
monitor.start()
```

## Development Notes

- The package name is still `moodeng`, even though the current behavior is no
  longer specific to Moo Deng.
- The repository currently depends on heavyweight vision packages and model
  downloads, so startup can be slow on a fresh environment.

## Validation

Recent manual checks for the current branch:

- `python3 -m compileall src/moodeng`
- `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests`
- `git diff --check`
- Pier 39 live-source smoke test:
  resolved `https://www.pier39.com/sealions/` to camera `CID_UROS0000008D`
  and fetched a live `6526x1576` frame through the `HDRelay` path

## Contributing

1. Create a branch.
2. Make the change.
3. Run the relevant checks.
4. Open a pull request.
