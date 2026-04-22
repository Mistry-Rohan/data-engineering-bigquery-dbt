select
    tripid,
    pickup_datetime,
    dropoff_datetime,
    trip_duration_minutes
from {{ ref('fct_taxi_trips') }}
where trip_duration_minutes < 0
