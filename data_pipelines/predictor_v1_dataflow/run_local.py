# run_local.py

import argparse
import logging
import os
import sys

from main import run_pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", help="GCP project ID.", default="ai-system-meigsy-gcp")
    parser.add_argument("--region", help="GCP region.", default="us-central1")
    parser.add_argument("--runner", help="Beam runner type (e.g., DataflowRunner, DirectRunner).", default="DirectRunner")
    parser.add_argument("--temp_location", help="GCS temp location.", default="gs://predictor-v1-dataflow-773645421672/temp")
    parser.add_argument("--staging_location", help="GCS staging location.", default="gs://predictor-v1-dataflow-773645421672/staging")
    parser.add_argument("--input_table", help="Input BigQuery table.", required=True)
    parser.add_argument("--limit", help="Limit the number of input rows.", type=int, default=None)
    parser.add_argument("--output_table", help="Output BigQuery table.", default="predictor_v1_curated.output_v1")
    parser.add_argument("--api_key", help="OpenAI API Key.", required=True)

    known_args, pipeline_args = parser.parse_known_args()

    logging.basicConfig(level=logging.INFO)
    logging.info("Starting the pipeline...")

    run_pipeline(
        project_id=known_args.project,
        input_table=known_args.input_table,
        limit=known_args.limit,
        output_table=known_args.output_table,
        api_key=known_args.api_key,  # Pass the API key to the pipeline
        options=pipeline_args + [
            f'--project={known_args.project}',
            f'--region={known_args.region}',
            f'--runner={known_args.runner}',
            f'--temp_location={known_args.temp_location}',
            f'--staging_location={known_args.staging_location}'
        ]
    )


if __name__ == '__main__':
    API_KEY = os.environ.get("OPENAI_API_KEY")

    sys.argv.extend([
        "--input_table=predictor_v1_curated.v_unprocessed_inputs_v1",
        "--limit=1",
        "--output_table=predictor_v1_curated.output_v1",
        f"--api_key={API_KEY}"
    ])
    main()
