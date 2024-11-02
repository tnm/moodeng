from abc import ABC, abstractmethod
from twilio.rest import Client
from pushbullet import Pushbullet

class Alerter(ABC):
    """Abstract base class for different types of alerts"""
    @abstractmethod
    def send_alert(self, message: str) -> None:
        """Send an alert with the given message"""
        pass

class LogAlerter(Alerter):
    """Simple console logging alerter"""
    def send_alert(self, message: str) -> None:
        print(f"[ALERT] {message}")

class SMSAlerter(Alerter):
    """SMS alerter using Twilio"""
    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.to_number = to_number

    def send_alert(self, message: str) -> None:
        self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=self.to_number
        )

class PushAlerter(Alerter):
    """Push notification alerter using Pushbullet"""
    def __init__(self, api_key: str):
        self.pb = Pushbullet(api_key)

    def send_alert(self, message: str) -> None:
        self.pb.push_note("Moo Deng Alert! 🦛", message)