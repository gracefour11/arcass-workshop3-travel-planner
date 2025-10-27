import requests

HEADERS = {
    "User-Agent": "DevTravelPlanner/1.0 (local dev)"
}

def get_summary_from_wikipedia(title):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("extract", "")
    except Exception as e:
        print(f"❌ Failed to get summary for {title}: {e}")
        return ""