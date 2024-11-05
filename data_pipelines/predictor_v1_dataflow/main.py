import argparse

import apache_beam as beam
from apache_beam.io.gcp.bigquery import ReadFromBigQuery, WriteToBigQuery
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions


class GetPrediction(beam.DoFn):
    def __init__(self, api_key):
        self.api_key = api_key

    def process(self, element, *args, **kwargs):
        import logging
        import time
        from datetime import datetime
        import base64
        import json
        from langchain_openai import ChatOpenAI
        from langchain_community.callbacks.manager import get_openai_callback
        from model_output_schema import schema
        from example_data import example_1, example_2
        from tag import TAG

        logging.info(f"{TAG} Processing element from foo: {element['foo']}, inserted_at: {element['inserted_at']}")

        MODEL_ID = "gpt-4o-mini"
        LLM = ChatOpenAI(openai_api_key=self.api_key, model=MODEL_ID, temperature=0)

        static_prompt_prefix = f"""You are a helpful influgerator. A user will give you a foo and ask you how many bars are in it. ONLY RETURN JSON, DO NOT WRITE CODE. IF THERE'S NO BARs RETURN NULL. The output should only 
                             contain one valid JSON object that follows this schema.

                             SCHEMA: 
                             {schema}

                             Example of a good input and output:

                             EXAMPLE FOO:
                             {example_1[('foo')]}

                             EXAMPLE OUTPUT: 
                             {example_1['bar']}

                             Example of edge case data I want to make you aware of:

                             EXAMPLE FOO:
                             {example_2['foo']}

                             EXAMPLE OUTPUT:
                             {example_2['bar']}

                             ACTUAL FOO:

                             """

        static_prompt_postfix = f"""

                             OUTPUT: 

                             """

        # Ensure prompt fits within token limit
        static_prompt_length = len(static_prompt_prefix) + len(static_prompt_postfix)

        char_limit = 512000  # Adjusted for token limits. I could use the tokenizer to get exact numbers here but good enough is....good enough for now.
        available_length_for_actual_foo = char_limit - static_prompt_length
        actual_foo = element['foo']

        if len(actual_foo) > available_length_for_actual_foo:
            logging.info(f"{TAG} Text exceeds {available_length_for_actual_foo} characters. Truncating.")
            actual_foo = actual_foo[:available_length_for_actual_foo]

        prompt = f"{static_prompt_prefix}{actual_foo}{static_prompt_postfix}"

        prediction_time = datetime.utcnow().isoformat()
        start_time = time.time()

        # Initialize base response
        base_response = {
            "input": {
                "foo": element["foo"],
                "inserted_at": element["inserted_at"],
            },
            "prediction": {
                "text": None,
                "model": MODEL_ID,
                "response_object": None,
            },
            "response_code": None,
            "error_message": None,
            "prediction_time": prediction_time,
            "prediction_duration_seconds": None
        }

        try:
            with get_openai_callback() as openai_callback:  # there's some useful info in here I'm not using in this example
                response = LLM.invoke(prompt)
            end_time = time.time()
            inference_duration_seconds = end_time - start_time

            encoded_prediction = base64.b64encode(response.content.encode('utf-8')).decode('utf-8')

            response_dict = response.dict()
            encoded_response = base64.b64encode(json.dumps(response_dict).encode('utf-8')).decode('utf-8')

            base_response.update({
                "prediction": {
                    "text": encoded_prediction,
                    "model": MODEL_ID,
                    "response_object": encoded_response,
                },
                "response_code": 200,
                "prediction_duration_seconds": inference_duration_seconds
            })

            yield base_response

        except Exception as e:
            import traceback

            end_time = time.time()
            stack_trace = traceback.format_exc()

            logging.error(f"{TAG} Exception: unexpected error during prediction for foo: {element['foo']}. Error: {e}. Stack Trace: {stack_trace}")

            inference_duration_seconds = end_time - start_time

            error_details = f"Error: {e}\nStack Trace: {stack_trace}"
            encoded_error = base64.b64encode(error_details.encode('utf-8')).decode('utf-8')

            base_response.update({
                "response_code": 500,
                "error_message": encoded_error,
                "prediction_duration_seconds": inference_duration_seconds
            })

            yield base_response


def run_pipeline(project_id, input_table, limit, output_table, api_key, options=None):
    from output_schema import prediction_record_schema
    import logging
    from tag import TAG

    logging.getLogger().setLevel(logging.INFO)
    logging.info(f"{TAG} Starting pipeline for project: {project_id}")

    pipeline_options = PipelineOptions(options)
    pipeline_options.view_as(SetupOptions).save_main_session = True

    input_query = f"""
        SELECT foo, 
               inserted_at
        FROM {input_table}
    """

    if limit:
        input_query += f" LIMIT {limit}"

    with beam.Pipeline(options=pipeline_options) as pipeline:
        (
                pipeline
                | 'Read from BigQuery' >> ReadFromBigQuery(query=input_query, use_standard_sql=True)
                | 'Make Predictions' >> beam.ParDo(GetPrediction(api_key=api_key))
                | 'Write to BigQuery' >> WriteToBigQuery(
            table=output_table,
            schema=prediction_record_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
        )
        )


if __name__ == '__main__':
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("--project", help="GCP project ID.", default="ai-system-meigsy-gcp")
    parser.add_argument("--region", help="GCP region.", default="us-central1")
    parser.add_argument("--runner", help="Beam runner type (e.g., DataflowRunner, DirectRunner).", default="DirectRunner")
    parser.add_argument("--temp_location", help="GCS temp location.", required=True)
    parser.add_argument("--staging_location", help="GCS staging location.", required=True)
    parser.add_argument("--input_table", help="Input BigQuery table.", required=True)
    parser.add_argument("--limit", help="Limit the number of input rows.", type=int, default=None)
    parser.add_argument("--output_table", help="Output BigQuery table.", required=True)
    parser.add_argument("--api_key", help="OpenAI API Key.", required=True)  # Added API key argument

    known_args, pipeline_args = parser.parse_known_args()

    logging.basicConfig(level=logging.INFO)
    logging.info(f"Launching pipeline...")

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
