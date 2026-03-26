with

    dates as (
        select * from {{ ref('dim__dates') }}
        where date(timestamp_date) <= current_date()
    ),

    regions as (
        select distinct
            region_name
        from {{ ref('stg__postal_codes') }}
        where region_name is not null
    ),

    date_region as (
        select
            cast(dates.timestamp_date as date) as date,
            dates.day,
            dates.month,
            dates.iso_week,
            dates.year,
            regions.region_name

        from dates
        cross join regions
    ),

    offers as (
        select
            date(created_at)        as offer_date,
            region_name,
            count(job_offer_id)     as nb_offers

        from {{ ref('job_offers') }}
        where region_name is not null
        group by all
    ),

    final as (
        select
            dr.day,
            dr.month,
            dr.iso_week,
            dr.year,
            dr.region_name,
            coalesce(o.nb_offers, 0)    as nb_offers

        from date_region dr
        left join offers o
            on dr.date = o.offer_date
            and dr.region_name = o.region_name
    )

select * 
from final
