import os

from utilities import execute_script, start_dataflow_job


def predict(project_id, template_path, input_table_id, limit, output_table_id, api_key):
    service_account = os.environ.get("SERVICE_ACCOUNT_BEAM")

    execute_script(project_id=project_id, sql_file_path="bigquery/bq_ddl.sql", verbose=True)

    start_dataflow_job(task_name="predictor-v1",
                       template_path=template_path,
                       input_table_id=input_table_id,
                       limit=limit,
                       output_table_id=output_table_id,
                       api_key=api_key,
                       service_account_name=service_account)


if __name__ == "__main__":
    _project_id = "ai-system-meigsy-gcp"
    os.environ["SERVICE_ACCOUNT_BEAM"] = "predictor-v1-beam"
    API_KEY = os.environ.get("OPENAI_API_KEY")

    predict(project_id=_project_id,
            template_path=f"gs://{_project_id}-dataflow/templates/predictor-v1-dataflow-template",
            input_table_id="predictor_v1_curated.v_unprocessed_inputs_v1",
            limit=10,
            output_table_id="predictor_v1_curated.output_v1",
            api_key=API_KEY)
