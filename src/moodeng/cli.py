import sys
import os
import subprocess
import argparse
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)


def main():
    parser = argparse.ArgumentParser(
        description='Monitor live streams for animal detections',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Basic configuration
    parser.add_argument('--url', 
                       help='Live page or stream URL (defaults to the latest configured stream)')
    parser.add_argument('--config', 
                       help='Path to config file')
    parser.add_argument('--min-confidence', 
                       type=float,
                       default=0.20,
                       help='Minimum confidence threshold for detection')
    parser.add_argument('--target-label',
                       default=None,
                       help='OpenImages class to detect (for example: hippopotamus, "Sea lion")')
    parser.add_argument('--reference-name',
                       default=None,
                       help='Friendly name for reference-image matching, e.g. "Chonkers"')
    parser.add_argument('--reference-image',
                       action='append',
                       default=None,
                       help='Path to a reference image for the specific animal you want to match; repeat this flag to add more images')
    parser.add_argument('--reference-threshold',
                       type=float,
                       default=None,
                       help='Minimum reference match score for alerting when using --reference-image')
    parser.add_argument('--alert-cooldown', 
                       type=int,
                       default=300,
                       help='Minimum time between alerts in seconds')
    
    # Alert configuration
    parser.add_argument('--alert-type',
                       choices=['log', 'sms', 'push'],
                       help='Type of alerts to send')
    
    # Twilio configuration
    parser.add_argument('--twilio-sid',
                       help='Twilio account SID')
    parser.add_argument('--twilio-token',
                       help='Twilio auth token')
    parser.add_argument('--twilio-from',
                       help='Twilio from number')
    parser.add_argument('--twilio-to',
                       help='Twilio to number')
    
    # Pushbullet configuration
    parser.add_argument('--pushbullet-key',
                       help='Pushbullet API key')
    
    # Debug mode
    parser.add_argument('--debug',
                       action='store_true',
                       help='Enable debug mode')
    
    # Force new environment
    parser.add_argument('--fresh',
                       action='store_true',
                       help='Force creation of fresh environment')
    
    # Version
    parser.add_argument('--version',
                       action='version',
                       version=f'%(prog)s 0.1.0')
    
    args = parser.parse_args()
    
    # First check for live stream before any setup
    from .config import get_latest_stream_url
    
    # Get the stream URL either from args or by finding latest
    stream_url = args.url or get_latest_stream_url()
    if not stream_url:
        print("\n❌ No live stream available right now.")
        print("💡 Tips:")
        print("   1. The stream might be offline - try again later")
        print("   2. Or specify a different URL with --url")
        print("   3. Check https://www.youtube.com/@ZoodioThailand/live")
        return 0
    
    print(f"🎥 Found source: {stream_url}")
    print("Setting up moodeng...")
    
    try:
        print("🔍 Checking dependencies...")
        # Import the heavy packages after initial message
        import cv2
        import pafy
        import pandas
        import numpy
        import yaml
        import matplotlib
        import seaborn
        import tqdm
        import psutil
        import scipy
        import ultralytics
        import git
    except ImportError as e:
        print(f"📦 Installing required packages (this might take a minute)...")
        try:
            subprocess.check_call([
                "uv", "pip", "install",
                "torch", "opencv-python", "pafy", "youtube-dl",
                "pandas", "numpy", "pyyaml", "matplotlib",
                "seaborn", "tqdm", "psutil", "scipy", "ultralytics",
                "gitpython"
            ])
            print("Dependencies installed. Restarting moodeng...")
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            print("💡 Try: pipx install --force moodeng")
            sys.exit(1)
    
    # Only import our own modules after dependency check
    from .detector import Monitor
    from .alerters import LogAlerter, SMSAlerter, PushAlerter
    from .config import get_config
    from .exceptions import ConfigurationError

    # Load config file if specified
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config file: {e}")
    
    # Create alerter
    alert_type = args.alert_type or (config or {}).get('alert_type', 'log')
    
    if alert_type == 'sms':
        config = config or {}
        twilio_config = config.get('twilio', {})
        
        # Prefer command line args over config
        account_sid = args.twilio_sid or twilio_config.get('account_sid')
        auth_token = args.twilio_token or twilio_config.get('auth_token')
        from_number = args.twilio_from or twilio_config.get('from_number')
        to_number = args.twilio_to or twilio_config.get('to_number')
        
        if not all([account_sid, auth_token, from_number, to_number]):
            raise ConfigurationError("Missing required Twilio configuration")
        
        alerter = SMSAlerter(account_sid, auth_token, from_number, to_number)
        
    elif alert_type == 'push':
        config = config or {}
        pushbullet_config = config.get('pushbullet', {})
        
        api_key = args.pushbullet_key or pushbullet_config.get('api_key')
        
        if not api_key:
            raise ConfigurationError("Missing Pushbullet API key")
        
        alerter = PushAlerter(api_key)
        
    else:
        alerter = LogAlerter()
    
    # Create monitor with merged configuration
    monitor_config = {
        'source_url': stream_url,  # Use the URL we already found
    }
    
    if config:
        monitor_config.update(config)

    if args.target_label is not None:
        monitor_config['target_label'] = args.target_label
    if args.reference_name is not None:
        monitor_config['reference_name'] = args.reference_name
    if args.reference_image is not None:
        monitor_config['reference_images'] = args.reference_image
    if args.reference_threshold is not None:
        monitor_config['reference_match_threshold'] = args.reference_threshold
    if args.min_confidence is not None:
        monitor_config['min_confidence'] = args.min_confidence
    if args.alert_cooldown is not None:
        monitor_config['alert_cooldown'] = args.alert_cooldown
    
    # Enable debug mode if specified
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print("Debug mode enabled")
    
    # Create and start monitor
    print("🔧 Setting up detector...")
    monitor = Monitor(
        alerter=alerter,
        **monitor_config
    )
    
    try:
        print("👀 Watching the configured live source (Press Ctrl+C to stop)...")
        monitor.start()
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    except ConfigurationError as e:
        print(f"⚠️  Configuration error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
