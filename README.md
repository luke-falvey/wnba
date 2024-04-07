# WNBA Bot

Books courts on HelloClub via REST API

## Getting Started

Environment Variables

Ensure credentials work with direct username and password - not the OAuth flow via Google or Facebook
```bash
HELLO_CLUB_USERNAME = "<USERNAME>"
HELLO_CLUB_PASSWORD = "<PASSWORD>"
```

Python virtual environment setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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