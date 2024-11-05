from datetime import datetime

from utilities import execute_query


def table_snapshot(project_id, expiration_days):
    today = datetime.utcnow().strftime('%Y%m%d%H%M')

    # There are sdk/client options for doing this stuff, but it's more convenient in pure bigquery SQL.
    # When things go wrong I can grab the verbatim query and drop it into the bigquery console to start debugging.
    query = f"""
    CREATE SNAPSHOT TABLE predictor_v1_backup.output_v1_{today}
    CLONE predictor_v1_curated.output_v1
    """

    if expiration_days:
        query += f"""OPTIONS(expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL {expiration_days} DAY));"""

    execute_query(project_id, query, verbose=True)


if __name__ == "__main__":
    # Executing from here is just for local testing. So if I set the expiration to one day
    # I can debug as much as I want without needing to worry about cleaning up. It'll all disappear in a day.

    _project_id = "ai-system-meigsy-gcp"
    table_snapshot(project_id=_project_id, expiration_days=1)
