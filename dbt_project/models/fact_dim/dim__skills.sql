with 

    source as (
        select * from {{ ref('stg__job_offers') }}
    ),

    final as (            
        select
            competence.code         as skill_id,
            -- Un même code peut avoir plusieurs libellés (variantes, encodage cassé) : on garde le plus fréquent
            approx_top_count(competence.libelle, 1)[offset(0)].value as skill_label

        from source,
        unnest(competences) as competence
        where competence.code is not null -- Si pas d'ID, pas fiable
        group by skill_id
    )

select * 
from final