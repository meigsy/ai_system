import os

from flask import Flask, jsonify, request

from bigquery_gcs_backup import gcs_backup
from bigquery_table_snapshot import table_snapshot
from prediction_logic import predict
from tag import TAG

app = Flask(__name__)

GCP_PROJECT = os.getenv("GCP_PROJECT")
TEMPLATE_PATH = f"gs://{GCP_PROJECT}-dataflow/templates/predictor-v1-dataflow-template"
API_KEY = os.environ.get("OPENAI_API_KEY")


@app.route('/predict', methods=['POST'])
def prediction_endpoint():
    try:
        data = request.get_json()

        limit = data.get('limit', None)
        if not limit:
            raise ValueError("limit is required.")

        predict(project_id=GCP_PROJECT,
                template_path=TEMPLATE_PATH,
                input_table_id="predictor_v1_curated.v_unprocessed_inputs_v1",
                limit=limit,
                output_table_id="predictor_v1_curated.output_v1",
                api_key=API_KEY)

        return jsonify({"message": f"{TAG} job triggered. limit: {limit}"}), 200
    except Exception as e:
        app.logger.error(f"{TAG} Error during job: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/table_snapshot', methods=['POST'])
def table_snapshot_endpoint():
    try:
        data = request.get_json()
        expiration_days = data.get('expiration_days', 30)

        table_snapshot(project_id=GCP_PROJECT, expiration_days=expiration_days)

        return jsonify({"message": f"{TAG} table snapshot triggered."}), 200
    except Exception as e:
        app.logger.error(f"{TAG} Error during table snapshot job: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/gcs_backup', methods=['POST'])
def gcs_backup_endpoint():
    try:
        gcs_backup(project_id=GCP_PROJECT, dataset_id="predictor_v1_curated", table_id="output_v1")

        return jsonify({"message": f"{TAG} GCS backup triggered."}), 200
    except Exception as e:
        app.logger.error(f"{TAG} Error during GCS backup job: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
