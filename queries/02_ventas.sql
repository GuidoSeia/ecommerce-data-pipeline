-- Ventas por día y por semana.
-- Una "venta" es una orden que llegó a estado paid, contada en la fecha
-- en que se pagó (una orden cuenta una sola vez, sin importar que luego
-- se haya enviado, entregado o devuelto).

-- Por día
select
    date_trunc('day', paid_at) as sale_day,
    count(*) as sales
from marts.fct_orders
where is_paid
group by 1
order by 1;

-- Por semana
select
    date_trunc('week', paid_at) as sale_week,
    count(*) as sales
from marts.fct_orders
where is_paid
group by 1
order by 1;
