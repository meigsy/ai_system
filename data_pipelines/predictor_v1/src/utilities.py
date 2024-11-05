import os
from datetime import datetime

import google.auth
from google.cloud import bigquery
from googleapiclient.discovery import build

from tag import TAG


def execute_script(project_id, sql_file_path, verbose=True):
    # Ensure the sql_file_path is an absolute path
    if not os.path.isabs(sql_file_path):
        # Assuming the script is located in the src directory, adjust the path accordingly
        base_path = os.path.dirname(__file__)
        sql_file_path = os.path.join(base_path, sql_file_path)

    # Normalize the path
    sql_file_path = os.path.abspath(sql_file_path)

    print(f"{TAG} query: start. file: {sql_file_path}")

    try:
        with open(sql_file_path, 'r') as file_stream:
            sql_text = file_stream.read()
            execute_query(project_id, sql_text, verbose)
    except FileNotFoundError:
        print(f"Error: The file {sql_file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    print(f"{TAG} query: complete. file: {sql_file_path}")


def execute_query(project_id, query_text, verbose=True):
    if verbose:
        print(f"{TAG} query_text: \n{query_text}")

    with bigquery.Client(project=project_id) as client:
        query_job = client.query(query_text)
        return query_job.result()  # Waits for job to complete.


def start_dataflow_job(task_name,
                       template_path,
                       input_table_id,
                       limit,
                       output_table_id,
                       api_key,
                       service_account_name):
    credentials, project_id = google.auth.default()  # TODO: get credentials for an explicit project so you can't mess up by having the wrong one set locally -Sly 11/4/2024
    region = "us-central1"
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    job_name = f"{task_name}-{limit}-{timestamp}"

    # NOTE: The dataflow template automatically deploys in the same project this is getting called from
    dataflow = build("dataflow", "v1b3", credentials=credentials)

    request = dataflow.projects().locations().flexTemplates().launch(
        projectId=project_id,
        location=region,
        body={
            "launchParameter": {
                "jobName": job_name,
                "containerSpecGcsPath": template_path,
                "parameters": {
                    "project": project_id,
                    "region": region,
                    "input_table": input_table_id,
                    "limit": str(limit),
                    "output_table": output_table_id,
                    "api_key": api_key
                },
                "environment": {
                    "tempLocation": f"gs://{project_id}-dataflow/temp",
                    "subnetwork": "regions/us-central1/subnetworks/default",
                    "maxWorkers": 300,
                    "network": "default",
                    "serviceAccountEmail": f"{service_account_name}@{project_id}.iam.gserviceaccount.com"
                }
            }
        }
    )

    response = request.execute()
    print(f"Dataflow job started: {response}")
