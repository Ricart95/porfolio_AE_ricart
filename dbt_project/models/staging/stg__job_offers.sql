with 
    source as (
        select *
        from {{ source('raw_france_travail', 'offres_emploi') }}
    ),

    final as (

        select 
            -- ids
            id                      as job_offer_id,

            -- description  
            intitule                as job_title,
            romeCode                as rome_code,
            romeLibelle             as rome_label,
            appellationlibelle      as job_appellation,

            -- type de contrat  
            typeContrat             as contract_type_code,
            typeContratLibelle      as contract_type_label,
            natureContrat           as contract_nature,

            -- experience
            experienceExige         as experience_required,
            experienceLibelle       as experience_label,
            experienceCommentaire   as experience_comment,

            -- qualification
            qualificationCode       as qualification_id,
            qualificationLibelle    as qualification_label,

            -- localisation
            lieuTravail.codePostal                                      as workplace_postal_code,
            concat(lieuTravail.latitude, ',', lieuTravail.longitude)    as workplace_geolocation,

            -- entreprise
            entreprise.nom                  as company_name,
            entreprise.entrepriseAdaptee    as is_adapted_company,

            -- salaire
            salaire.libelle                 as salary_label,
            salaire.complement1             as salary_complement,

            -- secteur
            codeNAF                         as naf_code,
            secteurActivite                 as activity_sector_code,
            secteurActiviteLibelle          as activity_sector_label,

            -- durée et conditions
            dureeTravailLibelle             as work_duration_label,
            dureeTravailLibelleConverti     as work_duration_converted,
            deplacementCode                 as travel_requirement_code,
            deplacementLibelle              as travel_requirement_label,
            alternance                      as is_apprenticeship,
            accessibleTH                    as is_disabled_accessible,
            nombrePostes                    as number_of_positions,
            offresManqueCandidats           as is_hard_to_fill,

            -- champs répétés (traités dans les prochains modèles)
            competences,
            formations,
            langues,
            permis,
            qualitesProfessionnelles,

            -- dates
            TIMESTAMP(REPLACE(dateCreation, 'Z', '+00:00'))         as created_at,
            TIMESTAMP(REPLACE(dateActualisation, 'Z', '+00:00'))    as updated_at

            from source
            group by all -- nécessaire pour éviter les doublons liés à la nature répétée de certains champs (ex: compétences)
    )

select *
from final