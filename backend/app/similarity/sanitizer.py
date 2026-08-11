import re
from typing import Dict, Tuple

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_REGEX = r"\+?\b\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"
IP_REGEX = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"

def sanitize_text(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Scans the text for sensitive information (Emails, Phone Numbers, IP Addresses)
    and replaces them with secure placeholders. Returns the sanitized text and
    a mapping dict to restore them later.
    """
    mask_map = {}
    counter = 0
    sanitized = text

    # Helper to mask a pattern
    def mask_pattern(pattern: str, placeholder_prefix: str, current_text: str) -> str:
        nonlocal counter
        for match in set(re.findall(pattern, current_text)):
            placeholder = f"[{placeholder_prefix}_{counter}]"
            mask_map[placeholder] = match
            current_text = current_text.replace(match, placeholder)
            counter += 1
        return current_text

    # Mask Emails
    sanitized = mask_pattern(EMAIL_REGEX, "MASK_EMAIL", sanitized)
    
    # Mask Phones
    sanitized = mask_pattern(PHONE_REGEX, "MASK_PHONE", sanitized)
    
    # Mask IPs
    sanitized = mask_pattern(IP_REGEX, "MASK_IP", sanitized)

    return sanitized, mask_map

def desanitize_text(text: str, mask_map: Dict[str, str]) -> str:
    """
    Restores the original values of masked placeholders in the text.
    """
    desanitized = text
    for placeholder, original in mask_map.items():
        desanitized = desanitized.replace(placeholder, original)
    return desanitized
