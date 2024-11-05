CREATE TABLE IF NOT EXISTS predictor_v1_curated.output_v1
(
    input                       STRUCT <
                                        foo STRING NOT NULL,
                                        input_timestamp TIMESTAMP NOT NULL>,
    prediction                  STRUCT <
                                        text STRING,
                                        model STRING,
                                        response_object STRING>,
    response_code               INT64,
    error_message               STRING,
    prediction_time             TIMESTAMP NOT NULL,
    prediction_duration_seconds FLOAT64
);


-- This normally doesn't exist here. But I need to add it for this to function.
-- Following my pipeline pattern each pipeline is normally consuming the output of a another process so
-- (i.e. some_pipeline_v1.output_v1. The schema will be application specific but I just copied the one from above for convenience)
CREATE TABLE IF NOT EXISTS predictor_v1_curated.other_pipeline_output_v1
(
    foo         STRING    NOT NULL,
    inserted_at TIMESTAMP NOT NULL
);


CREATE OR REPLACE VIEW predictor_v1_curated.v_unprocessed_inputs_v1 AS
WITH cte_input AS
         (SELECT foo,
                 inserted_at
          FROM predictor_v1_curated.other_pipeline_output_v1
          --*************************************************************************************
          --*************************************************************************************
          -- NOTE: THIS LIMIT WILL HARD LIMIT ROWS THAT CAN BE RUN THROUGH THE PIPELINE
          --*************************************************************************************
          --*************************************************************************************
          LIMIT 5000)
SELECT input.foo,
       input.inserted_at
FROM cte_input input
         LEFT JOIN predictor_v1_curated.output_v1 output
                   ON input.foo = output.input.foo
WHERE output.input.foo IS NULL
ORDER BY input.inserted_at;


CREATE OR REPLACE VIEW predictor_v1_curated.v_errors_v1 AS
SELECT CAST(FROM_BASE64(error_message) AS STRING) AS decoded_error_message,
       *
FROM predictor_v1_curated.output_v1
WHERE response_code != 200;


CREATE OR REPLACE VIEW predictor_v1_curated.v_output_v1 AS
WITH cte_decoded AS
         (SELECT output.input,
                 CAST(FROM_BASE64(prediction.text) AS STRING) AS prediction,
                 output.prediction.model,
                 output.prediction.response_object,
                 output.response_code,
                 output.error_message,
                 output.prediction_time,
                 output.prediction_duration_seconds
          FROM predictor_v1_curated.output_v1 output
          WHERE response_code = 200)
SELECT input,
       prediction,
       model,
       response_object,
       response_code,
       error_message,
       prediction_time,
       prediction_duration_seconds
FROM cte_decoded;


----------------------------------------------------------------------------
-- OUTPUTS
----------------------------------------------------------------------------

-- I'd normally have views here that post process the output by doing things like extracting
-- the valuable output from the prediction text and formatting for easy consumption by analysts
-- and other consumers.