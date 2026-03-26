with 

    source as (
        select * from {{ ref('stg__job_offers') }}
    ),

    final as (
        select
            naf_code                as naf_id,
            activity_sector_code    as sector_code,
            activity_sector_label   as sector_label

        from source
        where naf_code is not null
        group by all
    )

select * 
from final