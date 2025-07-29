from airflow import DAG
# from airflow.operators.bash import BashOperator
from datetime import datetime,timedelta
import pandas as pd
# Removed unresolved import for S3 operators
from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.decorators import task



#lets define the S3 path to the CSV file
#make sure you have the right permissions to access this file
s3_path = 's3://imani-airflow-data/raw/QVI_transaction_data.csv'


#create a function to read the CSV file from S3 and also provide the necessary credentials to connect to aws and s3.
@task
def extract(**kwargs):
    s3_hook = S3Hook(aws_conn_id='aws-connect')
    aws_hook = AwsBaseHook(aws_conn_id='aws-connect', client_type='s3')

    # Get credentials and region from the AWS hook as i already have the aws connection set up in airflow
    # Make sure you have the AWS connection set up in Airflow with the ID 'aws-connect' (one might have a different ID)
    credentials = aws_hook.get_credentials()
    region_name = "us-east-1"
    global storage_options
    storage_options = {
        "key": credentials.access_key,
        "secret": credentials.secret_key,
        "token": credentials.token,
        "client_kwargs": {"region_name": region_name}
    }
    df = pd.read_csv(s3_path, storage_options=storage_options)
    
    file_path = "/tmp/mymani.csv"
    df.to_csv(file_path, index=False)
    return file_path

@task
def transform(file_path):
    df=pd.read_csv(file_path)
    df['DATE']=pd.to_datetime(df['DATE'],origin = "1899-12-30", unit='D')
    df= df.dropna()
    df= df[~df['PROD_NAME'].str.lower().str.contains('salsa', na=False)]

    outliers = df[df['PROD_QTY'] >20]
    df=df[~df['LYLTY_CARD_NBR'].isin(outliers['LYLTY_CARD_NBR'])]
    df=df.drop_duplicates()

    global file_path_s3
    file_path_s3 = "/tmp/transformed.csv"
    df.to_csv(file_path_s3, index=False)

    return file_path_s3

@task
def data_quality_check(file_path_s3: str):
    df = pd.read_csv(file_path_s3)
    if df.empty:
        raise ValueError("DataFrame is empty after transformation.")
        return False
    if df.isnull().any().any():
        raise ValueError("Data quality check failed: Null values found in the dataset")
        return False
    if df.duplicated().any():
        raise ValueError("Data quality check failed: Duplicate rows found in the dataset")
        return False
    return {    "is_valid": True,
                "file_path": file_path_s3 
            }

@task.branch
def decide_path(check: bool):
    if check['is_valid']:
        return 'file_location'
    else:
        return 'data_quality_check_failed'

@task
def data_quality_check_failed():
    raise ValueError("Data quality check failed. No further processing will be done.")


@task
def upload_to_s3(file_path_s3, bucket_name: str, s3_folder: str, filename: str, ti=None):
    s3_hook = S3Hook(aws_conn_id='aws-connect')
    key = f"{s3_folder}/{filename}"  # e.g. "folder1/myfile.csv" or "folder2/myfile.csv"
    s3_hook.load_file(filename=file_path_s3, key=key, bucket_name=bucket_name, replace=True)
    return f"s3://{bucket_name}/{key}"


    

@task
def file_location(ti=None):
    check = ti.xcom_pull(task_ids='data_quality_check')
    file_path_s3 = check.get("file_path")
    if not file_path_s3:
        raise ValueError("No transformed file path available.")
    return file_path_s3




# Define the default arguments for the DAG


default_args={
        'owner': 'airflow',
        'retries': 1,
        'retry_delay': timedelta(minutes=1)
    }

with DAG(
    #here we define the DAG ID and other parameters where dag id is the one we see in the Airflow UI as the name of the DAG
    dag_id='trans_dag_26',
    start_date=datetime(2023, 10, 1),
    schedule_interval='@daily',
    default_args=default_args,  
    
) as dag:
    

    raw              = extract()
    transformed      = transform(raw)
    check            = data_quality_check(transformed)
    branch           = decide_path(check)          # returns "file_location" or "data_quality_check_failed"

    file_loc         = file_location()        # <-- CALL the task here!
    failed           = data_quality_check_failed()
    upload           = upload_to_s3(
                         file_loc,                  # <-- pass the XComArg from file_location()
                         bucket_name='imani-airflow-data',
                         s3_folder='transformed',
                         filename='transformed.csv',
                       )
    

    raw >> transformed >> check >> branch
    branch >> [file_loc, failed]
    file_loc >> upload
    

