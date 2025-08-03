import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from db import fetchall, get_conn

st.set_page_config(page_title="Automação", layout="wide")
st.title("🤖 Automação - Descontos e Rotinas")

st.markdown("""
Esta página automatiza rotinas do brechó:
- **Atualização automática de descontos** por tempo
- **Identificação de itens parados**
- **Sugestões de ações**
""")

st.divider()

# Automatic markdown updates
st.subheader("🏷️ Atualização Automática de Descontos")

st.markdown("""
**Política atual:**
- 0-30 dias: Preço cheio (0%)
- 31-60 dias: 1º desconto (-10%)
- 61-90 dias: 2º desconto (-25%)
- 90+ dias: 3º desconto (-40%)
""")

def update_markdown_stages():
    """Update markdown stages based on days since listing"""
    with get_conn() as conn:
        # Items that should move to stage 1 (10% off)
        conn.execute("""
            UPDATE items 
            SET markdown_stage = 1 
            WHERE active = 1 
              AND sold_at IS NULL 
              AND markdown_stage = 0 
              AND julianday('now') - julianday(listed_at) > 30
        """)
        stage1_updates = conn.total_changes
        
        # Items that should move to stage 2 (25% off)
        conn.execute("""
            UPDATE items 
            SET markdown_stage = 2 
            WHERE active = 1 
              AND sold_at IS NULL 
              AND markdown_stage = 1 
              AND julianday('now') - julianday(listed_at) > 60
        """)
        stage2_updates = conn.total_changes - stage1_updates
        
        # Items that should move to stage 3 (40% off)
        conn.execute("""
            UPDATE items 
            SET markdown_stage = 3 
            WHERE active = 1 
              AND sold_at IS NULL 
              AND markdown_stage = 2 
              AND julianday('now') - julianday(listed_at) > 90
        """)
        stage3_updates = conn.total_changes - stage1_updates - stage2_updates
        
        return stage1_updates, stage2_updates, stage3_updates

# Check items pending markdown updates
_, pending_updates = fetchall("""
    SELECT 
        CASE 
            WHEN julianday('now') - julianday(listed_at) > 90 AND markdown_stage < 3 THEN 'Para 40% OFF'
            WHEN julianday('now') - julianday(listed_at) > 60 AND markdown_stage < 2 THEN 'Para 25% OFF'
            WHEN julianday('now') - julianday(listed_at) > 30 AND markdown_stage < 1 THEN 'Para 10% OFF'
            ELSE 'OK'
        END as update_needed,
        COUNT(*) as qty
    FROM items 
    WHERE active = 1 AND sold_at IS NULL
    GROUP BY update_needed
    HAVING update_needed != 'OK'
    ORDER BY qty DESC
""")

if pending_updates:
    st.warning(f"⚠️ **{sum(qty for _, qty in pending_updates)} itens** precisam de atualização de desconto:")
    for update_type, qty in pending_updates:
        st.write(f"• {qty} itens {update_type}")
    
    if st.button("🔄 Atualizar Descontos Automaticamente", type="primary"):
        stage1, stage2, stage3 = update_markdown_stages()
        total_updated = stage1 + stage2 + stage3
        if total_updated > 0:
            st.success(f"✅ Atualizados {total_updated} itens:")
            if stage1 > 0:
                st.write(f"• {stage1} itens → 10% OFF")
            if stage2 > 0:
                st.write(f"• {stage2} itens → 25% OFF")
            if stage3 > 0:
                st.write(f"• {stage3} itens → 40% OFF")
        else:
            st.info("Nenhum item foi atualizado.")
else:
    st.success("✅ Todos os itens estão com desconto correto!")

st.divider()

# Slow movers analysis
st.subheader("🐌 Itens com Baixa Rotação")

col1, col2 = st.columns(2)

with col1:
    st.write("**Itens há mais de 90 dias (candidatos a bundle/doação):**")
    _, very_slow = fetchall("""
        SELECT sku, category, brand, size, 
               julianday('now') - julianday(listed_at) as days_listed,
               list_price, markdown_stage
        FROM items 
        WHERE active = 1 AND sold_at IS NULL 
          AND julianday('now') - julianday(listed_at) > 90
        ORDER BY days_listed DESC
        LIMIT 20
    """)
    
    if very_slow:
        df_slow = pd.DataFrame(very_slow, columns=[
            'SKU', 'Categoria', 'Marca', 'Tamanho', 'Dias', 'Preço', 'Desconto'
        ])
        df_slow['Dias'] = df_slow['Dias'].round(0).astype(int)
        df_slow['Desconto'] = df_slow['Desconto'].map({
            0: '0%', 1: '10%', 2: '25%', 3: '40%'
        })
        st.dataframe(df_slow, use_container_width=True)
        
        # Suggest bundle pricing
        st.info("💡 **Sugestão:** Agrupe estes itens em promoções tipo '3 por R$ X' ou '5 por R$ Y'")
    else:
        st.success("Nenhum item há mais de 90 dias!")

with col2:
    st.write("**Categorias com maior acúmulo de estoque:**")
    _, category_stock = fetchall("""
        SELECT category, 
               COUNT(*) as total_items,
               COUNT(CASE WHEN julianday('now') - julianday(listed_at) > 60 THEN 1 END) as old_items,
               ROUND(COUNT(CASE WHEN julianday('now') - julianday(listed_at) > 60 THEN 1 END) * 100.0 / COUNT(*), 1) as old_pct
        FROM items 
        WHERE active = 1 AND sold_at IS NULL
        GROUP BY category
        HAVING total_items > 5
        ORDER BY old_pct DESC, total_items DESC
    """)
    
    if category_stock:
        df_cat_stock = pd.DataFrame(category_stock, columns=[
            'Categoria', 'Total', 'Itens Antigos (60+ dias)', '% Antigos'
        ])
        st.dataframe(df_cat_stock, use_container_width=True)
        
        # Highlight problematic categories
        problem_categories = df_cat_stock[df_cat_stock['% Antigos'] > 50]
        if not problem_categories.empty:
            st.warning("⚠️ **Categorias com alta % de itens antigos:**")
            for _, row in problem_categories.iterrows():
                st.write(f"• {row['Categoria']}: {row['% Antigos']}% antigos")

st.divider()

# Inventory management suggestions
st.subheader("📦 Sugestões de Gestão de Estoque")

col1, col2 = st.columns(2)

with col1:
    st.write("**🔥 Categorias/Tamanhos com Alta Rotação (foque na aquisição):**")
    _, high_demand = fetchall("""
        SELECT i.category, i.size, 
               COUNT(*) as total_sold,
               AVG(julianday(s.date) - julianday(i.listed_at)) as avg_days_to_sell
        FROM sales s
        JOIN items i ON s.sku = i.sku
        WHERE s.date >= date('now', '-30 days')
        GROUP BY i.category, i.size
        HAVING total_sold >= 3 AND avg_days_to_sell <= 14
        ORDER BY total_sold DESC, avg_days_to_sell ASC
        LIMIT 10
    """)
    
    if high_demand:
        df_demand = pd.DataFrame(high_demand, columns=[
            'Categoria', 'Tamanho', 'Vendas (30d)', 'Dias Médios'
        ])
        df_demand['Dias Médios'] = df_demand['Dias Médios'].round(1)
        st.dataframe(df_demand, use_container_width=True)
        st.info("💡 Priorize a aquisição dessas combinações categoria+tamanho")
    else:
        st.info("Dados insuficientes para análise de alta demanda")

with col2:
    st.write("**❄️ Combinações com Baixa Demanda (evite aquisição):**")
    _, low_demand = fetchall("""
        SELECT category, size, 
               COUNT(*) as current_stock,
               COUNT(CASE WHEN sold_at IS NOT NULL THEN 1 END) as sold_ever,
               AVG(CASE WHEN sold_at IS NOT NULL 
                   THEN julianday(sold_at) - julianday(listed_at) END) as avg_days_when_sold
        FROM items 
        WHERE listed_at >= date('now', '-90 days')
        GROUP BY category, size
        HAVING current_stock >= 3 
           AND (sold_ever = 0 OR avg_days_when_sold > 45)
        ORDER BY current_stock DESC
        LIMIT 10
    """)
    
    if low_demand:
        df_low = pd.DataFrame(low_demand, columns=[
            'Categoria', 'Tamanho', 'Estoque Atual', 'Vendas Históricas', 'Dias p/ Vender'
        ])
        df_low['Dias p/ Vender'] = df_low['Dias p/ Vender'].fillna(0).round(1)
        st.dataframe(df_low, use_container_width=True)
        st.warning("⚠️ Evite adquirir mais itens dessas combinações")
    else:
        st.success("Não há combinações problemáticas identificadas")

st.divider()

# Consignor performance
st.subheader("👥 Performance dos Consignantes")

_, consignor_perf = fetchall("""
    SELECT c.name,
           COUNT(CASE WHEN i.listed_at >= date('now', '-30 days') THEN 1 END) as items_added_30d,
           COUNT(CASE WHEN s.date >= date('now', '-30 days') THEN 1 END) as items_sold_30d,
           ROUND(COUNT(CASE WHEN s.date >= date('now', '-30 days') THEN 1 END) * 100.0 / 
                 NULLIF(COUNT(CASE WHEN i.listed_at >= date('now', '-30 days') THEN 1 END), 0), 1) as sell_through_rate,
           SUM(CASE WHEN s.date >= date('now', '-30 days') 
               THEN s.sale_price - COALESCE(s.discount_value, 0) END) as revenue_30d
    FROM consignors c
    LEFT JOIN items i ON c.id = i.consignor_id
    LEFT JOIN sales s ON i.sku = s.sku
    WHERE c.active = 1
    GROUP BY c.id, c.name
    HAVING items_added_30d > 0 OR items_sold_30d > 0
    ORDER BY sell_through_rate DESC NULLS LAST, revenue_30d DESC NULLS LAST
""")

if consignor_perf:
    df_perf = pd.DataFrame(consignor_perf, columns=[
        'Consignante', 'Itens Adicionados (30d)', 'Itens Vendidos (30d)', 
        'Taxa de Venda (%)', 'Receita (30d)'
    ])
    df_perf['Taxa de Venda (%)'] = df_perf['Taxa de Venda (%)'].fillna(0)
    df_perf['Receita (30d)'] = df_perf['Receita (30d)'].fillna(0)
    
    st.dataframe(df_perf, use_container_width=True)
    
    # Identify top and bottom performers
    top_performers = df_perf[df_perf['Taxa de Venda (%)'] >= 50].head(3)
    if not top_performers.empty:
        st.success("🏆 **Top performers (taxa ≥ 50%):**")
        for _, row in top_performers.iterrows():
            st.write(f"• {row['Consignante']}: {row['Taxa de Venda (%)']}% de taxa de venda")
    
    low_performers = df_perf[(df_perf['Itens Adicionados (30d)'] >= 5) & 
                            (df_perf['Taxa de Venda (%)'] < 20)].head(3)
    if not low_performers.empty:
        st.warning("⚠️ **Consignantes com baixa performance (≥5 itens, <20% vendas):**")
        for _, row in low_performers.iterrows():
            st.write(f"• {row['Consignante']}: {row['Taxa de Venda (%)']}% de taxa de venda")

st.divider()

# Automated actions summary
st.subheader("📋 Resumo de Ações Sugeridas")

actions = []

# Check for markdown updates needed
_, markdown_check = fetchall("""
    SELECT COUNT(*) FROM items 
    WHERE active = 1 AND sold_at IS NULL 
      AND ((julianday('now') - julianday(listed_at) > 30 AND markdown_stage = 0)
           OR (julianday('now') - julianday(listed_at) > 60 AND markdown_stage = 1)
           OR (julianday('now') - julianday(listed_at) > 90 AND markdown_stage = 2))
""")
markdown_pending = markdown_check[0][0] if markdown_check else 0
if markdown_pending > 0:
    actions.append(f"🏷️ Atualizar desconto de {markdown_pending} itens")

# Check for very old items
_, old_items_check = fetchall("""
    SELECT COUNT(*) FROM items 
    WHERE active = 1 AND sold_at IS NULL 
      AND julianday('now') - julianday(listed_at) > 90
""")
old_items = old_items_check[0][0] if old_items_check else 0
if old_items > 10:
    actions.append(f"📦 Considerar bundle/doação de {old_items} itens antigos (>90 dias)")

# Check for overstocked categories
_, overstock_check = fetchall("""
    SELECT COUNT(DISTINCT category) FROM (
        SELECT category, COUNT(*) as qty
        FROM items 
        WHERE active = 1 AND sold_at IS NULL
        GROUP BY category
        HAVING qty > 20
    )
""")
overstock_cats = overstock_check[0][0] if overstock_check else 0
if overstock_cats > 0:
    actions.append(f"⚠️ {overstock_cats} categorias com estoque alto (>20 itens)")

if actions:
    st.markdown("**Ações prioritárias para hoje:**")
    for action in actions:
        st.write(f"• {action}")
else:
    st.success("✅ Nenhuma ação urgente identificada. Estoque bem gerido!")

# Automation settings
st.divider()
st.subheader("⚙️ Configurações de Automação")

st.markdown("""
**Para implementar em versões futuras:**
- [ ] Atualização automática de descontos (execução diária)
- [ ] Alertas por WhatsApp para itens que precisam de ação
- [ ] Sugestões automáticas de preço baseadas em performance
- [ ] Notificações para consignantes sobre itens vendidos
- [ ] Backup automático do banco de dados
""")

# Manual backup option
if st.button("💾 Fazer Backup Manual do Banco"):
    import shutil
    from datetime import datetime
    
    backup_name = f"brecho_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        shutil.copy2("brecho.db", backup_name)
        st.success(f"✅ Backup criado: {backup_name}")
        
        # Offer download
        with open(backup_name, "rb") as f:
            st.download_button(
                "📥 Baixar Backup",
                f.read(),
                file_name=backup_name,
                mime="application/octet-stream"
            )
    except Exception as e:
        st.error(f"Erro ao criar backup: {e}")
