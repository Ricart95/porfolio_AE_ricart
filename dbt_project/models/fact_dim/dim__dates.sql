with
    date_array as (

        select
            cast(`date` as timestamp) as timestamp_date,

        from
            unnest(generate_date_array('2024-01-01', '2029-12-31')) as `date`
    ),


    final as (

        select
            timestamp_date,
            extract(day from timestamp_date) as `day`,
            extract(month from timestamp_date) as `month`,
            extract(year from timestamp_date) as `year`,
            extract(quarter from timestamp_date) as quarter,
            extract(isoweek from timestamp_date) as iso_week,
            extract(dayofweek from timestamp_date) as day_of_week,
            extract(dayofyear from timestamp_date) as day_of_year,
            format_date('%Y-%m-%d', timestamp_date) as `date`,
            format_date('%Y-%m', timestamp_date) as `year_month`,
            current_timestamp() as _dbt_updated_at

        from
            date_array
    )

select * 
from final