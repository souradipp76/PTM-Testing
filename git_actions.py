import subprocess, sys

from github import Auth
from github import Github

from git import Repo

auth = Auth.Token("")
g = Github(auth=auth)

repo = g.get_repo("deepset-ai/haystack")
print(repo.get_topics())
git_url = repo.clone_url;
print(git_url)
# contents = repo.get_contents("")
# for content_file in contents:
#     print(content_file)
#     print(content_file.download_url)


repo_dir = "sample-repos\\haystack"
# Repo.clone_from(git_url, repo_dir)

subprocess.run(["act", "-W", "sample-repos\\haystack\\.github\\workflows\\e2e.yml"])