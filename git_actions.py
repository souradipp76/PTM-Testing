import subprocess, sys, os
import docker

from github import Auth
from github import Github

from git import Repo

auth = Auth.Token("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")
g = Github(auth=auth)

repo = g.get_repo("deepset-ai/haystack")
print(repo.get_topics())
git_url = repo.clone_url;
print(git_url)
# contents = repo.get_contents("")
# for content_file in contents:
#     print(content_file)
#     print(content_file.download_url)

secret_file = "../../gha.secrets"
repo_dir = "sample-repos/haystack"
os.chdir(repo_dir)

# Repo.clone_from(git_url, repo_dir)

# subprocess.run(["act", "workflow_dispatch", "-W", ".github/workflows/e2e.yml", "-P", "macos-latest=-self-hosted", "--secret-file", "../../gha.secrets"])
subprocess.run(["act", "workflow_dispatch", "-W", ".github/workflows/e2e.yml", "--container-architecture", "linux/amd64", "--secret-file", "../../gha.secrets"])
# subprocess.run(["python", "-m", "piptools", "compile", "-o", "requirements.txt", "pyproject.toml"])
# subprocess.run(["python", "-m", "pip", "install", "-r", "requirements.txt"])
# subprocess.run(["python", "-m", "pip", "install", ".[extra-dependencies]"])
# subprocess.run("tox")

# client = docker.client.from_env()

# def checkDockerContainerStatus( container):
#     client = docker.from_env()
#     #cli = docker.APIClient()
#     if client.containers.list(filters={'name': container}):
#         response = client.containers.list(filters={'name': container})
#         return str(response[0].id)[:12]
#     else:
#         return None

# CONTAINER_ID = checkDockerContainerStatus('node')

# if CONTAINER_ID is not None:
#     print(f"Found! {CONTAINER_ID}")
#     container = client.containers.get(CONTAINER_ID)
#     exit_code, output = container.exec_run("python your_script.py script_args")
# else:
#     print("Container node is not found")


os.chdir('../..')