"this is an example DAG that runs a dummy task"

from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
import logging
import time  # Import time for sleep
from template_package.example_module import main
from template_package.Create_db_table import create_table


def foo():
    """A dummy function that simulates some work."""
    logger = logging.getLogger("airflow.task")
    logger.info("Executing foo...")
    time.sleep(5)  # Simulate a delay
    logger.info("foo completed.")


def bar():
    """A dummy function that simulates some work."""
    logger = logging.getLogger("airflow.task")
    logger.info("Executing bar...")
    time.sleep(5)  # Simulate a delay
    logger.info("bar completed.")


default_args = {
    "owner": "airflow",
    "start_date": pendulum.now("UTC").subtract(
        hours=1
    ),  # Start one hour ago for testing
    "retries": 1,
}

dag = DAG(
    "example_dag",
    default_args=default_args,
    description="An example DAG that runs a dummy task",
    schedule="*/5 * * * *",  # Run every 5 minutes
    catchup=False,  # Do not backfill
    tags=["example", "dummy"],
    max_active_runs=1,  # Limit to one active run at a time
)


run_foo_task = PythonOperator(
    task_id="example_function",
    python_callable=main,
    dag=dag,
)

run_bar_task = PythonOperator(
    task_id="create_table",
    python_callable=create_table,
    dag=dag,
)

run_bar_task >> run_foo_task
