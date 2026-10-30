-- order_items crece al mismo ritmo que las órdenes, así que también es
-- incremental: solo se procesan líneas nuevas según _ingested_at.
-- (order_id, line_number) no es una clave única en el raw: hay casos donde
-- la misma línea quedó registrada con un product_id o quantity distinto
-- entre dos extracciones. Nos quedamos con la versión más reciente según
-- _ingested_at; el merge por unique_key hace que una corrección posterior
-- pise la fila vieja en vez de duplicarla.
{{
    config(
        materialized='incremental',
        unique_key=['order_id', 'line_number'],
        incremental_strategy='delete+insert'
    )
}}

with ranked as (
    select
        order_id,
        line_number,
        product_id,
        quantity,
        _ingested_at,
        row_number() over (
            partition by order_id, line_number
            order by _ingested_at desc
        ) as rn
    from {{ source('raw', 'order_items') }}
    {% if is_incremental() %}
    where _ingested_at > (select coalesce(max(_ingested_at), timestamp '1900-01-01') from {{ this }})
    {% endif %}
)

select
    order_id,
    line_number,
    product_id,
    quantity,
    _ingested_at
from ranked
where rn = 1
