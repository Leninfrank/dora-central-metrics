import requests, json, os
from datetime import datetime, timedelta

# Setup GitHub API access
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN not set")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
BASE_URL = "https://api.github.com"

def check_rate_limit():
    url = f"{BASE_URL}/rate_limit"
    res = requests.get(url, headers=HEADERS)
    print("⏳ Rate Limit:", res.json())

def get_commit_count(owner, repo, since):
    url = f"{BASE_URL}/repos/{owner}/{repo}/commits?since={since}&per_page=100"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"❌ Failed to fetch commits for {repo}: {res.status_code}")
        print(res.text)
        return 0
    return len(res.json())

def get_pr_lead_time(owner, repo):
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls?state=closed&per_page=100"
    res = requests.get(url, headers=HEADERS)

    try:
        prs = res.json()
    except Exception as e:
        print(f"❌ Failed to parse PRs JSON for {repo}: {e}")
        print(res.text)
        return 0

    if not isinstance(prs, list):
        print(f"❌ Unexpected response for PRs in {repo}: {prs}")
        return 0

    times = []
    for pr in prs:
        if isinstance(pr, dict) and pr.get("merged_at"):
            created = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            merged = datetime.strptime(pr["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
            times.append((merged - created).total_seconds())

    return round(sum(times) / len(times) / 3600, 2) if times else 0

def main():
    print("🔎 Starting DORA metrics collection...")
    check_rate_limit()

    # Read list of repos
    if not os.path.exists("repos.txt"):
        raise FileNotFoundError("repos.txt file not found")
    
    with open("repos.txt") as f:
        repos = [line.strip() for line in f if line.strip()]

    since = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    results = []

    for repo in repos:
        print(f"📦 Processing {repo}...")
        owner, name = repo.split("/")
        try:
            deployment_freq = get_commit_count(owner, name, since)
            lead_time = get_pr_lead_time(owner, name)
            results.append({
                "repo": repo,
                "deployment_frequency": deployment_freq,
                "lead_time_hours": lead_time
            })
        except Exception as e:
            print(f"❌ Error processing {repo}: {e}")

    os.makedirs("data", exist_ok=True)
    with open("data/metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    print("✅ Metrics collection complete. Results saved to data/metrics.json")

if __name__ == "__main__":
    main()
