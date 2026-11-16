import time
import requests


def get_json(url, params=None, headers=None, retries=5, timeout=60):
    """GET with simple exponential backoff on rate limits and server errors."""
    for attempt in range(retries):
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
