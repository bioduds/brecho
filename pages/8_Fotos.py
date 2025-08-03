import streamlit as st
import os
from pathlib import Path
import pandas as pd
from PIL import Image
import io
from db import fetchall, upsert

st.set_page_config(page_title="Fotos", layout="wide")
st.title("📸 Gestão de Fotos dos Itens")

# Create photos directory if it doesn't exist
PHOTOS_DIR = Path("photos")
PHOTOS_DIR.mkdir(exist_ok=True)

st.markdown("""
Faça upload e gerencie fotos dos itens para usar no Instagram e vendas online.
**Formato recomendado:** 3 fotos por item (frontal, lateral, detalhe/defeito)
""")

st.divider()

# Photo upload section
st.subheader("📤 Upload de Fotos")

col1, col2 = st.columns([1, 2])

with col1:
    # Select item to add photos
    _, items_data = fetchall("""
        SELECT sku, category, brand, size, consignor_id 
        FROM items 
        WHERE active = 1 AND sold_at IS NULL
        ORDER BY listed_at DESC
        LIMIT 100
    """)
    
    if items_data:
        items_options = [f"{row[0]} - {row[1]} {row[2] or ''} {row[3] or ''}".strip() 
                        for row in items_data]
        selected_item = st.selectbox("Selecione o item:", [""] + items_options)
        
        if selected_item:
            selected_sku = selected_item.split(" - ")[0]
            
            # File uploader
            uploaded_files = st.file_uploader(
                "Escolha as fotos (máx. 5):",
                type=['png', 'jpg', 'jpeg'],
                accept_multiple_files=True,
                key="photo_upload"
            )
            
            if uploaded_files and len(uploaded_files) <= 5:
                st.success(f"✅ {len(uploaded_files)} foto(s) selecionada(s)")
                
                if st.button("💾 Salvar Fotos", type="primary"):
                    # Create folder for this SKU
                    sku_folder = PHOTOS_DIR / selected_sku
                    sku_folder.mkdir(exist_ok=True)
                    
                    saved_files = []
                    for i, uploaded_file in enumerate(uploaded_files):
                        # Save file
                        file_extension = uploaded_file.name.split('.')[-1].lower()
                        filename = f"{selected_sku}_{i+1}.{file_extension}"
                        file_path = sku_folder / filename
                        
                        # Resize and save image
                        img = Image.open(uploaded_file)
                        # Resize for social media (max 1080px)
                        img.thumbnail((1080, 1080), Image.Resampling.LANCZOS)
                        img.save(file_path, optimize=True, quality=85)
                        saved_files.append(str(file_path))
                    
                    # Update item with photos path
                    photos_url = str(sku_folder)
                    _, current_item = fetchall("SELECT * FROM items WHERE sku = ?", (selected_sku,))
                    if current_item:
                        item_data = dict(zip([
                            'sku', 'consignor_id', 'acquisition_type', 'category', 'subcategory',
                            'brand', 'gender', 'size', 'fit', 'color', 'fabric', 'condition',
                            'flaws', 'bust', 'waist', 'length', 'cost', 'list_price',
                            'markdown_stage', 'acquired_at', 'listed_at', 'channel_listed',
                            'sold_at', 'sale_price', 'channel_sold', 'days_on_hand',
                            'photos_url', 'notes', 'active'
                        ], current_item[0]))
                        item_data['photos_url'] = photos_url
                        upsert("items", "sku", item_data)
                    
                    st.success(f"✅ {len(saved_files)} fotos salvas para {selected_sku}")
            
            elif uploaded_files and len(uploaded_files) > 5:
                st.error("❌ Máximo 5 fotos por item")
    else:
        st.info("Nenhum item ativo encontrado")

with col2:
    # Preview uploaded photos
    if 'uploaded_files' in locals() and uploaded_files:
        st.write("**Preview das fotos:**")
        cols = st.columns(min(len(uploaded_files), 3))
        for i, uploaded_file in enumerate(uploaded_files):
            with cols[i % 3]:
                img = Image.open(uploaded_file)
                st.image(img, caption=f"Foto {i+1}", use_container_width=True)

st.divider()

# Photo gallery section
st.subheader("🖼️ Galeria de Fotos dos Itens")

# Filter options
col1, col2, col3 = st.columns(3)
with col1:
    filter_category = st.selectbox("Filtrar por categoria:", 
                                  ["Todas"] + ["Vestido", "Camisa", "Camiseta", "Calça", 
                                              "Jeans", "Saia", "Blazer", "Casaco", "Short", 
                                              "Macacão", "Sapato", "Bolsa", "Acessório"])
with col2:
    filter_brand = st.text_input("Filtrar por marca:")
with col3:
    show_only_with_photos = st.checkbox("Apenas itens com fotos", value=False)

# Get items with photos
query = """
    SELECT sku, category, brand, size, condition, list_price, markdown_stage, photos_url
    FROM items 
    WHERE active = 1 AND sold_at IS NULL
"""
params = []

if filter_category != "Todas":
    query += " AND category = ?"
    params.append(filter_category)

if filter_brand:
    query += " AND brand LIKE ?"
    params.append(f"%{filter_brand}%")

if show_only_with_photos:
    query += " AND photos_url IS NOT NULL AND photos_url != ''"

query += " ORDER BY listed_at DESC"

_, gallery_items = fetchall(query, params)

if gallery_items:
    # Display items in grid
    items_per_row = 3
    for i in range(0, len(gallery_items), items_per_row):
        cols = st.columns(items_per_row)
        for j in range(items_per_row):
            if i + j < len(gallery_items):
                item = gallery_items[i + j]
                sku, category, brand, size, condition, list_price, markdown_stage, photos_url = item
                
                with cols[j]:
                    st.write(f"**{sku}**")
                    st.write(f"{category} {brand or ''} {size or ''}".strip())
                    st.write(f"Condição: {condition}")
                    
                    # Calculate current price
                    discount_pct = {0: 0, 1: 0.10, 2: 0.25, 3: 0.40}.get(markdown_stage, 0)
                    current_price = list_price * (1 - discount_pct)
                    
                    if discount_pct > 0:
                        st.write(f"~~R$ {list_price:.2f}~~ **R$ {current_price:.2f}**")
                        st.write(f"🏷️ {int(discount_pct * 100)}% OFF")
                    else:
                        st.write(f"**R$ {current_price:.2f}**")
                    
                    # Show photos if available
                    if photos_url and Path(photos_url).exists():
                        photo_files = list(Path(photos_url).glob("*.jpg")) + \
                                     list(Path(photos_url).glob("*.jpeg")) + \
                                     list(Path(photos_url).glob("*.png"))
                        
                        if photo_files:
                            # Show first photo as thumbnail
                            try:
                                img = Image.open(photo_files[0])
                                st.image(img, use_container_width=True)
                                
                                # Button to view all photos
                                if st.button(f"Ver todas ({len(photo_files)})", key=f"view_{sku}"):
                                    st.session_state[f"show_photos_{sku}"] = True
                                
                                # Show all photos in expander if requested
                                if st.session_state.get(f"show_photos_{sku}", False):
                                    with st.expander(f"Todas as fotos de {sku}", expanded=True):
                                        for photo_file in photo_files:
                                            img = Image.open(photo_file)
                                            st.image(img, caption=photo_file.name, use_container_width=True)
                                        if st.button("Fechar", key=f"close_{sku}"):
                                            st.session_state[f"show_photos_{sku}"] = False
                                            st.rerun()
                                            
                            except Exception as e:
                                st.error(f"Erro ao carregar foto: {e}")
                        else:
                            st.info("📁 Pasta criada, sem fotos")
                    else:
                        st.warning("📷 Sem fotos")
                        if st.button(f"Adicionar fotos", key=f"add_{sku}"):
                            st.session_state['photo_upload'] = None  # Reset uploader
                            st.rerun()
                    
                    st.divider()
else:
    st.info("Nenhum item encontrado com os filtros aplicados")

st.divider()

# Photo statistics
st.subheader("📊 Estatísticas de Fotos")

col1, col2, col3 = st.columns(3)

# Count items with and without photos
_, photo_stats = fetchall("""
    SELECT 
        COUNT(*) as total_items,
        COUNT(CASE WHEN photos_url IS NOT NULL AND photos_url != '' THEN 1 END) as with_photos,
        COUNT(CASE WHEN photos_url IS NULL OR photos_url = '' THEN 1 END) as without_photos
    FROM items 
    WHERE active = 1 AND sold_at IS NULL
""")

if photo_stats:
    total, with_photos, without_photos = photo_stats[0]
    
    with col1:
        st.metric("Total de Itens", total)
    
    with col2:
        st.metric("Com Fotos", with_photos, 
                 help=f"{(with_photos/total*100):.1f}% do estoque" if total > 0 else "")
    
    with col3:
        st.metric("Sem Fotos", without_photos,
                 help=f"{(without_photos/total*100):.1f}% do estoque" if total > 0 else "")

# Photo coverage by category
st.write("**Cobertura de fotos por categoria:**")
_, category_photos = fetchall("""
    SELECT category,
           COUNT(*) as total,
           COUNT(CASE WHEN photos_url IS NOT NULL AND photos_url != '' THEN 1 END) as with_photos,
           ROUND(COUNT(CASE WHEN photos_url IS NOT NULL AND photos_url != '' THEN 1 END) * 100.0 / COUNT(*), 1) as coverage_pct
    FROM items 
    WHERE active = 1 AND sold_at IS NULL
    GROUP BY category
    ORDER BY coverage_pct ASC, total DESC
""")

if category_photos:
    df_coverage = pd.DataFrame(category_photos, columns=[
        'Categoria', 'Total', 'Com Fotos', 'Cobertura (%)'
    ])
    st.dataframe(df_coverage, use_container_width=True)
    
    # Highlight categories that need photos
    low_coverage = df_coverage[(df_coverage['Total'] >= 3) & (df_coverage['Cobertura (%)'] < 50)]
    if not low_coverage.empty:
        st.warning("⚠️ **Categorias que precisam de mais fotos:**")
        for _, row in low_coverage.iterrows():
            st.write(f"• {row['Categoria']}: {row['Cobertura (%)']}% ({row['Com Fotos']}/{row['Total']} itens)")

st.divider()

# Bulk operations
st.subheader("🔧 Operações em Lote")

col1, col2 = st.columns(2)

with col1:
    st.write("**Gerar lista para fotografia:**")
    priority_filter = st.selectbox("Prioridade:", [
        "Todos sem foto",
        "Itens novos (< 30 dias) sem foto", 
        "Itens de maior valor sem foto",
        "Categorias específicas sem foto"
    ])
    
    if st.button("📋 Gerar Lista"):
        if priority_filter == "Todos sem foto":
            query = """
                SELECT sku, category, brand, size, list_price
                FROM items 
                WHERE active = 1 AND sold_at IS NULL 
                  AND (photos_url IS NULL OR photos_url = '')
                ORDER BY list_price DESC
            """
        elif priority_filter == "Itens novos (< 30 dias) sem foto":
            query = """
                SELECT sku, category, brand, size, list_price
                FROM items 
                WHERE active = 1 AND sold_at IS NULL 
                  AND (photos_url IS NULL OR photos_url = '')
                  AND julianday('now') - julianday(listed_at) <= 30
                ORDER BY listed_at DESC
            """
        elif priority_filter == "Itens de maior valor sem foto":
            query = """
                SELECT sku, category, brand, size, list_price
                FROM items 
                WHERE active = 1 AND sold_at IS NULL 
                  AND (photos_url IS NULL OR photos_url = '')
                  AND list_price >= 50
                ORDER BY list_price DESC
            """
        else:  # Categories
            query = """
                SELECT sku, category, brand, size, list_price
                FROM items 
                WHERE active = 1 AND sold_at IS NULL 
                  AND (photos_url IS NULL OR photos_url = '')
                  AND category IN ('Vestido', 'Blazer', 'Casaco', 'Bolsa')
                ORDER BY category, list_price DESC
            """
        
        _, photo_list = fetchall(query)
        if photo_list:
            df_list = pd.DataFrame(photo_list, columns=[
                'SKU', 'Categoria', 'Marca', 'Tamanho', 'Preço'
            ])
            st.dataframe(df_list, use_container_width=True)
            
            # Download as CSV
            csv = df_list.to_csv(index=False)
            st.download_button(
                "📥 Baixar lista (CSV)",
                csv.encode('utf-8'),
                "lista_fotografias.csv",
                "text/csv"
            )
        else:
            st.success("✅ Todos os itens já têm fotos!")

with col2:
    st.write("**Limpeza de arquivos órfãos:**")
    if st.button("🧹 Verificar Arquivos Não Utilizados"):
        # Find photo folders that don't correspond to active items
        _, active_skus = fetchall("SELECT sku FROM items WHERE active = 1")
        active_sku_set = {sku[0] for sku in active_skus}
        
        orphaned_folders = []
        if PHOTOS_DIR.exists():
            for folder in PHOTOS_DIR.iterdir():
                if folder.is_dir() and folder.name not in active_sku_set:
                    orphaned_folders.append(folder.name)
        
        if orphaned_folders:
            st.warning(f"⚠️ {len(orphaned_folders)} pastas órfãs encontradas:")
            for folder in orphaned_folders[:10]:  # Show first 10
                st.write(f"• {folder}")
            if len(orphaned_folders) > 10:
                st.write(f"... e mais {len(orphaned_folders) - 10}")
            
            st.info("💡 Considere remover manualmente pastas de itens inativos ou vendidos")
        else:
            st.success("✅ Nenhuma pasta órfã encontrada")

# Tips section
st.divider()
st.subheader("💡 Dicas para Fotografia")

st.markdown("""
**📸 Qualidade das fotos:**
- Use luz natural (próximo à janela)
- Fundo neutro (branco ou cinza claro)  
- 3 ângulos: frontal, lateral, detalhe/defeito
- Resolução mínima: 800x800px

**📱 Para Instagram:**
- Formato quadrado (1:1) funciona melhor
- Use hashtags locais: #brechobh #belohorizonte #moda
- Poste no horário de maior engajamento (18h-21h)

**⚡ Produtividade:**
- Fotografe vários itens da mesma categoria juntos
- Use manequim ou cabide para consistência
- Prepare todos os itens antes de começar a fotografar
""")
