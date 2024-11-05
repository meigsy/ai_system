prediction_record_schema = {
    "fields": [
        {
            "name": "input",
            "type": "RECORD",
            "fields": [
                {
                    "name": "foo",
                    "type": "STRING",
                    "mode": "REQUIRED"
                },
                {
                    "name": "inserted_at",
                    "type": "TIMESTAMP",
                    "mode": "REQUIRED"
                }
            ]
        },
        {
            "name": "prediction",
            "type": "RECORD",
            "mode": "NULLABLE",
            "fields": [
                {
                    "name": "text",
                    "type": "STRING",
                    "mode": "NULLABLE"
                },
                {
                    "name": "model",
                    "type": "STRING",
                    "mode": "NULLABLE"
                },
                {
                    "name": "response_object",
                    "type": "STRING",
                    "mode": "NULLABLE"
                }
            ]
        },
        {
            "name": "response_code",
            "type": "INTEGER",
            "mode": "NULLABLE"
        },
        {
            "name": "error_message",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "prediction_time",
            "type": "TIMESTAMP",
            "mode": "REQUIRED"
        },
        {
            "name": "prediction_duration_seconds",
            "type": "FLOAT64",
            "mode": "NULLABLE"
        }
    ]
}
