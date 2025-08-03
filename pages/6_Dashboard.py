import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from db import fetchall

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Dashboard - KPIs do Brechó")

# Date range selector
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Data início", value=datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("Data fim", value=datetime.now())

st.divider()

# Key metrics cards
def get_kpi_data():
    # Total items in stock
    _, stock_rows = fetchall("SELECT COUNT(*) FROM items WHERE active=1 AND sold_at IS NULL")
    total_stock = stock_rows[0][0] if stock_rows else 0
    
    # Sales in period
    _, sales_rows = fetchall("""
        SELECT COUNT(*), SUM(sale_price - COALESCE(discount_value,0)) 
        FROM sales 
        WHERE date >= ? AND date <= ?
    """, (str(start_date), str(end_date)))
    period_sales_count = sales_rows[0][0] if sales_rows and sales_rows[0][0] else 0
    period_revenue = sales_rows[0][1] if sales_rows and sales_rows[0][1] else 0
    
    # Sell-through rate (items sold vs listed in period)
    _, listed_rows = fetchall("""
        SELECT COUNT(*) FROM items 
        WHERE listed_at >= ? AND listed_at <= ?
    """, (str(start_date), str(end_date)))
    period_listed = listed_rows[0][0] if listed_rows else 0
    sell_through_rate = (period_sales_count / period_listed * 100) if period_listed > 0 else 0
    
    # Average days to sell
    _, days_rows = fetchall("""
        SELECT AVG(julianday(s.date) - julianday(i.listed_at)) as avg_days
        FROM sales s
        JOIN items i ON s.sku = i.sku
        WHERE s.date >= ? AND s.date <= ?
    """, (str(start_date), str(end_date)))
    avg_days_to_sell = days_rows[0][0] if days_rows and days_rows[0][0] else 0
    
    return total_stock, period_sales_count, period_revenue, sell_through_rate, avg_days_to_sell

total_stock, period_sales_count, period_revenue, sell_through_rate, avg_days_to_sell = get_kpi_data()

# KPI Cards
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Estoque Atual", f"{total_stock:,}", help="Total de itens ativos não vendidos")
    
with col2:
    st.metric("Vendas (Período)", f"{period_sales_count:,}", help="Quantidade vendida no período")
    
with col3:
    st.metric("Receita (Período)", f"R$ {period_revenue:,.2f}", help="Receita líquida no período")
    
with col4:
    st.metric("Taxa de Venda", f"{sell_through_rate:.1f}%", help="% de itens vendidos vs listados no período")
    
with col5:
    st.metric("Dias p/ Vender", f"{avg_days_to_sell:.1f}", help="Tempo médio para venda")

st.divider()

# Charts section
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Vendas por Categoria")
    _, cat_sales = fetchall("""
        SELECT i.category, COUNT(*) as qty, SUM(s.sale_price - COALESCE(s.discount_value,0)) as revenue
        FROM sales s
        JOIN items i ON s.sku = i.sku
        WHERE s.date >= ? AND s.date <= ?
        GROUP BY i.category
        ORDER BY revenue DESC
    """, (str(start_date), str(end_date)))
    
    if cat_sales:
        df_cat = pd.DataFrame(cat_sales, columns=['Categoria', 'Quantidade', 'Receita'])
        fig_cat = px.bar(df_cat, x='Categoria', y='Receita', 
                        title="Receita por Categoria",
                        labels={'Receita': 'Receita (R$)'})
        fig_cat.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("Sem vendas no período selecionado")

with col2:
    st.subheader("📊 Análise ABC (Top Categorias)")
    if cat_sales:
        df_abc = pd.DataFrame(cat_sales, columns=['Categoria', 'Quantidade', 'Receita'])
        df_abc['Percentual'] = (df_abc['Receita'] / df_abc['Receita'].sum() * 100).round(1)
        df_abc['Acumulado'] = df_abc['Percentual'].cumsum()
        
        # Classify ABC
        df_abc['Classe'] = df_abc['Acumulado'].apply(
            lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C')
        )
        
        fig_abc = px.bar(df_abc, x='Categoria', y='Percentual', color='Classe',
                        title="Análise ABC - % da Receita",
                        color_discrete_map={'A': '#1f77b4', 'B': '#ff7f0e', 'C': '#d62728'})
        fig_abc.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_abc, use_container_width=True)
        
        # ABC Summary
        st.write("**Resumo ABC:**")
        abc_summary = df_abc.groupby('Classe').agg({
            'Categoria': 'count',
            'Receita': 'sum',
            'Percentual': 'sum'
        }).round(2)
        st.dataframe(abc_summary)

st.divider()

# Size coverage matrix
st.subheader("📏 Matriz Categoria × Tamanho (Taxa de Venda)")
_, size_data = fetchall("""
    SELECT i.category, i.size, 
           COUNT(CASE WHEN s.sku IS NOT NULL THEN 1 END) as sold,
           COUNT(*) as total,
           ROUND(COUNT(CASE WHEN s.sku IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as rate
    FROM items i
    LEFT JOIN sales s ON i.sku = s.sku 
        AND s.date >= ? AND s.date <= ?
    WHERE i.listed_at >= ?
    GROUP BY i.category, i.size
    HAVING COUNT(*) >= 2
    ORDER BY i.category, i.size
""", (str(start_date), str(end_date), str(start_date)))

if size_data:
    df_size = pd.DataFrame(size_data, columns=['Categoria', 'Tamanho', 'Vendido', 'Total', 'Taxa'])
    
    # Create pivot table
    pivot_size = df_size.pivot(index='Categoria', columns='Tamanho', values='Taxa').fillna(0)
    
    # Create heatmap
    fig_heatmap = px.imshow(pivot_size, 
                           labels=dict(x="Tamanho", y="Categoria", color="Taxa de Venda (%)"),
                           title="Taxa de Venda por Categoria e Tamanho",
                           color_continuous_scale="RdYlGn",
                           text_auto=True)
    fig_heatmap.update_layout(height=400)
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    st.info("💡 **Dica:** Células vermelhas indicam baixa rotatividade (considere reduzir compras). Células verdes indicam alta demanda (foque na aquisição).")

st.divider()

# Markdown stage analysis
st.subheader("🏷️ Análise de Descontos")
col1, col2 = st.columns(2)

with col1:
    st.write("**Estoque por Etapa de Desconto:**")
    _, markdown_stock = fetchall("""
        SELECT markdown_stage,
               CASE markdown_stage 
                   WHEN 0 THEN 'Preço cheio (0%)'
                   WHEN 1 THEN '1º desconto (-10%)'
                   WHEN 2 THEN '2º desconto (-25%)'
                   WHEN 3 THEN '3º desconto (-40%)'
                   ELSE 'Outro'
               END as stage_name,
               COUNT(*) as qty,
               SUM(list_price * (1 - CASE markdown_stage 
                   WHEN 0 THEN 0.0 WHEN 1 THEN 0.10 
                   WHEN 2 THEN 0.25 WHEN 3 THEN 0.40 ELSE 0 END)) as current_value
        FROM items 
        WHERE active=1 AND sold_at IS NULL
        GROUP BY markdown_stage
        ORDER BY markdown_stage
    """)
    
    if markdown_stock:
        df_markdown = pd.DataFrame(markdown_stock, columns=['Stage', 'Etapa', 'Quantidade', 'Valor Atual'])
        fig_markdown = px.pie(df_markdown, values='Quantidade', names='Etapa',
                             title="Distribuição do Estoque por Desconto")
        st.plotly_chart(fig_markdown, use_container_width=True)

with col2:
    st.write("**Performance por Etapa:**")
    _, stage_performance = fetchall("""
        SELECT i.markdown_stage,
               CASE i.markdown_stage 
                   WHEN 0 THEN 'Preço cheio'
                   WHEN 1 THEN '1º desconto'
                   WHEN 2 THEN '2º desconto'
                   WHEN 3 THEN '3º desconto'
                   ELSE 'Outro'
               END as stage_name,
               COUNT(*) as sold_qty,
               AVG(julianday(s.date) - julianday(i.listed_at)) as avg_days
        FROM sales s
        JOIN items i ON s.sku = i.sku
        WHERE s.date >= ? AND s.date <= ?
        GROUP BY i.markdown_stage
        ORDER BY i.markdown_stage
    """, (str(start_date), str(end_date)))
    
    if stage_performance:
        df_perf = pd.DataFrame(stage_performance, columns=['Stage', 'Etapa', 'Vendas', 'Dias Médios'])
        st.dataframe(df_perf[['Etapa', 'Vendas', 'Dias Médios']], use_container_width=True)

st.divider()

# Top performers
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top Consignantes (Período)")
    _, top_consignors = fetchall("""
        SELECT c.name, 
               COUNT(*) as items_sold,
               SUM(s.sale_price - COALESCE(s.discount_value,0)) as total_revenue,
               AVG(s.sale_price - COALESCE(s.discount_value,0)) as avg_price
        FROM sales s
        JOIN consignors c ON s.consignor_id = c.id
        WHERE s.date >= ? AND s.date <= ?
        GROUP BY c.id, c.name
        ORDER BY total_revenue DESC
        LIMIT 10
    """, (str(start_date), str(end_date)))
    
    if top_consignors:
        df_top = pd.DataFrame(top_consignors, columns=['Consignante', 'Itens Vendidos', 'Receita Total', 'Preço Médio'])
        df_top['Receita Total'] = df_top['Receita Total'].apply(lambda x: f"R$ {x:.2f}")
        df_top['Preço Médio'] = df_top['Preço Médio'].apply(lambda x: f"R$ {x:.2f}")
        st.dataframe(df_top, use_container_width=True)

with col2:
    st.subheader("⚡ Itens de Rotação Rápida")
    _, fast_movers = fetchall("""
        SELECT i.sku, i.category, i.brand, i.size,
               julianday(s.date) - julianday(i.listed_at) as days_to_sell,
               s.sale_price - COALESCE(s.discount_value,0) as net_price
        FROM sales s
        JOIN items i ON s.sku = i.sku
        WHERE s.date >= ? AND s.date <= ?
          AND julianday(s.date) - julianday(i.listed_at) <= 7
        ORDER BY days_to_sell ASC
        LIMIT 10
    """, (str(start_date), str(end_date)))
    
    if fast_movers:
        df_fast = pd.DataFrame(fast_movers, columns=['SKU', 'Categoria', 'Marca', 'Tamanho', 'Dias p/ Vender', 'Preço Líquido'])
        df_fast['Dias p/ Vender'] = df_fast['Dias p/ Vender'].apply(lambda x: f"{x:.1f}")
        df_fast['Preço Líquido'] = df_fast['Preço Líquido'].apply(lambda x: f"R$ {x:.2f}")
        st.dataframe(df_fast, use_container_width=True)
        st.info("💡 **Dica:** Essas combinações categoria+marca+tamanho vendem rápido. Priorize na aquisição!")

# Action recommendations
st.divider()
st.subheader("🎯 Recomendações de Ação")

# Get slow movers
_, slow_movers = fetchall("""
    SELECT category, COUNT(*) as qty
    FROM items 
    WHERE active=1 AND sold_at IS NULL 
      AND julianday('now') - julianday(listed_at) > 60
      AND markdown_stage < 2
    GROUP BY category
    HAVING COUNT(*) > 0
    ORDER BY qty DESC
    LIMIT 5
""")

if slow_movers:
    st.warning("⚠️ **Itens parados há mais de 60 dias (considere aumentar desconto):**")
    for category, qty in slow_movers:
        st.write(f"• {category}: {qty} itens")

# Stock gaps
_, stock_gaps = fetchall("""
    SELECT category, size, COUNT(*) as current_stock
    FROM items 
    WHERE active=1 AND sold_at IS NULL
    GROUP BY category, size
    HAVING COUNT(*) < 3
    ORDER BY current_stock ASC
    LIMIT 10
""")

if stock_gaps:
    st.info("📦 **Categorias/tamanhos com baixo estoque (< 3 itens):**")
    for category, size, stock in stock_gaps:
        st.write(f"• {category} tamanho {size}: apenas {stock} item(s)")
