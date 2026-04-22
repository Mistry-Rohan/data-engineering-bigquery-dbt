with tripdata as (
    select *
    from {{ source('bronze', 'green_tripdata') }}
    where vendorid is not null
),

renamed as (
    select
        -- identifiers
        {{ build_trip_id([
            "vendorid",
            "lpep_pickup_datetime",
            "lpep_dropoff_datetime",
            "pulocationid",
            "dolocationid"
        ]) }} as tripid,
        cast(vendorid as int64) as vendorid,
        cast(ratecodeid as int64) as ratecodeid,
        cast(pulocationid as int64) as pickup_locationid,
        cast(dolocationid as int64) as dropoff_locationid,

        -- timestamps
        cast(lpep_pickup_datetime as timestamp) as pickup_datetime,
        cast(lpep_dropoff_datetime as timestamp) as dropoff_datetime,

        -- trip info
        store_and_fwd_flag,
        cast(passenger_count as int64) as passenger_count,
        cast(trip_distance as numeric) as trip_distance,
        cast(trip_type as int64) as trip_type,

        -- payment info
        cast(fare_amount as numeric) as fare_amount,
        cast(extra as numeric) as extra,
        cast(mta_tax as numeric) as mta_tax,
        cast(tip_amount as numeric) as tip_amount,
        cast(tolls_amount as numeric) as tolls_amount,
        cast(ehail_fee as numeric) as ehail_fee,
        cast(improvement_surcharge as numeric) as improvement_surcharge,
        cast(total_amount as numeric) as total_amount,
        cast(payment_type as int64) as payment_type
    from tripdata
),

final as (
    select
        *,
        {{ get_payment_type_description('payment_type') }} as payment_type_description
    from renamed
)

select * from final
