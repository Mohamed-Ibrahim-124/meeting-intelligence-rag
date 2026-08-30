# Sample audio

Public test clips for trying the **Audio** upload path locally.

| File | Source | Notes |
|------|--------|-------|
| `jfk.wav` | [openai/whisper `tests/jfk.flac`](https://github.com/openai/whisper/blob/main/tests/jfk.flac) | ~11s clear English; 16 kHz mono WAV |
| `jfk.flac` | Same | Original upstream file |

## Try it

1. Start the app (`.\scripts\start-local.ps1` or `docker compose up`)
2. Open http://localhost:3000 → **Audio** tab
3. Upload `jfk.wav`, speaker label e.g. `President Kennedy`

Or via API:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/meetings/from-audio \
  -F "title=JFK sample" \
  -F "default_speaker=President Kennedy" \
  -F "file=@samples/audio/jfk.wav"
```

First audio upload downloads the Whisper model configured in `.env` (`WHISPER_MODEL_SIZE`, default `small`).
