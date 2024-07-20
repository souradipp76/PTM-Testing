import sqlalchemy
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from PeaTMOSS import *
from utils import *
import pandas as pd
import sys



def get_PTM_files_of_repo(repo_name):
    absolute_path = "D:\PeaTMOSS-Demos\PeaTMOSS_SAMPLE.db\PeaTMOSS_SAMPLE.db" #change this to an appropriate filepath for your directory
    engine = sqlalchemy.create_engine(f"sqlite:///{absolute_path}")

    with Session(engine) as session:
        ptm_repo_query = text(f"SELECT reuse_repository.url as repo_url, reuse_file.path as ptm_used_file_path , model.id as model_id , model.repo_url as model_url \
                              FROM reuse_file \
                              INNER JOIN model ON reuse_file.model_id=model.id \
                              INNER JOIN reuse_repository ON reuse_repository.id=reuse_file.reuse_repository_id \
                              WHERE reuse_repository.url='{repo_name}';")

        #creating a dataframe/csv
        models = session.execute(ptm_repo_query).all()
    print(f'Files in repo {repo_name} having PTMs are \n')    
    for model in models:
        print(f"{model.ptm_used_file_path} - {model.model_url}")




repo_name = sys.argv[1]
get_PTM_files_of_repo(repo_name)