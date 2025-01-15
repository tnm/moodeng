# 🦛 moodeng.py

Powerful CLI and Python library for monitoring YouTube live streams for 
Moo Deng appearances using state-of-the-art computer vision. 

<img width="1048" alt="image" src="https://github.com/user-attachments/assets/1c946d3b-7955-4ae4-a158-9df329e702db">

## ✨ Features

- 🔍 Real-time hippo detection using YOLOv8
- 🇹🇭 Defaults to the latest live Moo Deng stream from Zoodio Thailand
- 🌙 Probably works in both day and night conditions
- 📱 Multiple alert types:
  - Console logging (default)
  - SMS notifications (via Twilio)
  - Push notifications (via Pushbullet)
  - Custom alerts 

## 🚀 Quick Start

### Requirements

- Python 3.12 (required for PyTorch compatibility)
- macOS, Linux, or WSL

### Installation

```bash
# 1. Get Python 3.12 if needed
brew install pyenv
pyenv install 3.12
pyenv global 3.12

# 2. Clone and install
git clone https://github.com/tnm/moodeng.git
cd moodeng
chmod +x install.sh
./install.sh

# 3. Activate environment
source .venv/bin/activate
```

### Run

Start watching for hippos:
```bash
moodeng
```

That's it! First run will download the ML model and start monitoring.

## 🛠️ Configuration

### Alert Types

Console logging (default):
```bash
moodeng
```

SMS alerts (requires Twilio):
```bash
moodeng --alert-type sms \
  --twilio-sid "YOUR_SID" \
  --twilio-token "YOUR_TOKEN" \
  --twilio-from "+1234567890" \
  --twilio-to "+1234567890"
```

Push notifications (requires Pushbullet):
```bash
moodeng --alert-type push --pushbullet-key "YOUR_KEY"
```

### Options

```bash
# Custom stream URL
moodeng --url "YOUR_YOUTUBE_URL"

# Adjust detection sensitivity
moodeng --min-confidence 0.8

# Change alert frequency
moodeng --alert-cooldown 600  # 10 minutes

# Debug mode
moodeng --debug
```

## 📝 Notes

* The live stream is usually online but could be offline. If offline, try again later.
* Detection works for both Moo Deng (baby) and Jonah (mother).
* Model trained on common hippos, so detection threshold is set low for pygmy hippos.

## 🆘 Support

1. Run with `--debug` for more information
2. [Open an issue](https://github.com/tnm/moodeng/issues)
3. Email ted@cased.com

## 📄 License

MIT License. See `LICENSE` for details.
