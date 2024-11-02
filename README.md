# 🦛 moodeng.py

Powerful CLI and Python library for monitoring YouTube live streams for 
Moo Deng appearances using state-of-the-art computer vision. 

![GbXCLDMbgAAGY9Y](https://github.com/user-attachments/assets/a7cf05ac-13dc-41da-ae1c-b29577a863e0)


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

### Installation

Install pipx if you haven't already

```bash
brew install pipx
pipx ensurepath
```

You can install `moodeng` directly from GitHub:

```
pipx install git+https://github.com/tnm/moodeng.git
```

Or if you've cloned the repository:

```
git clone https://github.com/tnm/moodeng.git
cd moodeng
pipx install .
```

### Run

The easiest way to start monitoring is just to use the CLI:

```bash
moodeng
```

It may take a minute to setup the first time you run it. But Moo Deng is worth it.

The first time you run `moodeng`, it will:
1. Set up the required environment
2. Download the model
3. Connect to the stream
4. Start watching for Moo Deng

## 📓 Important Notes

* The live stream from Moo Deng's YouTube channel is *usually* online, but it could be offline. If it's offline, you'll get an error, and can try again later.

* The Moo Deng ML model detection is basic for now, so you may get alerts when Jonah (i.e., Moo Deng's mother) appears. She is noticeably larger than Moo Deng, as she is an adult. Sometimes the stream features only Jonah, sometimes it's both Jonah and Moo Deng. 

* Potentially you might only see Moo Deng, but that is uncommon since she is a baby.

* In any case, the model is not yet fine-tuned for Moo Deng, but pull requests are welcome and we can work together to improve it. Ideally, you could choose Jonah, Moo Deng, or both.

* Detection numbers are may be lower than expected, since the model is trained on the common hippo (*Hippopotamus amphibius*, and not Moo Deng's species—the pygmy hippo (*Choeropsis liberiensis*). This will improve. Also, given this, detection alerts are set relatively low—so don't worry, you should still get Moo Deng alerts.

### Update to latest version
```bash
pipx upgrade moodeng
```

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

The CLI is cool but you can also work with `moodeng` directly from Python. 
For example, you may want to integrate this library into another project, 
(e.g, Enterprise SaaS app that monitors your customers' streams for pygmy hippos, etc etc.)

```python
from moodeng import monitor, LogAlerter

# Basic usage - defaults to Moo Deng's stream
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

### Advanced Configuration

```python
from moodeng import monitor, LogAlerter

# All options
m = monitor(
    youtube_url="YOUR_YOUTUBE_URL",  # Optional: defaults to latest Moo Deng stream
    alerter=LogAlerter(),            # Optional: defaults to console logging
    min_confidence=0.7,              # Optional: detection sensitivity (0-1)
    alert_cooldown=300               # Optional: seconds between alerts
)

# Start monitoring
m.start()
```

## 📝 Configuration

You can use a YAML config file for persistent settings:

```yaml
# config.yaml
youtube_url: "YOUR_YOUTUBE_URL"  # Optional: defaults to Moo Deng's stream
alert_type: "push"  # log, sms, or push
min_confidence: 0.65
alert_cooldown: 300  # seconds between alerts

# Optional: for SMS alerts
twilio:
  account_sid: "YOUR_SID"
  auth_token: "YOUR_TOKEN"
  from_number: "+1234567890"
  to_number: "+1234567890"

# Optional: for push notifications
pushbullet:
  api_key: "YOUR_KEY"
```

Then run:
```bash
moodeng --config config.yaml
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

### Custom Alerters
Create your own alert system:

```python
from moodeng import Alerter, monitor

class DiscordAlerter(Alerter):
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_alert(self, message: str):
        # Send to Discord
        pass

# Use it
m = monitor(alerter=DiscordAlerter("webhook_url"))
m.start()
```

## 🔧 Troubleshooting

Common issues and solutions:

### Installation Issues
```bash
# Force a fresh installation
pipx uninstall moodeng
pipx install git+https://github.com/tnm/moodeng.git
```

### Runtime Issues
```bash
# Run in debug mode
moodeng --debug

# If you see dependency errors
pipx install --force moodeng
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
1. Check the troubleshooting guide above
2. Run with `--debug` for more information
3. [Open an issue](https://github.com/tnm/moodeng/issues)

## 🔒 Security

Found a security issue? I would be incredibly impressed, and will send you a
hippo figurine as a thank you. Email me at ted@cased.com.
