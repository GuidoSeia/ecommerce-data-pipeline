-- Ingresos totales y por categoría de producto.
-- Se reconoce el ingreso en el momento del pago: solo se consideran
-- líneas de órdenes que llegaron a paid (is_paid), al precio de catálogo
-- actual (no hay historial de precios en el raw). No se netea por
-- devoluciones (returned) en este número.

-- Total
select
    round(sum(item_revenue), 2) as total_revenue
from marts.fct_order_items
where is_paid;

-- Por categoría
select
    category,
    round(sum(item_revenue), 2) as revenue,
    round(100.0 * sum(item_revenue) / sum(sum(item_revenue)) over (), 1) as pct_of_total
from marts.fct_order_items
where is_paid
group by 1
order by revenue desc;
