# Editorial frontend (live)

`web/index.html` is the single-file editorial frontend (no build step) for The Economic Interpreter - and the source of the live site: the repo-root `index.html` and `public/index.html` are byte-identical copies of it.
It reads the JSON API in `api/index.py` (`/api?action=indicators|news|interpret|compare|analytics`). The Streamlit app is unchanged.

The earlier "Zero-Hallucination" design is archived at `index-classic.html` (repo root and `public/`), reachable from the site footer as "Classic dashboard view".

Run locally: `python dev_server.py 8000`, then open http://localhost:8000/ (the root serves `public/index.html`).
Use `?api=https://your-deployment/api` to point at a different API.

Visual language adapted from the free Midblock architecture template by 8B (MIT): https://github.com/8bsite/architecture-website-template
GSAP, ScrollTrigger and Lenis load from jsDelivr; fonts from Google Fonts.
