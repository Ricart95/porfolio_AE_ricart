with 

    source as (
        select * from {{ ref('stg__job_offers') }}
    ),

    final as (            
        select
            f.codeFormation    as formation_id,
            f.domaineLibelle   as domain_label,
            f.niveauLibelle    as level_label


        from source,
        unnest(source.formations) as f
        where f.codeFormation is not null -- Si pas d'ID, pas fiable
        qualify row_number() over (partition by f.codeFormation order by f.codeFormation) = 1
    )

select * 
from final