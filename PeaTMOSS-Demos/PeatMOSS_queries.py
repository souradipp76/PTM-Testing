import sqlalchemy
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from PeaTMOSS import *
from utils import *
import pandas as pd
def get_user_from_repo_url(repo_url):
    user = repo_url[repo_url.find("/")+1:repo_url.rfind("/")]
    return user

def get_reponame_from_repo_url(repo_url):
    reponame = repo_url[repo_url.rfind("/")+1:]
    return reponame

if __name__ == "__main__":

    ### When creating an absolute path string, make sure there is a leading forward slash (/)
    absolute_path = "D:\PeaTMOSS-Demos\PeaTMOSS_SAMPLE.db\PeaTMOSS_SAMPLE.db" #change this to an appropriate filepath for your directory
    engine = sqlalchemy.create_engine(f"sqlite:///{absolute_path}")
    # relati_path = "PeaTMOSS.db"
    # engine = sqlalchemy.create_engine(f"sqlite:///{relative_path}")

    highly_downloaded = {}
    reused_rates = {}
    with Session(engine) as session:
        # Query the 100 most downloaded models from the Model table
        #query_name_downloads = sqlalchemy.select(ReuseRepository.id, ReuseRepository.name, ReuseRepository.url, ReuseRepository.files).limit(10) # The Model class is declared in PeaTMOSS

        ptm_repo_query = text("SELECT reuse_repository.url as repo_url, reuse_file.path as ptm_used_file_path , model.id as model_id , model.repo_url as model_url  from reuse_file INNER JOIN model ON reuse_file.model_id=model.id INNER JOIN reuse_repository on reuse_repository.id=reuse_file.reuse_repository_id;")

        #creating a dataframe/csv
        models = session.execute(ptm_repo_query).all()
    all_repos = []
    repo_list = []
    for model in models:
        repo_url = model.repo_url
        if repo_url in repo_list:
            continue
        else:
            repo_list.append(repo_url)

        user_name = get_user_from_repo_url(repo_url)
        repo_name = get_reponame_from_repo_url(repo_url)
        repo_data = fetch_repo_data(user_name,repo_name)
        if repo_data:
            print("Succesfully fetched data for ",repo_name)
            repo_info = {"Repo URL":repo_url,
                        "Repo Stars": repo_data["stargazers_count"],
                        "Repo Forks": repo_data["forks_count"],
                        "Repo Watchers": repo_data["watchers_count"],
                        #"File with PTM": model.ptm_used_file_path,
                        "Model url": model.model_url}
        else:
            print("Cannot fetch data for ",repo_name)
            repo_info = {"Repo URL":repo_url,
                        "Repo Stars": None,
                        "Repo Forks": None,
                        "Repo Watchers": None,
                        #"File with PTM": model.ptm_used_file_path,
                        "Model url": model.model_url}

        all_repos.append(repo_info)
    
    df = pd.DataFrame(all_repos)
    df.to_csv("dataset_dumps/repo_info_data.csv")