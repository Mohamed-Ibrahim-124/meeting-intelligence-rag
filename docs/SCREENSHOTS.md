# Screenshots

Captured from a local run (`python scripts/capture_screenshots.py`).

| File | Screen |
|------|--------|
| [01-home-upload.png](screenshots/01-home-upload.png) | Home — text transcript upload |
| [02-home-audio.png](screenshots/02-home-audio.png) | Home — audio upload tab |
| [03-meeting-detail.png](screenshots/03-meeting-detail.png) | Meeting detail — transcript & metadata |
| [04-meeting-chat.png](screenshots/04-meeting-chat.png) | Grounded chat with suggested question |
| [05-meeting-intelligence.png](screenshots/05-meeting-intelligence.png) | Summary, decisions, action items |
| [06-api-docs.png](screenshots/06-api-docs.png) | FastAPI OpenAPI docs |

Regenerate after UI changes:

```powershell
.\scripts\start-local.ps1
python scripts/seed_samples.py
python scripts/capture_screenshots.py
```

Uses system **Edge** via Playwright (`channel="msedge"`) — no bundled Chromium download required.
