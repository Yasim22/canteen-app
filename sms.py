import os


def normalize_phone(phone: str) -> str:
    """0244123456 -> +233244123456"""
    phone = phone.strip().replace(" ", "")
    if phone.startswith("0"):
        return "+233" + phone[1:]
    if phone.startswith("233"):
        return "+" + phone
    return phone


def send_sms(to: str, message: str) -> bool:
    """Send an SMS via Africa's Talking. Falls back to console if no key/network."""
    username = os.getenv("AT_USERNAME", "sandbox")
    api_key = os.getenv("AT_API_KEY")
    if not api_key:
        print(f"[SMS-FALLBACK] To {to}: {message}")
        return False
    try:
        import africastalking
        africastalking.initialize(username, api_key)
        africastalking.SMS.send(message, [to])
        return True
    except Exception as e:
        print(f"[SMS-ERROR] {e}")
        return False