-- raw.orders es un log de eventos que crece sin límite (una fila por cada
-- cambio de estado de cada orden, para siempre). Reescanear toda la tabla
-- en cada corrida no escala, así que este modelo es incremental: cada
-- corrida solo procesa los eventos cuyo _ingested_at es posterior al
-- máximo ya cargado. El join por (order_id, status, event_at) como
-- unique_key hace que, si un evento ya cargado se reingesta (duplicado de
-- extracción), se pise a sí mismo en vez de duplicarse.
{{
    config(
        materialized='incremental',
        unique_key=['order_id', 'status', 'event_at'],
        incremental_strategy='delete+insert'
    )
}}

select
    order_id,
    any_value(customer_id) as customer_id,
    status,
    event_at,
    max(_ingested_at) as _ingested_at
from {{ source('raw', 'orders') }}
{% if is_incremental() %}
where _ingested_at > (select coalesce(max(_ingested_at), timestamp '1900-01-01') from {{ this }})
{% endif %}
group by order_id, status, event_at
