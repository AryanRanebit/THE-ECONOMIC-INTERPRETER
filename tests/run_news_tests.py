import sys, os, pandas as pd
sys.path.insert(0, os.getcwd())

from modules.news_data import (
    fetch_google_news_rss, deduplicate_articles,
    load_sample_news, get_economic_news, clean_html_text,
)

results = []

# Test 1: Live RSS
df = fetch_google_news_rss("India economy inflation GDP", timeout_seconds=10)
if df.empty:
    results.append(("Live RSS", "SKIP", "No articles returned (network unavailable or RSS blocked)"))
else:
    expected = {"title", "source", "published_at", "description", "url", "is_sample"}
    missing = expected - set(df.columns)
    if not missing and not any(df["is_sample"]):
        results.append(("Live RSS", "PASS", str(len(df)) + " articles, schema OK, is_sample=False"))
    else:
        results.append(("Live RSS", "FAIL", "missing=" + str(missing)))
    print("Live sample title:", df.iloc[0]["title"][:80])

# Test 2: Sample data
s = load_sample_news()
ok2 = (not s.empty) and bool(s["is_sample"].all())
results.append(("Sample Data", "PASS" if ok2 else "FAIL",
                str(len(s)) + " articles, all is_sample=" + str(ok2)))

# Test 3: URL dedup
d = pd.DataFrame([
    {"title": "A",  "source": "S1", "published_at": "2025", "description": "D", "url": "https://a.com", "is_sample": False},
    {"title": "A2", "source": "S2", "published_at": "2025", "description": "D", "url": "https://a.com", "is_sample": False},
    {"title": "B",  "source": "S3", "published_at": "2025", "description": "D", "url": "https://b.com", "is_sample": False},
])
r = deduplicate_articles(d)
results.append(("URL Dedup", "PASS" if len(r) == 2 else "FAIL",
                "3 in -> " + str(len(r)) + " out (expect 2)"))

# Test 4: Title dedup
d2 = pd.DataFrame([
    {"title": "Same Headline", "source": "X", "published_at": "2025", "description": "D", "url": "https://x.com/1", "is_sample": False},
    {"title": "same headline", "source": "Y", "published_at": "2025", "description": "D", "url": "https://y.com/2", "is_sample": False},
])
r2 = deduplicate_articles(d2)
results.append(("Title Dedup (case)", "PASS" if len(r2) == 1 else "FAIL",
                "2 in -> " + str(len(r2)) + " out (expect 1)"))

# Test 5: Missing fields
try:
    sparse = pd.DataFrame([{"title": "T", "source": None, "published_at": None, "description": None, "url": None, "is_sample": False}])
    deduplicate_articles(sparse)
    results.append(("Missing Fields", "PASS", "No crash on None fields"))
except Exception as e:
    results.append(("Missing Fields", "FAIL", str(e)))

# Test 6: HTML cleaning
raw = "<b>Food &amp; Fuel</b> Price Rise"
cleaned = clean_html_text(raw)
expected_clean = "Food & Fuel Price Rise"
results.append(("HTML Cleaning", "PASS" if cleaned == expected_clean else "FAIL", repr(cleaned)))

# Test 7: Empty response type safety
empty = fetch_google_news_rss("xyzzy_nonexistent_query_99999", timeout_seconds=5)
results.append(("Empty Response Type", "PASS" if isinstance(empty, pd.DataFrame) else "FAIL",
                "rows=" + str(len(empty))))

# Test 8: Sample mode API
payload = get_economic_news(query="India economy", use_sample_data=True)
ok8 = payload["is_sample"] and not payload["articles"].empty
results.append(("Sample Mode API", "PASS" if ok8 else "FAIL",
                "is_sample=" + str(payload["is_sample"]) + " articles=" + str(len(payload["articles"]))))

# Print summary
print()
print("-" * 65)
print("{:<25} {:<8} {}".format("TEST", "STATUS", "DETAILS"))
print("-" * 65)
fail_count = 0
for name, status, detail in results:
    print("{:<25} {:<8} {}".format(name, status, detail))
    if status == "FAIL":
        fail_count += 1
print("-" * 65)
print("Result: " + str(len(results)) + " tests, " + str(fail_count) + " failures")
if fail_count:
    sys.exit(1)
