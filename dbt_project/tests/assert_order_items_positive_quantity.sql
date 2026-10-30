-- Falla si aparece alguna línea de orden con cantidad nula o no positiva.
select *
from {{ ref('fct_order_items') }}
where quantity is null or quantity <= 0
