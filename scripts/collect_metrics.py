import requests, json, os
from datetime import datetime, timedelta

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
BASE_URL = "https://api.github.com"

def get_commit_count(owner, repo, since):
    url = f"{BASE_URL}/repos/{owner}/{repo}/commits?since={since}"
    res = requests.get(url, headers=HEADERS)
    return len(res.json())

def get_pr_lead_time(owner, repo):
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls?state=closed"
    res = requests.get(url, headers=HEADERS)
    times = []
    for pr in res.json():
        if pr.get("merged_at"):
            created = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            merged = datetime.strptime(pr["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
            times.append((merged - created).total_seconds())
    return sum(times) / len(times) / 3600 if times else 0

def main():
    repos = open("repos.txt").read().splitlines()
    since = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    results = []

    for repo in repos:
        owner, name = repo.split("/")
        result = {
            "repo": repo,
            "deployment_frequency": get_commit_count(owner, name, since),
            "lead_time_hours": round(get_pr_lead_time(owner, name), 2),
        }
        results.append(result)

    with open("data/metrics.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
