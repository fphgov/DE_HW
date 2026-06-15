import io
import zipfile
import requests
import pandas as pd

from datetime import datetime, timedelta
from google.transit import gtfs_realtime_pb2

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

API_KEY = "0ed267e5-7ae5-4872-adbe-c9925b452570"

TRIP_UPDATES_URL = "https://go.bkk.hu/api/query/v1/ws/gtfs-rt/full/TripUpdates.pb"
GTFS_ZIP_URL = "https://go.bkk.hu/api/static/v1/public-gtfs/budapest_gtfs.zip"


def download_gtfs_maps():
    print("Downloading static GTFS...")

    r = requests.get(GTFS_ZIP_URL, timeout=60)
    r.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(r.content))

    routes = pd.read_csv(z.open("routes.txt"), dtype=str)
    stops = pd.read_csv(z.open("stops.txt"), dtype=str)
    trips = pd.read_csv(z.open("trips.txt"), dtype=str)
    stop_times = pd.read_csv(z.open("stop_times.txt"), dtype=str)

    route_map = dict(zip(routes["route_id"], routes["route_short_name"]))
    stop_map = dict(zip(stops["stop_id"], stops["stop_name"]))
    trip_map = dict(zip(trips["trip_id"], trips["trip_headsign"]))

    # (trip_id, stop_sequence) -> scheduled arrival time
    scheduled_map = {}

    for row in stop_times.itertuples():
        try:
            scheduled_map[(row.trip_id, int(row.stop_sequence))] = row.arrival_time
        except:
            pass

    print("GTFS loaded.")
    print("Routes:", len(route_map))
    print("Stops:", len(stop_map))
    print("Trips:", len(trip_map))
    print("Scheduled stop times:", len(scheduled_map))

    return route_map, stop_map, trip_map, scheduled_map


def download_trip_updates(api_key):
    print("\nDownloading realtime TripUpdates...")

    r = requests.get(
        TRIP_UPDATES_URL,
        params={"key": api_key},
        timeout=30,
    )

    print("STATUS:", r.status_code)
    print("TYPE:", r.headers.get("content-type"))

    r.raise_for_status()

    if "protobuf" not in r.headers.get("content-type", ""):
        print(r.text[:1000])
        raise ValueError("Response is not protobuf")

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(r.content)

    print("Feed entities:", len(feed.entity))

    return feed


def gtfs_time_to_timestamp(gtfs_time):
    """
    Converts GTFS time like:
    14:30:00
    25:10:00

    into today's Unix timestamp.
    """

    h, m, s = map(int, gtfs_time.split(":"))

    today = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    dt = today + timedelta(
        hours=h,
        minutes=m,
        seconds=s
    )

    return int(dt.timestamp())


def extract_delays(
    feed,
    route_map,
    stop_map,
    trip_map,
    scheduled_map,
    route_filter=None
):
    rows = []

    total_trip_updates = 0
    total_stop_updates = 0
    matched_stop_times = 0

    for entity in feed.entity:

        if not entity.HasField("trip_update"):
            continue

        total_trip_updates += 1

        tu = entity.trip_update
        trip = tu.trip

        route_id = trip.route_id
        trip_id = trip.trip_id

        route_name = route_map.get(route_id, route_id)
        headsign = trip_map.get(trip_id, "")

        # optional filter
        if route_filter is not None:
            if route_name != route_filter:
                continue

        for s in tu.stop_time_update:

            total_stop_updates += 1

            try:
                stop_sequence = int(s.stop_sequence)
            except:
                continue

            scheduled_gtfs_time = scheduled_map.get(
                (trip_id, stop_sequence)
            )

            if scheduled_gtfs_time is None:
                continue

            matched_stop_times += 1

            predicted_time = None
            event_type = None

            if s.HasField("arrival") and s.arrival.HasField("time"):
                predicted_time = s.arrival.time
                event_type = "arrival"

            elif s.HasField("departure") and s.departure.HasField("time"):
                predicted_time = s.departure.time
                event_type = "departure"

            if predicted_time is None:
                continue

            scheduled_timestamp = gtfs_time_to_timestamp(
                scheduled_gtfs_time
            )

            delay_sec = predicted_time - scheduled_timestamp
            delay_min = round(delay_sec / 60, 1)

            rows.append({
                "route": route_name,
                "headsign": headsign,
                "trip_id": trip_id,
                "stop_sequence": stop_sequence,
                "stop_id": s.stop_id,
                "stop_name": stop_map.get(s.stop_id, s.stop_id),
                "event": event_type,
                "scheduled_time": scheduled_gtfs_time,
                "predicted_timestamp": predicted_time,
                "delay_sec": delay_sec,
                "delay_min": delay_min,
            })

    print("\nTrip updates:", total_trip_updates)
    print("Stop updates:", total_stop_updates)
    print("Matched scheduled stop times:", matched_stop_times)
    print("Rows created:", len(rows))

    return pd.DataFrame(rows)


def main():

    route_map, stop_map, trip_map, scheduled_map = download_gtfs_maps()

    feed = download_trip_updates(API_KEY)

    # route_filter examples:
    # "105"
    # "4"
    # "6"
    # "M3"

    df = extract_delays(
        feed=feed,
        route_map=route_map,
        stop_map=stop_map,
        trip_map=trip_map,
        scheduled_map=scheduled_map,
        route_filter=None
    )

    if df.empty:
        print("\nNo data rows created.")
        return

    df = df.sort_values([
        "route",
        "trip_id",
        "stop_sequence"
    ])

    print("\nFIRST 50 ROWS:\n")
    print(df.head(50).to_string(index=False))

    output_file = "bkk_delays.csv"

    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nSaved CSV: {output_file}")


if __name__ == "__main__":
    main()