with trips as (
    select *
    from {{ ref('int_trips_unioned') }}
),

final as (
    select
        tripid,
        service_type,
        vendorid,
        ratecodeid,
        pickup_locationid,
        dropoff_locationid,
        pickup_datetime,
        dropoff_datetime,
        timestamp_diff(dropoff_datetime, pickup_datetime, minute) as trip_duration_minutes,
        store_and_fwd_flag,
        passenger_count,
        trip_distance,
        trip_type,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        ehail_fee,
        improvement_surcharge,
        total_amount,
        payment_type,
        payment_type_description,
        cast(date_trunc(date(pickup_datetime), month) as date) as trip_month
    from trips
    where pickup_datetime is not null
      and dropoff_datetime is not null
      and dropoff_datetime >= pickup_datetime
)

select * from final
