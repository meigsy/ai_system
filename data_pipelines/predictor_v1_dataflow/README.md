# Predictor v1

This pipeline uses apache beam to make a prediction for each row in an input table.

It reads from an input table, and for each input, performs its process, then stores the output into an output table. The full input is saved with the output to give the full context without needing to
re-run pipelines or join datasets or anything. Data is cheap, engineer time is not. The output is unprocessed. Its unknowable what you'll need in the future so save all of it. Also, this prevents data
loss due to processing and parsing errors. Deal with it after the fact, and you'll never lose any information (aka the lifeblood of all we do). Also, memory is cheap, engineer time is not.

There's normally tests in ./tests but those are application specific so I didn't put any examples in.

This pipeline is an atomic, idempotent node in a data mesh. This is the fundamental unit of work in my systems. You would swap out the prediction process for any type of language model, image model,
algorithm, whatever. The pattern is:

1. read inputs
2. do work
3. write outputs

As long as the input table adheres to its contract, it'll process the data and write to the output table. Using apache beam means we don't have to manage the cluster of compute under the hood. It
could be one machine or hundreds or thousands of machines (which is the scale I usually find myself in). And if necessary we can deep dive into machine types and such like in spark. But I've built
around 30+ of these to iteratively build our data mesh, and I've yet to need to dive deep enough to justify the technical overhead of using spark.

---

## Getting Started

1. execute: `source setup_venv.sh`
2. TDD to your heart's content!

## Execute Locally

1. Open run_local.py
2. Execute the main function

## Enhancements

1. TBD