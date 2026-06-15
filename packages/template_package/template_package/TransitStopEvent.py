from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Float, Time, BigInteger

Base = declarative_base()


class TransitStopEvent(Base):
    __tablename__ = "transit_stop_events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    route = Column(String(20), nullable=False)
    headsign = Column(String(100), nullable=False)
    trip_id = Column(String(50), nullable=False)

    stop_sequence = Column(Integer, nullable=False)
    stop_id = Column(String(20), nullable=False)
    stop_name = Column(String(150), nullable=False)

    event = Column(String(20), nullable=False)
    scheduled_time = Column(Time, nullable=False)

    predicted_timestamp = Column(BigInteger, nullable=False)
    delay_sec = Column(Integer, nullable=False)
    delay_min = Column(Float, nullable=False)