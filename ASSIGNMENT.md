# Prueba técnica — Data Engineering

## El escenario

Una empresa de e-commerce vende productos en varios países de Latinoamérica y España. Sus sistemas operativos (clientes, catálogo y órdenes) se extraen periódicamente hacia un data lake. Esa extracción ya está hecha y te la entregamos en un archivo DuckDB.

El equipo de negocio quiere empezar a tomar decisiones con datos y te pidió lo siguiente.

## Lo que necesita el negocio

- **Clientes.** Saber cuántos clientes tenemos, cuántos están activos y cómo crece la base de clientes mes a mes.
- **Ventas.** Ver la cantidad de ventas por día y por semana.
- **Ingresos.** Conocer los ingresos totales y cómo se abren por categoría de producto.
- **Órdenes.** Entender qué proporción de las órdenes se entrega y qué proporción se cancela.

## Lo que te entregamos

```
.
├── README.md
└── data/
    └── ecommerce.duckdb   # datos tal como llegan de la fuente
```

El archivo `data/ecommerce.duckdb` contiene el schema `raw` con cuatro tablas:

| Tabla | Descripción |
|---|---|
| `raw.customers` | Clientes registrados en la plataforma. |
| `raw.products` | Catálogo de productos y su precio de lista. |
| `raw.orders` | Eventos del ciclo de vida de cada orden. |
| `raw.order_items` | Productos y cantidades incluidos en cada orden. |

Las columnas con prefijo `_` son metadatos de la extracción: `_extracted_at` indica cuándo se tomó la información de la fuente y `_ingested_at`, cuándo llegó el registro al data lake.

## Lo que esperamos

Construye, sobre el mismo DuckDB (u otro archivo DuckDB propio), el modelo de datos que consideres adecuado para responder las preguntas del negocio, junto con el proceso que lo genera a partir de `raw`.

El proceso se ejecuta en forma batch, una vez por día.

## Stack

- Python y SQL sobre DuckDB.
- Puedes usar dbt si te resulta cómodo; no es obligatorio.
- No hace falta implementar un orquestador: alcanza con un punto de entrada claro.

## Qué entregar

Crea tu propio repositorio público (GitHub, GitLab o similar) que contenga:

- El código del proceso que construye tu modelo de datos a partir de `raw`.
- Las consultas que responden cada una de las preguntas del negocio.
- Un `README.md` con:
  - Instrucciones para ejecutar todo desde cero en una máquina limpia.
  - Una sección de decisiones con las decisiones de diseño y los supuestos que tomaste.
  - Cómo orquestarías el proceso diario en un entorno productivo (por ejemplo, con Airflow). No hace falta implementarlo, solo describirlo.

Cuando termines, envíanos el enlace al repositorio.

## Reglas del juego

- Plazo de entrega: 5 días corridos desde que recibes la prueba.
- Uso de IA: está permitido. Indica en el `README.md` qué herramientas usaste y para qué.
- Si algo de la consigna te resulta ambiguo, toma una decisión, déjala documentada en la sección de decisiones y sigue adelante.

## Próximo paso

Después de la entrega, haremos una entrevista virtual en la que revisaremos la solución juntos.

¡Éxitos!
