import requests
from config import ACCESS_TOKEN

def fetch_repo_data(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"token {ACCESS_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code} - {response.text}")
        return None
    
if __name__ == '__main__':
    pass