import os
import time
from datetime import datetime, timezone

from google.cloud import storage, bigquery


def gcs_backup(project_id, dataset_id, table_id):
    """
    Export a BigQuery table to a temporary (unlocked) Google Cloud Storage bucket,
    then move the exported files to a locked backup bucket for retention.
    AVRO or PARQUET are binary formats that contain the schema in the file as well which
    is convenient for storing and processing data
    """
    temp_bucket_name = os.getenv("PIPELINE_BUCKET_NAME")
    backup_bucket_name = os.getenv("BACKUP_BUCKET_NAME")
    storage_client = storage.Client()
    bq_client = bigquery.Client(project=project_id)

    now = datetime.now(timezone.utc)
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')
    timestamp = now.strftime('%H%M%S')

    temp_uri = f"gs://{temp_bucket_name}/{dataset_id}/{table_id}/{year}/{month}/{day}/{timestamp}/{table_id}_*.avro"
    # There are sdk/client options for doing this stuff, but it's more convenient in pure bigquery SQL.
    # When things go wrong I can grab the verbatim query and drop it into the bigquery console to start debugging.
    query = f"""EXPORT DATA
                  OPTIONS(
                    uri='{temp_uri}',
                    format='AVRO'
                  )
                AS
                SELECT * FROM {dataset_id}.{table_id};"""

    # Start the export query
    print(f"query: {query}")
    query_job = bq_client.query(query)

    # Polling until the job is done
    print("Waiting for BigQuery export to complete...")
    while not query_job.done():
        time.sleep(5)  # Wait for 5 seconds before checking the status again

    # Check for errors in the export job
    if query_job.errors:
        print("Export job failed with errors:", query_job.errors)
        return
    else:
        print("Export completed successfully.")

    # Define paths for copying and moving files
    temp_path_prefix = f"{dataset_id}/{table_id}/{year}/{month}/{day}/{timestamp}/"
    backup_path_prefix = temp_path_prefix

    print(f"Copying files from {temp_bucket_name}/{temp_path_prefix} to {backup_bucket_name}/{backup_path_prefix}")

    temp_bucket = storage_client.bucket(temp_bucket_name)
    backup_bucket = storage_client.bucket(backup_bucket_name)

    # Copy each file from the temporary bucket to the backup bucket
    blobs = temp_bucket.list_blobs(prefix=temp_path_prefix)
    for blob in blobs:
        new_blob = backup_bucket.blob(f"{backup_path_prefix}{blob.name.split('/')[-1]}")
        new_blob.rewrite(blob)
        print(f"Copied {blob.name} to {backup_bucket_name}/{new_blob.name}")

    # Delete files from the temporary bucket
    for blob in temp_bucket.list_blobs(prefix=temp_path_prefix):
        blob.delete()
        print(f"Deleted {blob.name} from {temp_bucket_name}")

    print(f"Backup completed successfully in {backup_bucket_name}/{backup_path_prefix}")


if __name__ == "__main__":
    _project_id = "ai-system-meigsy-gcp"
    _pipline_bucket = "predictor-v1-jobs-773645421672"
    os.environ["PIPELINE_BUCKET_NAME"] = _pipline_bucket
    os.environ["BACKUP_BUCKET_NAME"] = f"backup-{_pipline_bucket}"

    gcs_backup(project_id=_project_id, dataset_id="predictor_v1_curated", table_id="output_v1")
