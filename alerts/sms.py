"""
Africa's Talking SMS (HTTPS). No-op if credentials are missing.

https://developers.africastalking.com/docs/sms/sending/post
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

AFRICASTALKING_URL = 'https://api.africastalking.com/version1/messaging'


def send_sms(to_e164: str, message: str) -> bool:
    """
    Send a single SMS. ``to_e164`` should include country code (e.g. +221...).

    Returns True if the API accepted the request (HTTP 2xx and success in JSON).
    """
    username = getattr(settings, 'AFRICASTALKING_USERNAME', '') or ''
    api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '') or ''
    if not username or not api_key or not to_e164.strip() or not message.strip():
        return False

    body = urllib.parse.urlencode(
        {
            'username': username,
            'to': to_e164.strip(),
            'message': message[:480],
        }
    ).encode('utf-8')

    req = urllib.request.Request(
        AFRICASTALKING_URL,
        data=body,
        method='POST',
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apiKey': api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            data = json.loads(raw)
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Africa's Talking SMS failed: %s", exc)
        return False
    except json.JSONDecodeError:
        logger.warning("Africa's Talking non-JSON response: %s", raw[:300])
        return False

    recipients = (data or {}).get('SMSMessageData', {}).get('Recipients') or []
    if not recipients:
        logger.warning('Africa\'s Talking unexpected response: %s', data)
        return False
    status = recipients[0].get('status') if isinstance(recipients[0], dict) else None
    ok = status == 'Success' or status == 'Sent'
    if not ok:
        logger.warning('Africa\'s Talking recipient status: %s', recipients[0])
    return bool(ok)
