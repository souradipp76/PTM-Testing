import subprocess, sys, os
import docker

# from github import Auth
# from github import Github

# from git import Repo

# auth = Auth.Token("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")
# g = Github(auth=auth)

# repo = g.get_repo("deepset-ai/haystack")
# print(repo.get_topics())
# git_url = repo.clone_url;
# print(git_url)
# # contents = repo.get_contents("")
# # for content_file in contents:
# #     print(content_file)
# #     print(content_file.download_url)

# Initialize Docker client
client = docker.from_env()

# Define the Dockerfile content
dockerfile_content = '''
FROM ubuntu:latest

ARG GITHUB_URL

# Install dependencies
RUN apt-get update && \\
    apt-get install -y git python3 python3-pip && \\
    pip3 install pytest && \\
    apt-get clean && \\
    rm -rf /var/lib/apt/lists/*

# Clone and setup repository
RUN git clone $GITHUB_URL ptm_repo && \\
    cd ptm_repo && \\
    pip3 install -e . \\

CMD ["pytest", "ptm_repo/"]
'''

# Create a temporary Dockerfile
dockerfile_path = './Dockerfile'
with open(dockerfile_path, 'w') as f:
    f.write(dockerfile_content)

# Build the Docker image
image, build_logs = client.images.build(
    path='.',
    dockerfile=dockerfile_path,
    tag='test-env'
)

print(build_logs)

# Define a function to run pytest inside the Docker container, save results to a file, and clean up the container
def run_pytest_and_save_results(container, output_file):
    try:
        # Fetch the container logs to get pytest results
        logs = container.logs().decode('utf-8')
        
        # Save pytest results to a text file
        with open(output_file, 'w') as f:
            f.write(logs)
        
        print(f'pytest results saved to {output_file}')
        
    except docker.errors.ContainerError as e:
        print(f'pytest execution failed: {e}')
        
    finally:
        # Stop and remove the Docker container
        container.stop()
        container.remove()

# Run the Docker container and execute 'pytest'
try:
    container = client.containers.run(
        image='test-env',
        detach=True,
        tty=True
    )
    
    # Save pytest logs to a text file
    output_file = 'pytest_logs.txt'
    run_pytest_and_save_results(container, output_file)
    
finally:
    # Remove the temporary Dockerfile
    os.remove(dockerfile_path)
