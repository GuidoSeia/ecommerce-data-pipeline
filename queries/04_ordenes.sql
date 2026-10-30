-- Qué proporción de las órdenes se entrega y qué proporción se cancela.
-- Se toma el estado actual (el más avanzado alcanzado) de cada orden,
-- sobre el total de órdenes, de forma que las proporciones sumen 100%.

select
    current_status,
    count(*) as orders,
    round(100.0 * count(*) / sum(count(*)) over (), 1) as pct_of_total
from marts.fct_orders
group by 1
order by orders desc;
