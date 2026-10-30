select
    customer_id,
    first_name,
    last_name,
    email,
    country_code,
    segment,
    created_at,
    updated_at
from {{ source('raw', 'customers') }}
