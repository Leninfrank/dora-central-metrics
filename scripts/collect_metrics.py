import sys
import os
import json
from datetime import datetime, timezone
from github import Github

# GitHub Token must be stored in secrets or env
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN not set")
    sys.exit(1)

# Initialize GitHub client
gh = Github(GITHUB_TOKEN)

# Get target repo from command-line argument
if len(sys.argv) < 2:
    print("❌ Usage: python collect_metrics.py <org/repo>")
    sys.exit(1)

repo_name = sys.argv[1]
try:
    repo = gh.get_repo(repo_name)
except Exception as e:
    print(f"❌ Error accessing repo {repo_name}: {e}")
    sys.exit(1)

print(f"📦 Collecting DORA metrics for: {repo_name}")

# -- Deployment Frequency (number of deployments in last 7 days) --
deployments = repo.get_deployments()
deployment_count = 0
one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
for d in deployments:
    if d.created_at >= one_week_ago:
        deployment_count += 1

# -- Lead Time for Changes (avg time from PR created to merged) --
pulls = repo.get_pulls(state='closed')
lead_times = []
for pr in pulls:
    if pr.merged and pr.created_at and pr.merged_at:
        delta = pr.merged_at - pr.created_at
        lead_times.append(delta.total_seconds() / 3600)  # hours

avg_lead_time_hours = round(sum(lead_times) / len(lead_times), 2) if lead_times else 0

# -- Change Failure Rate (optional: assume 10% of deployments fail) --
# For a real implementation, check status of deployments or reverts
change_failure_rate = 0.1  # placeholder

# Save metrics
metrics = {
    "repository": repo_name,
    "deployment_frequency": deployment_count,
    "average_lead_time_hours": avg_lead_time_hours,
    "change_failure_rate": change_failure_rate,
    "timestamp_collected": datetime.now(timezone.utc).isoformat()
}

# Write to metrics/<repo>.json
os.makedirs("metrics", exist_ok=True)
out_file = f"metrics/{repo_name.replace('/', '__')}.json"
with open(out_file, "w") as f:
    json.dump(metrics, f, indent=2)

print(f"✅ Metrics written to {out_file}")
