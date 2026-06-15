from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Time, BigInteger


class Base(DeclarativeBase):
    pass


class TransitStopEvent(Base):
    __tablename__ = "transit_stop_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    route: Mapped[str] = mapped_column(String(20), nullable=False)
    headsign: Mapped[str] = mapped_column(String(100), nullable=False)
    trip_id: Mapped[str] = mapped_column(String(50), nullable=False)

    stop_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    stop_id: Mapped[str] = mapped_column(String(20), nullable=False)
    stop_name: Mapped[str] = mapped_column(String(150), nullable=False)

    event: Mapped[str] = mapped_column(String(20), nullable=False)
    scheduled_time: Mapped[str] = mapped_column(Time, nullable=False)

    predicted_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    delay_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_min: Mapped[float] = mapped_column(Float, nullable=False)