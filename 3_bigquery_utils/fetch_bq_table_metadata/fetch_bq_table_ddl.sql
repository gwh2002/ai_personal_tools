select table_schema,
    table_name,
    table_type,
    TIMESTAMP_TRUNC(creation_time, SECOND) as creation_time,
    TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), SECOND) as fetched_at,
    ddl
from `region-us`.INFORMATION_SCHEMA.TABLES
where 1 = 1 -- and lower(table_name) = 'ifms_wa_most_recent_data'
    and table_schema in (
        'dataset1',
        'dataset2',
        'dataset3'
    )
    and table_name not like '%irrelevant table names%'
order by table_schema,
    table_name
limit 1000;