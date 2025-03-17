# WNBA Bot

Books courts on HelloClub via REST API

## Getting Started

Environment Variables

Ensure credentials work with direct username and password - not the OAuth flow via Google or Facebook
```bash
HELLO_CLUB_USERNAME = "<USERNAME>"
HELLO_CLUB_PASSWORD = "<PASSWORD>"
```

Python Environment Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
```bash
uv sync
```

Run
```bash
python src/main.py
```

### TODO
- Config validation
- Scheduling via Cron
- Book adjacent courts if preferred court is not available

### Much later
- Periodically check courts for availability. Courts free up 2 days prior to booking to avoid fees


### Server timings from NZ

```
2025-03-17 08:44:52.549Z # Time request was sent from laptop
2025-03-17T08:44:52.965Z # Time booking was created (+416ms)
2025-03-17T08:44:53.074Z # Time confirmation email was sent (+109)
```