-- Un registro por cliente, con el último estado conocido (tipo 1, sin
-- historial de segmento/país) y un flag de actividad: tuvo un evento
-- paid/shipped/delivered en los últimos 90 días respecto a la fecha más
-- reciente de los datos (as_of_date simula "hoy" sobre un dataset fijo).
--
-- A diferencia de stg_orders/fct_orders/fct_order_items, este modelo se
-- queda como full refresh: la cantidad de clientes crece órdenes de
-- magnitud más lento que el log de eventos de órdenes (cientos vs.
-- millones de filas con el tiempo), y ya lee fct_orders — que es chico y
-- está incremental — no el raw. Recalcularlo entero en cada corrida es
-- barato y evita la complejidad de trackear qué clientes cambiaron.
with orders as (
    select * from {{ ref('fct_orders') }}
),

customer_orders as (
    select
        customer_id,
        min(paid_at) as first_purchase_at,
        greatest(
            max(paid_at),
            max(shipped_at),
            max(delivered_at)
        ) as last_purchase_at,
        count(*) filter (where is_paid) as paid_orders
    from orders
    group by customer_id
),

as_of as (
    select max(last_event_at) as as_of_date from orders
)

select
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.country_code,
    c.segment,
    c.created_at as signed_up_at,
    co.first_purchase_at,
    co.last_purchase_at,
    coalesce(co.paid_orders, 0) as paid_orders,
    coalesce(
        co.last_purchase_at >= (select as_of_date from as_of) - interval '90 days',
        false
    ) as is_active
from {{ ref('stg_customers') }} c
left join customer_orders co on c.customer_id = co.customer_id
