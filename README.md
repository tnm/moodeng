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
  - SMS notifications (via Twilio, could use more testing)
  - Push notifications (via Pushbullet, could use more testing)
  - Custom alerts 

Check out notes below for more details and caveats.

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

That's it! First run will:
1. Download the ML model
2. Connect to Moo Deng's stream
3. Start watching for hippos

## 📓 Important Notes

* The live stream from Moo Deng's YouTube channel is *usually* online, but it could be offline. If it's offline, you'll get an error, and can try again later.

* The Moo Deng ML model detection is basic for now, so you may get alerts when Jonah (i.e., Moo Deng's mother) appears. She is noticeably larger than Moo Deng, as she is an adult. Sometimes the stream features only Jonah, sometimes it's both Jonah and Moo Deng. 

* Potentially you might only see Moo Deng, but that is uncommon since she is a baby.

* In any case, the model is not yet fine-tuned for Moo Deng, but pull requests are welcome and we can work together to improve it. Ideally, you could choose Jonah, Moo Deng, or both.

* Detection numbers may be lower than expected, since the model is trained on the common hippo (*Hippopotamus amphibius*), and not Moo Deng's species—the pygmy hippo (*Choeropsis liberiensis*). This will improve. Given this, detection alerts are set relatively low: so don't worry, you should still get Moo Deng alerts.

## 💫 More things you can do

Explicitly specify a different stream in case the default one goes offline
or you want to try with your own stream:
```bash
moodeng --url "YOUR_YOUTUBE_URL"
```

Get SMS notifications (requires Twilio account):
```bash
moodeng --alert-type sms \
  --twilio-sid "YOUR_SID" \
  --twilio-token "YOUR_TOKEN" \
  --twilio-from "+1234567890" \
  --twilio-to "+1234567890"
```

Get push notifications (requires Pushbullet account):
```bash
moodeng --alert-type push --pushbullet-key "YOUR_KEY"
```

## 🐍 Python Usage

The CLI is cool, but you can also work with `moodeng` directly from Python. 
You may want to integrate this library into another project, e.g, Enterprise SaaS app that monitors your 
customers' streams for pygmy hippos, etc etc.

```python
from moodeng import monitor, LogAlerter

# Basic usage (defaults to Moo Deng's stream)
m = monitor(alerter=LogAlerter())
m.start()

# Or customize everything
m = monitor(
    youtube_url="YOUR_YOUTUBE_URL",
    min_confidence=0.7,
    alert_cooldown=300 # seconds between alerts
)
m.start()
```

### Different Alert Types

```python
# SMS Alerts
from moodeng import monitor, SMSAlerter

m = monitor(
    alerter=SMSAlerter(
        account_sid="YOUR_SID",
        auth_token="YOUR_TOKEN",
        from_number="+1234567890",
        to_number="+1234567890"
    )
)
m.start()

# Push Notifications
from moodeng import monitor, PushAlerter

m = monitor(
    alerter=PushAlerter(api_key="YOUR_PUSHBULLET_KEY")
)
m.start()
```

### Custom Alert Handler

```python
from moodeng import Alerter, monitor

class MyCustomAlerter(Alerter):
    def send_alert(self, message: str):
        # Do something with the alert
        print(f"Custom alert: {message}")

m = monitor(alerter=MyCustomAlerter())
m.start()
```

## 🛠️ Advanced Usage from CLI

### Debug Mode
If something's not working:
```bash
moodeng --debug
```

### Detection Settings
Adjust how sensitive the hippo detection is:
```bash
# More selective detection
moodeng --min-confidence 0.8

# Change how often you get alerts
moodeng --alert-cooldown 600  # 10 minutes
```

## 🤝 Contributing

Please do! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add AmazingFeature'`)
6. Push (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🆘 Support

Need help?
1. Run with `--debug` for more information
2. [Open an issue](https://github.com/tnm/moodeng/issues)
3. Email ted@cased.com

## 🔒 Security

Found a security issue? I would be incredibly impressed, and will try to send you a
hippo figurine as a thank you. Email me at ted@cased.com.
