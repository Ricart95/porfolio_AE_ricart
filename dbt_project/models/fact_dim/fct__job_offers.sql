with

    source as (
        select * from {{ ref('stg__job_offers') }}
    ),

    final as (
        select

            -- Ids
            job_offer_id,
            qualification_id,
            naf_code                    as naf_id,


            -- Codes
            rome_code,
            contract_type_code,
            travel_requirement_code,
            workplace_postal_code       as postal_code,

            -- Strings
            job_title,
            job_appellation,
            company_name,
            contract_type_label,
            contract_nature,
            experience_required,
            experience_label,
            work_duration_label,
            work_duration_converted,
            travel_requirement_label,
            salary_label,
            salary_complement,
            rome_label,

            -- Integers
            number_of_positions,

            -- Booleans
            is_apprenticeship,
            is_disabled_accessible,
            is_hard_to_fill,
            is_adapted_company,

            -- Timestamps
            created_at,
            updated_at

        from source
    )

select * 
from final