import json
import subprocess, os
import fileinput
import pandas as pd
import shutil
import yaml
import sqlalchemy
import traceback

from sqlalchemy.sql import text
from sqlalchemy.orm import Session

# from github import Auth
# from github import Github
from git import Repo

import glob 
  
def iterate_nested_json_for_loop(json_obj, runs, env_vars, matrix):
    for key, value in json_obj.items():
        if isinstance(value, dict):
            if key == "env":
                env_dict = value
                for k,v in env_dict.items():
                    env_vars[k] = v
            elif key == "matrix":
                matrix_dict = value
                for k,v in matrix_dict.items():
                    matrix[k] = v
            else:
                iterate_nested_json_for_loop(value, runs, env_vars, matrix)
        elif isinstance(value, list):
            for val in value:
                if isinstance(val, dict):
                    iterate_nested_json_for_loop(val, runs, env_vars, matrix)
        elif key == "run":
            runs.append(value)    

def replace_text(filename, text_to_search, replacement_text):
    with fileinput.FileInput(filename, inplace=True, backup=".bak") as file:
        for line in file:
            if line.find("pip") == -1:
                print(line.replace(text_to_search, replacement_text), end='')

project_root = 'PTM-Testing/'
openai_api_key = os.environ["OPENAI_API_KEY"]

# github_token = os.environ["GITHUB_TOKEN"]
# auth = Auth.Token("{token}")
# g = Github(auth=auth)

# df = pd.read_csv("data/repo_with_workflow_v1_test.csv", header=0)
df = pd.read_excel("data/final_repo_list_for_analysis.xlsx", header=0)
secret_file = project_root+"gha.secrets"

e2e = 0
integration = 0
unit = 0

use_act = False

for index, row in df.iterrows():
    has_workflow = row['has_workflow_files']
    has_setup = row['has_setup']
    has_pyproject = row['has_pyproject']
    has_makefile = row['has_makefile']

    if not has_workflow:
        continue

    repo_name = "/".join(row["repo url"].split("/")[-2:])
    module_name = row["repo url"].split("/")[-1]
    git_url = "https://github.com/"+repo_name+".git"

    # try:
    #     repo = g.get_repo(repo_name)
    #     git_url = repo.clone_url
    # except:
    #     print("Repo not found")
    #     continue

    print(git_url)

    repo_dir = "sample-repos/" + repo_name

    if not os.path.isdir(repo_dir):
        Repo.clone_from(git_url, repo_dir)

    os.chdir(repo_dir)

    actions_file_list = glob.glob('.github/**/*.y*ml', recursive = True)
    actions_file_list = [x.replace(project_root+repo_dir+"/", "") for x in actions_file_list]
    # actions_file_list = [x[1:-1] for x in row["workflow_files_for_test"][1:-1].split(", ")]
    print(actions_file_list)

    file_pattern = ["dev", "test", "ci", "end", "e2e", "cov", "unit", "main", "build", "integration"]
    filtered_actions_file_list = list(filter(lambda x: any([y in x for y in file_pattern]), actions_file_list))
    print(filtered_actions_file_list)

    dst = project_root+'coverage-data/'+repo_name
    try:
        os.makedirs(dst)
    except OSError as error:
        print(error)

    for file in filtered_actions_file_list:

        if use_act:
            ######## Using act #######
            try:
                action_file = ".github/workflows/"+file
                replace_text(action_file, "3.8", "3.10.11")
                replace_text(action_file, "3.9", "3.10.11")
                replace_text(action_file, "ubuntu-latest", "macos-latest")
                replace_text(action_file, "pytest", "pytest --cov-report term --cov-report json --cov "+module_name)
                subprocess.run(["act", "-W", action_file, "-P", "macos-latest=-self-hosted","--secret-file", secret_file])
                os.chdir(os.path.join(project_root,repo_dir))
            except:
                print(f"Error running {action_file}")
                os.chdir(os.path.join(project_root,repo_dir))
                continue

        else:
            ######## Parsing GitHub Workflow files  #######
            if "end" in file or "e2e" in file:
                e2e+=1
            elif "integration" in file:
                integration+=1
            elif "unit" in file:
                unit+=1

            try:
                print(f"#### Action File: {file} ####\n")
                # action_file = ".github/workflows/"+file
                action_file = file
                # replace_text(action_file, "3.8", "3.10.11")
                # replace_text(action_file, "3.9", "3.10.11")
                replace_text(action_file, "ubuntu-latest", "macos-latest")

                with open(action_file) as f:
                    try:
                        data = yaml.safe_load(f)
                        print(data)
                    except yaml.YAMLError as exc:
                        print(exc)
                        continue
                
                run_commands = []
                env_vars = {}
                matrix = {}
                iterate_nested_json_for_loop(data, run_commands, env_vars, matrix)

                print(env_vars)
                print(matrix)
                print(os.getcwd())
                if len(run_commands) == 0:
                    os.chdir(os.path.join(project_root,repo_dir))
                    continue
                
                has_pip = False
                for i, command in enumerate(run_commands):
                    command = command.strip()
                    print(f"Got command: {command}\n")
                    try:
                        subcommands = command.split()
                        if "pip" in subcommands:
                            has_pip  = True
                        
                        if len(subcommands) == 0 or "black" in subcommands or "flake8" in subcommands or "isort" in subcommands:
                            continue
                        
                        if "pytest" in subcommands and not ("--cov" in subcommands) and not("pip" in subcommands):
                            command = command.replace("pytest", "pytest --cov-report=term --cov-report=json --cov=.")
                            # if not "coverage" in subcommands:
                            # command = command.replace("pytest", "coverage json -m pytest --cov-report=json")
                            # else:
                            #     command = command.replace("coverage run", "coverage json")
                        
                        if "--cov-report=html" in command:
                            command = command.replace("--cov-report=html", "--cov-report=json") 
                        
                        if ("pytest" in subcommands or "coverage" in subcommands) and not has_pip:
                            
                            # Install dependencies
                            try:
                                requirement_files = glob.glob('./**/requirements*.txt', recursive = True) 
                                print(requirement_files)
                                install_dependencies = ["pip", "install"]
                                for f in requirement_files:
                                    install_dependencies.append("-r")
                                    install_dependencies.append(f)
                                subprocess.run(install_dependencies)
                            except:
                                print("No requirements.txt")

                            # Run setup.py
                            if has_setup:
                                try:
                                    run_setup = ["python", "setup.py", "install"]
                                    subprocess.run(run_setup)
                                except:
                                    print("Unable to run setup")

                            # Run Makefile
                            if has_makefile:
                                try:
                                    subprocess.run(["make"])
                                except:
                                    print("No Makefile")
                    
                            # Run pip install
                            try:
                                install_module = ["pip", "install", "-e", "."]
                                subprocess.run(install_module)
                            except:
                                print("Unable to install module using pip")

                        for var,val in env_vars.items():
                            if val == "${{ secrets.OPENAI_API_KEY }}" or val == "${{secrets.OPENAI_API_KEY}}":
                                val = openai_api_key
                            # if val == "${{ secrets.HUGGINGFACE }}" or val == "${{secrets.OPENAI_API_KEY}}":
                            #     val = openai_api_key
                            # if val == "${{ secrets.GITHUB_TOKEN }}" or val == "${{secrets.GITHUB_TOKEN}}":
                            #     val = github_token
                            # if val == "${{ github.repository }}" or val == "${{github.repository}}":
                            #     val = repo_name
                            if isinstance(val,list):
                                val = val[0]
                            command = command.replace("$"+var, str(val))
                            command = command.replace("${"+var+"}", str(val))
                            command = command.replace("${{"+var+"}}", str(val))
                            command = command.replace("${{ "+var+" }}", str(val))
                            command = command.replace("${{ env."+var+" }}", str(val))
                            command = command.replace("${{env."+var+"}}", str(val))

                            command = command.replace("${{ secrets.OPENAI_API_KEY }}", openai_api_key)
                            command = command.replace("${{secrets.OPENAI_API_KEY}}", openai_api_key)
                            command = command.replace("${{ secrets.OPENAI_API_KEY }}", openai_api_key)
                            command = command.replace("${{secrets.OPENAI_API_KEY}}", openai_api_key)
                            command = command.replace("${{ runner.os }}", "macos-latest")
                            command = command.replace("${{ matrix.os }}", "macos-latest")
                            command = command.replace("${{ matrix.python-version }}", "3.9")

                        for var,val in matrix.items():
                            if var.startswith("os"):
                                val = "macos-latest"
                            elif isinstance(val,list):
                                if var.startswith("working-directory"):
                                    import sys
                                    for v in val:
                                        sys.path.append(os.path.join(project_root+repo_dir,v))
                                val = val[0]
                            command = command.replace("${{ matrix."+var+" }}", str(val))
                            command = command.replace("${{matrix."+var+"}}", str(val))

                        print(f"Running command: {command}")
                        subprocess.call(command, shell=True)
                    except:
                        print(f"Unable to run command: {command}")
                        print(traceback.print_exc())
                os.chdir(os.path.join(project_root,repo_dir))
            except:
                print(f"Error running {action_file}")
                print(traceback.print_exc())
                os.chdir(os.path.join(project_root,repo_dir))
                continue
        
        coverage_files = glob.glob(os.path.join(project_root,repo_dir)+'/**/coverage.json', recursive = True)
        print(coverage_files)
        for file in coverage_files:
            dst_file_name = file.replace(os.path.join(project_root,repo_dir)+"/", "").replace("/", "-")
            print(dst_file_name)
            shutil.copy(file, dst+ "/"+dst_file_name)  
            
        os.chdir(project_root)
        # shutil.rmtree(repo_dir)

def get_PTM_files_of_repo(repo_url):
    absolute_path = "PeaTMOSS_SAMPLE.db" #change this to an appropriate filepath for your directory
    engine = sqlalchemy.create_engine(f"sqlite:///{absolute_path}")

    with Session(engine) as session:
        ptm_repo_query = text(f"SELECT reuse_repository.url as repo_url, reuse_file.path as ptm_used_file_path , model.id as model_id , model.repo_url as model_url \
                              FROM reuse_file \
                              INNER JOIN model ON reuse_file.model_id=model.id \
                              INNER JOIN reuse_repository ON reuse_repository.id=reuse_file.reuse_repository_id \
                              WHERE reuse_repository.url='{repo_url}';")

        #creating a dataframe/csv
        models = session.execute(ptm_repo_query).all()
    #print(f'Files in repo {repo_name} having PTMs are \n')
    reuse_files = []
    for model in models:
        #print(f"{model.ptm_used_file_path} - {model.model_url}")
        reuse_files.append(model.ptm_used_file_path)
    return reuse_files

alldata = []
for i,row in df.iterrows():
    github_repo = row["repo url"]
    repo_name = "/".join(github_repo.split("/")[-2:])
    
    print(f"\n Repo = {github_repo}")
    files = get_PTM_files_of_repo(github_repo)

    try:
        coverage_files = os.listdir(f"coverage-data/{repo_name}")
    except: 
        continue
        
    for file in files:
        file_name = "/".join(file.split("/")[2:])
        # file_name = file[find_nth(file,"/",2)+1:]
        coverage_percent = None
        for coverage_file in coverage_files:
            try:
                f = open(f"coverage-data/{repo_name}/{coverage_file}")
                coverage_data = json.load(f)
                if file_name in coverage_data['files']:
                    #print(coverage_data['files'][file_name]['summary']['percent_covered'])
                    coverage_percent = coverage_data['files'][file_name]['summary']['percent_covered']
                else:
                    coverage_percent = None
            except(FileNotFoundError):
                print(f"coverage-data/{repo_name}/{coverage_file} file not found")
                #continue

        row_dict = {"repo_url":github_repo,
                    "reuse_file":file_name,
                    "percent covered":coverage_percent}

        alldata.append(row_dict)

new_df = pd.DataFrame(alldata, index=None)
new_df.to_csv('results/out.csv', index=False)
print(unit, integration, e2e)
