with 

    source as (
        select * from {{ ref('stg__job_offers') }}
    ),

    postal_codes as (
        select
            postal_code,
            city_name,
            department_code,
            department_name,
            region_name

        from {{ ref('stg__postal_codes') }}
        group by all
    ),

    final as (            
        select 
            workplace_postal_code   as postal_code,
            department_code,
            city_name,
            department_name,
            region_name

        from source
        left join postal_codes on source.workplace_postal_code = postal_codes.postal_code -- jointure pour éviter les doublons sur noms de villes
        where workplace_postal_code is not null -- Si pas de code postal, pas utile
            and region_name is not null -- Exclut les codes postaux absents du référentiel
        group by all
    )

select *
from final