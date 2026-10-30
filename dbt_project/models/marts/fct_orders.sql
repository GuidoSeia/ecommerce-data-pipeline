-- Una fila por orden: pivotea el log de eventos de stg_orders en columnas
-- de timestamp por estado y deriva el estado actual (el más avanzado
-- alcanzado). cancelled es siempre terminal en los datos de origen, nunca
-- va seguido de shipped/delivered.
--
-- Incremental: una orden vieja puede recibir un evento nuevo en cualquier
-- momento (ej. una orden pagada hace semanas recién ahora se entrega), así
-- que no alcanza con agregar filas nuevas. En cada corrida se identifican
-- las órdenes con al menos un evento cargado desde la última corrida
-- (affected_orders) y se recalcula el pivot completo solo para esas
-- órdenes, usando TODO su historial de eventos — no solo los nuevos.
-- _loaded_at guarda el checkpoint para la próxima corrida incremental.
{{
    config(
        materialized='incremental',
        unique_key='order_id',
        incremental_strategy='delete+insert'
    )
}}

with affected_orders as (
    select distinct order_id
    from {{ ref('stg_orders') }}
    {% if is_incremental() %}
    where _ingested_at > (select coalesce(max(_loaded_at), timestamp '1900-01-01') from {{ this }})
    {% endif %}
),

pivoted as (
    select
        o.order_id,
        any_value(o.customer_id) as customer_id,
        min(o.event_at) filter (where o.status = 'created') as created_at,
        min(o.event_at) filter (where o.status = 'paid') as paid_at,
        min(o.event_at) filter (where o.status = 'shipped') as shipped_at,
        min(o.event_at) filter (where o.status = 'delivered') as delivered_at,
        min(o.event_at) filter (where o.status = 'cancelled') as cancelled_at,
        min(o.event_at) filter (where o.status = 'returned') as returned_at,
        max(o.event_at) as last_event_at,
        max(o._ingested_at) as _loaded_at
    from {{ ref('stg_orders') }} o
    {% if is_incremental() %}
    inner join affected_orders a on o.order_id = a.order_id
    {% endif %}
    group by o.order_id
)

select
    order_id,
    customer_id,
    created_at,
    paid_at,
    shipped_at,
    delivered_at,
    cancelled_at,
    returned_at,
    last_event_at,
    _loaded_at,
    case
        when returned_at is not null then 'returned'
        when delivered_at is not null then 'delivered'
        when cancelled_at is not null then 'cancelled'
        when shipped_at is not null then 'shipped'
        when paid_at is not null then 'paid'
        else 'created'
    end as current_status,
    paid_at is not null as is_paid
from pivoted
