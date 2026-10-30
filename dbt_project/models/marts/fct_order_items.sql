-- Una fila por línea de orden, con el producto, la categoría y el revenue
-- calculado al precio de catálogo actual (no hay historial de precios en
-- el raw). Trae también el estado de la orden para poder filtrar por
-- órdenes pagas en las queries de ingresos.
--
-- Incremental, con el mismo criterio que fct_orders: una línea se
-- reprocesa si llegó un ítem nuevo/corregido o si cambió el estado de su
-- orden (ej. pasa a "paid"), para que current_status/is_paid no queden
-- desactualizados en filas ya cargadas.
{{
    config(
        materialized='incremental',
        unique_key=['order_id', 'line_number'],
        incremental_strategy='delete+insert'
    )
}}

{% if is_incremental() %}
with affected_orders as (
    select distinct order_id
    from {{ ref('stg_order_items') }}
    where _ingested_at > (select coalesce(max(_loaded_at), timestamp '1900-01-01') from {{ this }})

    union

    select order_id
    from {{ ref('fct_orders') }}
    where _loaded_at > (select coalesce(max(_loaded_at), timestamp '1900-01-01') from {{ this }})
)
{% endif %}

select
    oi.order_id,
    oi.line_number,
    oi.product_id,
    p.product_name,
    p.category,
    oi.quantity,
    p.unit_price,
    p.currency,
    oi.quantity * p.unit_price as item_revenue,
    o.customer_id,
    o.current_status,
    o.is_paid,
    o.paid_at,
    o.created_at as order_created_at,
    oi._ingested_at as _loaded_at
from {{ ref('stg_order_items') }} oi
join {{ ref('stg_products') }} p on oi.product_id = p.product_id
join {{ ref('fct_orders') }} o on oi.order_id = o.order_id
{% if is_incremental() %}
where oi.order_id in (select order_id from affected_orders)
{% endif %}
