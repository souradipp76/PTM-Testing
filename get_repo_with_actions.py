import sqlalchemy
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from PeaTMOSS import *
from utils import *
import pandas as pd
import sys
from config import ACCESS_TOKEN
from github import Github
import time
import datetime
# Authentication is defined via github.Auth
from github import Auth
import os

# using an access token
auth = Auth.Token(ACCESS_TOKEN)

# Public Web Github
g = Github(auth=auth)

start = time.time()
if __name__ == "__main__":
    absolute_path = "D:\PeaTMOSS-Demos\PeaTMOSS_SAMPLE.db\PeaTMOSS_SAMPLE.db" #change this to an appropriate filepath for your directory
    engine = sqlalchemy.create_engine(f"sqlite:///{absolute_path}")

    highly_downloaded = {}
    reused_rates = {}
    with Session(engine) as session:
        ptm_repo_query = text("SELECT url as repo_url from reuse_repository")
        models = session.execute(ptm_repo_query).all()
    all_repos = []
    list_attributes = []
    count_repos = 0
    for model in models:
        repo_url = model.repo_url 
        print(f"processing for {repo_url[repo_url.find('/')+1:]}")
        try:
            repo = g.get_repo(repo_url[repo_url.find('/')+1:])
        except:
            print(f"{repo_url} not found !!")
            continue
        try:
            workflow_files = repo.get_contents(".github/workflows")
            has_workflow_files = True
        except:
            workflow_files = None
            has_workflow_files = False
        repo_root_files = repo.get_contents("")
        repo_root_files_str = [file.name for file in repo_root_files]

        if "pyproject.toml" in repo_root_files_str:
            has_pyproject = True
        else:
            has_pyproject = False
        
        if "setup.py" in repo_root_files_str:
            has_setup = True
        else:
            has_setup = False
        # what to do about its case
        
        if "Makefile" in repo_root_files_str:
            has_makefile = True
        else:
            has_makefile = False
        
        if "Dockerfile" in repo_root_files_str:
            has_dockerfile = True
        else:
            has_dockerfile = False

        if "pytest.ini" in repo_root_files_str:
            has_dockerfile = True
        else:
            has_dockerfile = False
        

        total_num_of_workflow_files=0
        num_workflow_files_for_test = 0
        workflow_files_for_test = []
        if workflow_files:
            total_num_of_workflow_files = len(workflow_files)
            #workflow_files_str = [file.name for file in workflow_files]
            for file in workflow_files:
                try:
                    file_content = file.decoded_content.decode()                    #count_api_hits+=1
                    if 'test' in file_content:
                        workflow_files_for_test.append(file.name)
                        num_workflow_files_for_test+=1
                except:
                    print(f"file content for {file.name} cannot be decoded in {repo_url}")            
        
        list_contributors = repo.get_contributors()
        #make dict for pandas df
        list_attributes.append({"repo url":repo_url,
                                "stars":repo.stargazers_count,
                                "num contributors":list_contributors.totalCount,
                                "has_workflow_files":has_workflow_files,
                                "num_workflow_files":total_num_of_workflow_files,
                                "num_test_workflow_files":num_workflow_files_for_test,
                                "workflow_files_for_test":workflow_files_for_test,
                                "has_pyproject":has_pyproject,
                                "has_setup":has_setup,
                                "has_makefile":has_makefile,
                                "has_dockerfile":has_dockerfile})
        count_repos+=1
        if count_repos%100==0:
            df = pd.DataFrame(list_attributes)
            print(f"Writing {len(list_attributes)} repos to csv.")
            filename = "gitRepo_with_actions.csv"
            if not os.path.isfile(filename):
                df.to_csv(filename, header='column_names', index=False)
            else:  # else it exists so append without writing the header
                df.to_csv(filename, mode='a', header=False, index=False)
            list_attributes = []

        if g.get_rate_limit().core.remaining<10:
            print(f"Ratelimit = {g.get_rate_limit()}")
            resettime = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
            print(f"Process will continue at {resettime}")
            delta = resettime - datetime.datetime.now()
            time.sleep(delta.seconds+50)

print(f"Script running time = {round((time.time() - start )/60, 3)} mins")