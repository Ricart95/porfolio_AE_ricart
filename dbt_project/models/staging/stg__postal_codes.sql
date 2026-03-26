with 

    source as ( 
        select * 
        from {{ ref('codes_postaux') }}  
    ),

    final as (
        select 
            lpad(code_postal, 5, '0')   as postal_code,
            code_departement            as department_code,
            libelle                     as city_name,
            nom_departement             as department_name,
            nom_region                  as region_name

        from source
        where nom_region is not null
        group by all
        qualify row_number() over (partition by postal_code order by region_name) = 1 -- En cas de doublons, on vient faire un traitement simple bien qu'arbitraire du fait d'un manque de feedback métier
    )

select *
from final