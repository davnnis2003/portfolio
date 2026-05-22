-- Populate staging.new_leads from ods.new_leads
TRUNCATE TABLE staging.new_leads;

INSERT INTO staging.new_leads (
    lead_id,
    created_at,
    customer_title,
    customer_surname,
    customer_segment,
    region,
    postal_area,
    city,
    product,
    rep_id,
    call_duration_min,
    building_type,
    building_year,
    n_vollgeschosse,
    heating_system,
    fassaden_typ,
    mauerstarke_cm,
    has_hohlraum,
    hohlraum_size_cm,
    is_gewoelbekeller,
    feuchtigkeit,
    dachboden_zukunft_wohnraum
)
SELECT
    intake_data->>'lead_id',
    (intake_data->>'created_at')::DATE,
    intake_data->'customer'->>'title',
    intake_data->'customer'->>'surname',
    intake_data->'customer'->>'segment',
    intake_data->'address'->>'region',
    intake_data->'address'->>'postal_area',
    intake_data->'address'->>'city',
    intake_data->>'product',
    intake_data->>'rep_id',
    (intake_data->>'call_duration_min')::INTEGER,
    intake_data->'fields'->>'building_type',
    (intake_data->'fields'->>'building_year')::INTEGER,
    (intake_data->'fields'->>'n_vollgeschosse')::INTEGER,
    intake_data->'fields'->>'heating_system',
    intake_data->'fields'->>'fassaden_typ',
    (intake_data->'fields'->>'mauerstarke_cm')::NUMERIC,
    (intake_data->'fields'->>'has_hohlraum')::BOOLEAN,
    (intake_data->'fields'->>'hohlraum_size_cm')::NUMERIC,
    (intake_data->'fields'->>'is_gewoelbekeller')::BOOLEAN,
    (intake_data->'fields'->>'feuchtigkeit')::BOOLEAN,
    (intake_data->'fields'->>'dachboden_zukunft_wohnraum')::BOOLEAN
FROM
    ods.new_leads;

-- Populate staging.new_lead_transcripts from ods.new_lead_transcripts
TRUNCATE TABLE staging.new_lead_transcripts;

INSERT INTO staging.new_lead_transcripts (
    lead_id,
    transcript_text,
    word_count,
    filename
)
SELECT
    lead_id,
    transcript_text,
    cardinality(regexp_split_to_array(trim(transcript_text), '\s+')) as word_count,
    filename
FROM
    ods.new_lead_transcripts;
