
import requests
from config import ACCESS_TOKEN
def fetch_repo_data(owner, repo, token):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code} - {response.text}")
        return None
    
def fetch_num_contributors(owner, repo, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code} - {response.text}")
        return None

# Replace these values with your GitHub username, repository name, and personal access token
owner = "ultralytics"
repo = "yolov5"

contributor_data = fetch_num_contributors(owner, repo, ACCESS_TOKEN)
if contributor_data:
    print(contributor_data)
"""repo_data = fetch_repo_data(owner, repo, access_token)
if repo_data:
    print("Repository Name:", repo_data["full_name"])
    print("Description:", repo_data["description"])
    print("URL:", repo_data["html_url"])
    print("Stars:", repo_data["stargazers_count"])
    print("Forks:", repo_data["forks_count"])
    print("Watchers:", repo_data["watchers_count"])

print (repo_data)"""