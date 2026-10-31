# Editorial frontend (additional track)

`web/index.html` is a single-file frontend (no build step) for The Economic Interpreter.
It reads the JSON API in `api/index.py` (`/api?action=indicators|news|interpret`). The Streamlit app is unchanged.

Run locally: `python dev_server.py 8000`, then open http://localhost:8000/web/index.html
Use `?api=https://your-deployment/api` to point at a different API.

Visual language adapted from the free Midblock architecture template by 8B (MIT): https://github.com/8bsite/architecture-website-template
GSAP, ScrollTrigger and Lenis load from jsDelivr; fonts from Google Fonts.
