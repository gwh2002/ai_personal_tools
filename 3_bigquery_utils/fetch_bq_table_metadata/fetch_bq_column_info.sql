select 
    table_schema,
    table_name,
    column_name,
    ordinal_position,
    data_type,
    CURRENT_TIMESTAMP() as fetched_at
from `region-us`.INFORMATION_SCHEMA.COLUMNS
where 1=1
and table_catalog = 'project'
-- and lower(table_name) = 'ifms_wa_most_recent_data'
and table_name like '%relevant table names%'
and table_name not like '%irrelevant table names%'
order by table_schema, table_name, ordinal_position
limit 1000;