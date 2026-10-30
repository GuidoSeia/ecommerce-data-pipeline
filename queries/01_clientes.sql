-- Clientes: total, activos y crecimiento mensual de la base.
-- "Activo" = tuvo un evento paid/shipped/delivered en los últimos 90 días

-- Total y activos
select
    count(*) as total_customers,
    count(*) filter (where is_active) as active_customers
from marts.dim_customers;

-- Crecimiento mensual de la base (altas por mes y acumulado)
select
    date_trunc('month', signed_up_at) as month,
    count(*) as new_customers,
    sum(count(*)) over (order by date_trunc('month', signed_up_at)) as cumulative_customers
from marts.dim_customers
group by 1
order by 1;
