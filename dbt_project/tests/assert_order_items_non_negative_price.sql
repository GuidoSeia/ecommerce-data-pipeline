-- Falla si aparece algún producto con precio unitario negativo.
select *
from {{ ref('fct_order_items') }}
where unit_price < 0
