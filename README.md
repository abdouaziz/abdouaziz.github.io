# lamia

Python client for the [LAM TTS API](https://ttsapi.lafricamobile.com/api/docs) — converts French text into natural-sounding speech for African languages (Wolof, and more).

## Installation

```bash
pip install lamia
```

## Authentication

Lamia supports two authentication modes.

**API key** (recommended):

```python
from lamia import Lamia

client = Lamia(api_key="ae_live_...")
```

**Username and password**:

```python
client = Lamia(username="your_account_id", password="your_password")
```

In username/password mode the client logs in automatically on the first request and refreshes the token transparently when it expires.

---

## Text-to-Speech

### Synthesize — translate + vocalize in one call

```python
result = client.synthesize("Bonjour le monde", to_lang="wolof", pitch=0, speed=1)
print(result.path_audio)      # URL of the generated audio file
print(result.duration)        # duration in seconds
```

### Translate only — no audio generated

```python
post = client.translate("Bonjour le monde", to_lang="wolof")
print(post.translated_text)
```

### Vocalize only — synthesize without translating

```python
result = client.vocalize("Jërejëf", to_lang="wolof", pitch=0, speed=1)
print(result.path_audio)
```

### List supported languages

```python
languages = client.get_languages()
print(languages)   # e.g. ["wolof", ...]
```

### Retrieve past TTS requests

```python
history = client.get_tts_requests()
for item in history:
    print(item.text, item.to_lang, item.path_audio)
```

**Parameters for synthesize / vocalize:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `str` | — | French source text |
| `to_lang` | `str` | — | Target language (e.g. `"wolof"`) |
| `pitch` | `float` | `0` | Voice pitch adjustment |
| `speed` | `float` | `1` | Speech speed multiplier |

---

## Speech-to-Text

### Transcribe an audio file

```python
# From a file path
result = client.transcribe("recording.wav", to_lang="wolof")
print(result.transcription)
print(result.duration)

# From bytes
with open("recording.wav", "rb") as f:
    result = client.transcribe(f.read(), to_lang="wolof")

# From a file-like object
with open("recording.wav", "rb") as f:
    result = client.transcribe(f, to_lang="wolof")
```

### Retrieve past STT requests

```python
history = client.get_stt_requests()
for item in history:
    print(item.transcription, item.to_lang)

# Single request by ID
item = client.get_stt_request(42)
print(item.transcription)
```

---

## Push TTS voice call *(admin only)*

Generate audio from text and immediately initiate a voice call to a list of contacts.

```python
client.push_tts(
    "Message urgent pour tous les villageois",
    to_lang="wolof",
    contacts_list=["+221700000000", "+221700000001"],
    pitch=0,
    speed=1,
)
```

---

## Credits

```python
credits = client.get_credits()
print(credits.remaining_credit)   # minutes remaining
print(credits.total_credit)       # total allocated
print(credits.consumed_credit)    # minutes used
```

---

## Statistics

```python
# Current period
stat = client.get_current_statistics()
print(stat.success_requests, stat.failed_requests, stat.total_requests)

# Full history
for stat in client.get_statistics():
    print(stat.date, stat.total_requests)
```

---

## Context manager

The client implements `__enter__` / `__exit__` so it can be used as a context manager, which ensures the underlying HTTP connection is closed cleanly.

```python
with Lamia(api_key="ae_live_...") as client:
    result = client.synthesize("Bonjour", to_lang="wolof")
    print(result.path_audio)
```

---

## Error handling

```python
from lamia import Lamia, AuthenticationError, APIError

try:
    client = Lamia(api_key="ae_live_invalid")
    client.get_credits()
except AuthenticationError as e:
    print("Auth failed:", e)
except APIError as e:
    print(f"API error {e.status_code}:", e.detail)
```

| Exception | Raised when |
|---|---|
| `AuthenticationError` | Invalid credentials or expired API key |
| `APIError` | The API returns an HTTP 4xx/5xx response |
| `LamiaError` | Base class for all lamia exceptions |

---

## Full API reference

| Method | Returns | Description |
|---|---|---|
| `get_credits()` | `CreditInfo` | Remaining credit balance |
| `get_languages()` | `list[str]` | Supported TTS languages |
| `get_tts_requests()` | `list[GetPost]` | All past TTS requests |
| `synthesize(text, to_lang)` | `PostVocalized` | Translate + vocalize |
| `translate(text, to_lang)` | `Post` | Translate only |
| `vocalize(text, to_lang)` | `PostVocalized` | Vocalize only |
| `push_tts(text, to_lang, contacts_list)` | `dict` | TTS voice call *(admin)* |
| `transcribe(audio, to_lang)` | `AudioToText` | Speech-to-text |
| `get_stt_requests()` | `list[AudioToText]` | All past STT requests |
| `get_stt_request(id)` | `AudioToText` | Single STT request by ID |
| `get_statistics()` | `list[Statistic]` | Historical usage stats |
| `get_current_statistics()` | `Statistic` | Current period stats |

---

## License

MIT
