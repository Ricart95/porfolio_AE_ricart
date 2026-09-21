with

    source as (
        select *
        from {{ ref('fct__job_offers') }}
    ),

    enriched as (
        select
            *,
            date_diff(CURRENT_TIMESTAMP(), created_at, day) as days_since_creation
            

        from source
    ),

    final as (
        select
            -- Ids
            job_offer_id,
            qualification_id,
            naf_id,

            -- Codes
            sector_code,
            rome_code,
            contract_type_code,
            travel_requirement_code,
            postal_code,
            department_code,

            -- Strings
            city_name,
            department_name,
            region_name,
            job_title,
            company_name,
            sector_label,
            rome_label,
            job_appellation,
            contract_type_label,
            contract_nature,
            experience_required,
            experience_label,
            qualification_label,
            work_duration_label,
            work_duration_converted,
            travel_requirement_label,
            salary_label,
            salary_complement,

            -- Integers
            number_of_positions,
            days_since_creation,

            -- Booleans
            is_apprenticeship,
            is_disabled_accessible,
            is_hard_to_fill,
            is_adapted_company,
            case
                when region_name = 'Ile-de-France' then True
                else False
            end as is_idf,

            -- Timestamps
            created_at,
            updated_at

        from enriched
        left join {{ ref('dim__qualifications') }}      using(qualification_id)
        left join {{ ref('dim__localisations') }}       using(postal_code)
        left join {{ ref('dim__sectors') }}             using(naf_id)

    )

select *
from final