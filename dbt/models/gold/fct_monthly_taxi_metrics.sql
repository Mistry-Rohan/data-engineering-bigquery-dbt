with monthly_metrics as (
    select
        trip_month,
        service_type,
        count(*) as trip_count,
        sum(coalesce(passenger_count, 0)) as passenger_count,
        sum(coalesce(trip_distance, 0)) as total_trip_distance,
        sum(coalesce(fare_amount, 0)) as total_fare_amount,
        sum(coalesce(tip_amount, 0)) as total_tip_amount,
        sum(coalesce(total_amount, 0)) as total_amount,
        avg(coalesce(trip_distance, 0)) as avg_trip_distance,
        avg(coalesce(total_amount, 0)) as avg_total_amount
    from {{ ref('fct_taxi_trips') }}
    group by 1, 2
)

select * from monthly_metrics
