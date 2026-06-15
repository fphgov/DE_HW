import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from airflow.models import Variable

from template_package.TransitStopEvent import Base

def create_table():
    engine = create_engine(
        f"mssql+pymssql://{Variable.get('mssql_user')}:{Variable.get('mssql_password')}"
        f"@{Variable.get('mssql_host')}:{Variable.get('mssql_port')}"
        f"/{Variable.get('mssql_database')}",
        echo=True
    )

    Base.metadata.create_all(engine)
