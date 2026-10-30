select
    product_id,
    product_name,
    category,
    unit_price,
    currency,
    created_at,
    updated_at
from {{ source('raw', 'products') }}
