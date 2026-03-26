with

    source as (
        select * from {{ ref('stg__job_offers') }}
    ),

    final as (
        select
            qualification_id,
            qualification_label
            
        from source
        where qualification_id is not null
        group by all
    )

select * 
from final