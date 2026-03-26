with 

    source as (
        select * from {{ ref('stg__job_offers') }}
    ),

    final as (            
        select
            competence.code         as skill_id,
            competence.libelle      as skill_label

        from source,
        unnest(competences) as competence
        where competence.code is not null -- Si pas d'ID, pas fiable
        group by all  
    )

select * 
from final