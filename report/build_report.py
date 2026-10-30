"""Genera report.html con las respuestas a las 4 preguntas de negocio.

Lee las consultas de queries/*.sql, las corre contra data/warehouse.duckdb
(el target que arma dbt) y arma un HTML autocontenido con KPIs, un gráfico
y el detalle tabular para cada pregunta.
"""
import base64
import datetime as dt
import io
import pathlib

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
WAREHOUSE_PATH = ROOT / "data" / "warehouse.duckdb"
QUERIES_DIR = ROOT / "queries"
OUTPUT_PATH = ROOT / "report.html"

COLORS = {
    "bg": "#f5f6f4",
    "card": "#ffffff",
    "border": "#e1e4df",
    "text": "#1c231f",
    "muted": "#6b756e",
    "accent": "#28603f",
    "accent_soft": "#e4efe8",
    "danger": "#a4463c",
    "amber": "#b8863c",
    "neutral": "#8b948d",
}

STATUS_COLORS = {
    "delivered": COLORS["accent"],
    "cancelled": COLORS["danger"],
    "returned": COLORS["amber"],
    "paid": COLORS["neutral"],
    "shipped": "#5f7a6c",
    "created": "#b7beb9",
}

STATUS_LABELS = {
    "created": "Creada",
    "paid": "Pagada",
    "shipped": "Enviada",
    "delivered": "Entregada",
    "cancelled": "Cancelada",
    "returned": "Devuelta",
}

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 10.5,
    "axes.edgecolor": COLORS["border"],
    "text.color": COLORS["text"],
    "axes.labelcolor": COLORS["muted"],
    "xtick.color": COLORS["muted"],
    "ytick.color": COLORS["muted"],
})


def split_statements(sql_text: str) -> list[str]:
    statements = []
    for chunk in sql_text.split(";"):
        lines = [
            line for line in chunk.splitlines() if line.strip() and not line.strip().startswith("--")
        ]
        if lines:
            statements.append("\n".join(lines))
    return statements


def run_query_file(con: duckdb.DuckDBPyConnection, filename: str) -> list[tuple[list[str], list[tuple]]]:
    sql_text = (QUERIES_DIR / filename).read_text()
    results = []
    for statement in split_statements(sql_text):
        cursor = con.execute(statement)
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
        results.append((columns, rows))
    return results


def fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.patch.set_facecolor(COLORS["card"])
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", facecolor=COLORS["card"])
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def style_axes(ax):
    ax.set_facecolor(COLORS["card"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["border"])
    ax.grid(axis="y", color=COLORS["border"], linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def shades(n: int, dark_hex: str, light_hex: str) -> list[str]:
    def to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    dark, light = to_rgb(dark_hex), to_rgb(light_hex)
    if n <= 1:
        return [dark_hex]
    out = []
    for i in range(n):
        t = i / (n - 1)
        rgb = tuple(round(dark[c] + (light[c] - dark[c]) * t) for c in range(3))
        out.append("#{:02x}{:02x}{:02x}".format(*rgb))
    return out


def table_html(columns: list[str], rows: list[tuple], labels: dict[str, str] | None = None) -> str:
    labels = labels or {}
    head = "".join(f"<th>{labels.get(c, c)}</th>" for c in columns)
    body = ""
    for row in rows:
        cells = "".join(f"<td>{format_cell(v)}</td>" for v in row)
        body += f"<tr>{cells}</tr>"
    inner = f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    return f"<details class=\"detail\"><summary>Ver el detalle</summary>{inner}</details>"


def format_cell(value) -> str:
    if value is None:
        return "–"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def kpi(value: str, label: str) -> str:
    return f'<div class="kpi"><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div></div>'


def line_area_chart(x_labels, y_values, ylabel: str) -> str:
    fig, ax = plt.subplots(figsize=(7.4, 3))
    ax.plot(x_labels, y_values, color=COLORS["accent"], linewidth=2.2, marker="o", markersize=3.5)
    ax.fill_between(range(len(x_labels)), y_values, color=COLORS["accent"], alpha=0.08)
    ax.set_ylabel(ylabel)
    style_axes(ax)
    step = max(1, len(x_labels) // 10)
    ax.set_xticks(range(0, len(x_labels), step))
    ax.set_xticklabels([x_labels[i] for i in range(0, len(x_labels), step)], rotation=40, ha="right")
    return fig_to_base64(fig)


def bar_chart(labels, values, ylabel: str, colors=None, horizontal: bool = False) -> str:
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    colors = colors or COLORS["accent"]
    if horizontal:
        ax.barh(labels, values, color=colors)
        ax.set_xlabel(ylabel)
        ax.invert_yaxis()
    else:
        ax.bar(labels, values, color=colors)
        ax.set_ylabel(ylabel)
    style_axes(ax)
    return fig_to_base64(fig)


def section_clientes(con) -> str:
    totals, growth = run_query_file(con, "01_clientes.sql")
    total_customers, active_customers = totals[1][0]
    active_pct = 100 * active_customers / total_customers if total_customers else 0
    months = [row[0].strftime("%Y-%m") for row in growth[1]]
    cumulative = [row[2] for row in growth[1]]

    kpis = (
        kpi(f"{total_customers:,}", "Clientes totales")
        + kpi(f"{active_customers:,}", "Activos (últimos 90 días)")
        + kpi(f"{active_pct:.0f}%", "Proporción activa")
    )
    intro = "Evolución de la base de clientes mes a mes, acumulada desde el primer registro."
    chart = line_area_chart(months, cumulative, "Clientes acumulados")
    table = table_html(*growth, labels={"month": "Mes", "new_customers": "Altas", "cumulative_customers": "Acumulado"})
    return render_section("clientes", "Clientes", intro, kpis, chart, table)


def section_ventas(con) -> str:
    daily, weekly = run_query_file(con, "02_ventas.sql")
    daily_counts = [row[1] for row in daily[1]]
    weeks = [row[0].strftime("%Y-%m-%d") for row in weekly[1]]
    weekly_counts = [row[1] for row in weekly[1]]

    total_sales = sum(daily_counts)
    avg_per_day = total_sales / len(daily_counts) if daily_counts else 0
    avg_per_week = total_sales / len(weekly_counts) if weekly_counts else 0

    kpis = (
        kpi(f"{total_sales:,}", "Ventas totales")
        + kpi(f"{avg_per_day:.1f}", "Promedio diario")
        + kpi(f"{avg_per_week:.0f}", "Promedio semanal")
    )
    intro = "Órdenes pagadas por semana. El detalle diario tiene más ruido y está en la tabla."
    chart = line_area_chart(weeks, weekly_counts, "Ventas por semana")
    table = table_html(*daily, labels={"sale_day": "Día", "sales": "Ventas"})
    return render_section("ventas", "Ventas", intro, kpis, chart, table)


def section_ingresos(con) -> str:
    total, by_category = run_query_file(con, "03_ingresos.sql")
    total_revenue = total[1][0][0]
    categories = [row[0] for row in by_category[1]]
    revenue = [row[1] for row in by_category[1]]
    top_category = categories[0] if categories else "–"
    top_share = by_category[1][0][2] if by_category[1] else 0

    kpis = (
        kpi(f"USD {total_revenue:,.0f}", "Ingresos totales")
        + kpi(top_category.title() if top_category != "–" else "–", "Categoría líder")
        + kpi(f"{top_share:.0f}%", "Participación de la líder")
    )
    intro = "Ingresos reconocidos al momento del pago, abiertos por categoría de producto."
    colors = shades(len(categories), COLORS["accent"], COLORS["accent_soft"])
    chart = bar_chart(categories, revenue, "Ingresos (USD)", colors=colors, horizontal=True)
    table = table_html(*by_category, labels={"category": "Categoría", "revenue": "Ingresos (USD)", "pct_of_total": "% del total"})
    return render_section("ingresos", "Ingresos", intro, kpis, chart, table)


def section_ordenes(con) -> str:
    (result,) = run_query_file(con, "04_ordenes.sql")
    columns, rows = result
    statuses = [row[0] for row in rows]
    counts = [row[1] for row in rows]
    pct_by_status = {row[0]: row[2] for row in rows}
    colors = [STATUS_COLORS.get(s, COLORS["neutral"]) for s in statuses]
    status_es = [STATUS_LABELS.get(s, s) for s in statuses]

    delivered_pct = pct_by_status.get("delivered", 0)
    cancelled_pct = pct_by_status.get("cancelled", 0)

    kpis = (
        kpi(f"{delivered_pct:.0f}%", "Entregadas")
        + kpi(f"{cancelled_pct:.0f}%", "Canceladas")
        + kpi(f"{sum(counts):,}", "Órdenes totales")
    )
    intro = "Distribución de órdenes por su estado actual, sobre el total histórico."
    chart = bar_chart(status_es, counts, "Cantidad de órdenes", colors=colors)
    display_rows = [(STATUS_LABELS.get(r[0], r[0]), r[1], r[2]) for r in rows]
    table = table_html(["Estado", "Órdenes", "% del total"], display_rows)
    return render_section("ordenes", "Órdenes", intro, kpis, chart, table)


def render_section(anchor: str, title: str, intro: str, kpis: str, chart_b64: str, table: str) -> str:
    return f"""
    <section id="{anchor}" class="card">
      <h2>{title}</h2>
      <p class="intro">{intro}</p>
      <div class="kpis">{kpis}</div>
      <img src="data:image/png;base64,{chart_b64}" alt="Gráfico de {title.lower()}">
      {table}
    </section>
    """


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reporte de negocio — e-commerce</title>
<style>
  :root {{
    --bg: {bg}; --card: {card}; --border: {border};
    --text: {text}; --muted: {muted}; --accent: {accent}; --accent-soft: {accent_soft};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    color: var(--text);
    background: var(--bg);
    margin: 0;
    line-height: 1.5;
  }}
  .wrap {{ max-width: 880px; margin: 0 auto; padding: 48px 24px 80px; }}
  header.page-header {{ margin-bottom: 32px; }}
  h1 {{ font-size: 1.5rem; margin: 0 0 4px; letter-spacing: -0.01em; }}
  .meta {{ color: var(--muted); font-size: 0.88rem; margin: 0; }}
  nav.toc {{ display: flex; gap: 8px; margin-top: 20px; flex-wrap: wrap; }}
  nav.toc a {{
    color: var(--accent); text-decoration: none; font-size: 0.85rem; font-weight: 600;
    background: var(--accent-soft); padding: 6px 14px; border-radius: 999px;
  }}
  nav.toc a:hover {{ opacity: 0.85; }}
  .card {{
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 28px 28px 20px; margin-bottom: 20px;
  }}
  h2 {{ font-size: 1.15rem; margin: 0 0 6px; }}
  .intro {{ color: var(--muted); margin: 0 0 18px; font-size: 0.93rem; max-width: 60ch; }}
  .kpis {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }}
  .kpi {{
    flex: 1 1 140px; border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 16px; background: #fcfdfc;
  }}
  .kpi-value {{ font-size: 1.4rem; font-weight: 700; color: var(--accent); }}
  .kpi-label {{ font-size: 0.78rem; color: var(--muted); margin-top: 2px; }}
  img {{ max-width: 100%; display: block; margin: 4px 0 16px; }}
  details.detail summary {{
    cursor: pointer; color: var(--accent); font-size: 0.85rem; font-weight: 600;
    margin-bottom: 8px; outline: none;
  }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; }}
  th, td {{ text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.03em; }}
  tbody tr:hover {{ background: #fafbfa; }}
  footer {{ margin-top: 40px; color: var(--muted); font-size: 0.8rem; border-top: 1px solid var(--border); padding-top: 16px; }}
</style>
</head>
<body>
  <div class="wrap">
    <header class="page-header">
      <h1>Reporte de negocio — e-commerce</h1>
      <p class="meta">Generado el {generated_at} a partir de marts.* (staging/marts construidos con dbt sobre raw).</p>
      <nav class="toc">
        <a href="#clientes">Clientes</a>
        <a href="#ventas">Ventas</a>
        <a href="#ingresos">Ingresos</a>
        <a href="#ordenes">Órdenes</a>
      </nav>
    </header>
    {sections}
    <footer>Pipeline: raw (ecommerce.duckdb) → staging → marts (dbt-duckdb, warehouse.duckdb) → este reporte.</footer>
  </div>
</body>
</html>
"""


def main():
    con = duckdb.connect(str(WAREHOUSE_PATH), read_only=True)
    sections = "".join([
        section_clientes(con),
        section_ventas(con),
        section_ingresos(con),
        section_ordenes(con),
    ])
    con.close()

    html = PAGE_TEMPLATE.format(
        sections=sections,
        generated_at=dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        **COLORS,
    )
    OUTPUT_PATH.write_text(html)
    print(f"Reporte generado en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
