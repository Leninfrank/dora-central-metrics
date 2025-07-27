import requests
import yaml
import json
from datetime import datetime

GITHUB_TOKEN = {secrets.PERSONAL_ACCESS_TOKEN}

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

def fetch_repos():
    with open("repos.yaml") as f:
        return yaml.safe_load(f)["repos"]

def get_deployments(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/deployments"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_commits(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_pull_requests(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=closed"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def calculate_dora_metrics(owner, repo):
    deployments = get_deployments(owner, repo)
    prs = get_pull_requests(owner, repo)

    deployment_frequency = len(deployments)
    lead_times = []

    for pr in prs:
        if pr.get("merged_at") and pr.get("created_at"):
            created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
            merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
            lead_times.append((merged - created).total_seconds())

    avg_lead_time = sum(lead_times) / len(lead_times) / 3600 if lead_times else 0

    return {
        "repo": f"{owner}/{repo}",
        "deployment_frequency": deployment_frequency,
        "lead_time_for_changes_hrs": round(avg_lead_time, 2),
    }

def main():
    results = []
    for repo in fetch_repos():
        metrics = calculate_dora_metrics(repo["owner"], repo["repo"])
        results.append(metrics)

    with open("dora_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
