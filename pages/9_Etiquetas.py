import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
from db import fetchall
from utils import compute_markdown_price

st.set_page_config(page_title="Etiquetas", layout="wide")
st.title("🏷️ Gerador de Etiquetas")

st.markdown("""
Gere etiquetas profissionais para impressão térmica ou comum.
**Tamanhos suportados:** 58x40mm (térmica), 70x50mm, A4 (múltiplas etiquetas)
""")

st.divider()

# Label generation section
st.subheader("🖨️ Gerar Etiquetas")

col1, col2 = st.columns([1, 2])

with col1:
    # Label format selection
    label_format = st.selectbox("Formato da etiqueta:", [
        "58x40mm (Térmica pequena)",
        "70x50mm (Térmica padrão)", 
        "90x60mm (Etiqueta grande)",
        "A4 - Grade 2x4 (8 etiquetas)",
        "A4 - Grade 3x6 (18 etiquetas)"
    ])
    
    # Single item or batch
    generation_mode = st.radio("Modo:", ["Item único", "Lote de itens"])
    
    if generation_mode == "Item único":
        # Get items for single label
        _, items_data = fetchall("""
            SELECT sku, category, brand, size, condition, list_price, markdown_stage
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
                item_data = next((item for item in items_data if item[0] == selected_sku), None)
                
                if st.button("🏷️ Gerar Etiqueta", type="primary"):
                    label_img = generate_single_label(item_data, label_format)
                    if label_img:
                        st.session_state['generated_label'] = label_img
                        st.session_state['label_filename'] = f"etiqueta_{selected_sku}.png"
    
    else:  # Batch mode
        # Filters for batch generation
        category_filter = st.selectbox("Categoria (opcional):", 
                                      ["Todas"] + ["Vestido", "Camisa", "Camiseta", "Calça", 
                                                  "Jeans", "Saia", "Blazer", "Casaco", "Short", 
                                                  "Macacão", "Sapato", "Bolsa", "Acessório"])
        
        days_filter = st.selectbox("Itens listados em:", [
            "Qualquer período",
            "Últimos 7 dias",
            "Últimos 30 dias",
            "Últimos 3 meses"
        ])
        
        max_items = st.number_input("Máximo de etiquetas:", min_value=1, max_value=50, value=10)
        
        if st.button("🏷️ Gerar Etiquetas em Lote", type="primary"):
            # Build query based on filters
            query = """
                SELECT sku, category, brand, size, condition, list_price, markdown_stage
                FROM items 
                WHERE active = 1 AND sold_at IS NULL
            """
            params = []
            
            if category_filter != "Todas":
                query += " AND category = ?"
                params.append(category_filter)
            
            if days_filter != "Qualquer período":
                days_map = {
                    "Últimos 7 dias": 7,
                    "Últimos 30 dias": 30,
                    "Últimos 3 meses": 90
                }
                query += " AND julianday('now') - julianday(listed_at) <= ?"
                params.append(days_map[days_filter])
            
            query += f" ORDER BY listed_at DESC LIMIT {max_items}"
            
            _, batch_items = fetchall(query, params)
            if batch_items:
                if "A4" in label_format:
                    # Generate A4 sheet with multiple labels
                    labels_img = generate_a4_labels(batch_items, label_format)
                    if labels_img:
                        st.session_state['generated_label'] = labels_img
                        st.session_state['label_filename'] = f"etiquetas_lote_{len(batch_items)}.png"
                else:
                    # Generate individual labels as ZIP
                    st.info("💡 Para lotes grandes, recomendamos usar formato A4")
                    if len(batch_items) <= 10:
                        # Generate individual labels
                        label_images = []
                        for item in batch_items:
                            label_img = generate_single_label(item, label_format)
                            if label_img:
                                label_images.append((item[0], label_img))
                        
                        if label_images:
                            st.session_state['batch_labels'] = label_images
            else:
                st.warning("Nenhum item encontrado com os filtros aplicados")

with col2:
    # Preview and download section
    if 'generated_label' in st.session_state:
        st.write("**Preview da etiqueta:**")
        st.image(st.session_state['generated_label'], width=300)
        
        # Convert to bytes for download
        img_bytes = io.BytesIO()
        st.session_state['generated_label'].save(img_bytes, format='PNG', dpi=(300, 300))
        img_bytes.seek(0)
        
        st.download_button(
            "📥 Baixar Etiqueta PNG",
            img_bytes.getvalue(),
            file_name=st.session_state.get('label_filename', 'etiqueta.png'),
            mime="image/png"
        )
    
    elif 'batch_labels' in st.session_state:
        st.write(f"**{len(st.session_state['batch_labels'])} etiquetas geradas:**")
        
        # Show first few as preview
        for i, (sku, label_img) in enumerate(st.session_state['batch_labels'][:3]):
            st.write(f"Etiqueta {i+1}: {sku}")
            st.image(label_img, width=200)
        
        if len(st.session_state['batch_labels']) > 3:
            st.write(f"... e mais {len(st.session_state['batch_labels']) - 3} etiquetas")
        
        # Individual downloads
        for sku, label_img in st.session_state['batch_labels']:
            img_bytes = io.BytesIO()
            label_img.save(img_bytes, format='PNG', dpi=(300, 300))
            img_bytes.seek(0)
            
            st.download_button(
                f"📥 {sku}",
                img_bytes.getvalue(),
                file_name=f"etiqueta_{sku}.png",
                mime="image/png",
                key=f"download_{sku}"
            )

def generate_single_label(item_data, label_format):
    """Generate a single item label"""
    if not item_data:
        return None
    
    sku, category, brand, size, condition, list_price, markdown_stage = item_data
    current_price = compute_markdown_price(list_price, markdown_stage)
    
    # Label dimensions (in pixels at 300 DPI)
    dimensions = {
        "58x40mm (Térmica pequena)": (689, 472),  # 58x40mm at 300 DPI
        "70x50mm (Térmica padrão)": (827, 591),   # 70x50mm at 300 DPI  
        "90x60mm (Etiqueta grande)": (1063, 709)  # 90x60mm at 300 DPI
    }
    
    if label_format not in dimensions:
        return None
    
    width, height = dimensions[label_format]
    
    # Create image
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts (fallback to default if not available)
    try:
        if "pequena" in label_format:
            font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
        else:
            font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 28)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
            font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(sku)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize QR code based on label size
    if "pequena" in label_format:
        qr_size = 80
    else:
        qr_size = 120
    
    qr_img = qr_img.resize((qr_size, qr_size))
    
    # Layout elements
    margin = 10
    
    # Position QR code (left side)
    qr_x = margin
    qr_y = (height - qr_size) // 2
    img.paste(qr_img, (qr_x, qr_y))
    
    # Text area (right of QR code)
    text_x = qr_x + qr_size + margin
    text_width = width - text_x - margin
    
    # Draw text elements
    y_pos = margin
    
    # SKU
    draw.text((text_x, y_pos), sku, fill="black", font=font_medium)
    y_pos += 30 if "pequena" not in label_format else 25
    
    # Category and brand
    item_desc = f"{category}"
    if brand:
        item_desc += f" {brand}"
    if size:
        item_desc += f" {size}"
    
    # Wrap text if too long
    if len(item_desc) > 15 and "pequena" in label_format:
        # Split into two lines for small labels
        words = item_desc.split()
        line1 = " ".join(words[:2])
        line2 = " ".join(words[2:])
        draw.text((text_x, y_pos), line1, fill="black", font=font_small)
        y_pos += 20
        if line2:
            draw.text((text_x, y_pos), line2, fill="black", font=font_small)
            y_pos += 20
    else:
        draw.text((text_x, y_pos), item_desc, fill="black", font=font_small)
        y_pos += 25 if "pequena" not in label_format else 20
    
    # Condition
    draw.text((text_x, y_pos), f"Estado: {condition}", fill="black", font=font_small)
    y_pos += 25 if "pequena" not in label_format else 20
    
    # Price
    if markdown_stage > 0:
        # Show original price crossed out
        price_text = f"R$ {current_price:.2f}"
        original_text = f"(R$ {list_price:.2f})"
        draw.text((text_x, y_pos), price_text, fill="red", font=font_large)
        y_pos += 30 if "pequena" not in label_format else 25
        draw.text((text_x, y_pos), original_text, fill="gray", font=font_small)
        
        # Draw line through original price
        bbox = draw.textbbox((text_x, y_pos), original_text, font=font_small)
        draw.line([(bbox[0], bbox[1] + 8), (bbox[2], bbox[1] + 8)], fill="gray", width=1)
    else:
        price_text = f"R$ {current_price:.2f}"
        draw.text((text_x, y_pos), price_text, fill="black", font=font_large)
    
    return img

def generate_a4_labels(items_data, label_format):
    """Generate A4 sheet with multiple labels"""
    # A4 dimensions at 300 DPI
    a4_width, a4_height = 2480, 3508
    
    # Grid configuration
    if "2x4" in label_format:
        cols, rows = 2, 4
        label_width = (a4_width - 3 * 40) // 2  # 40px margins
        label_height = (a4_height - 5 * 40) // 4
    else:  # 3x6
        cols, rows = 3, 6
        label_width = (a4_width - 4 * 30) // 3  # 30px margins
        label_height = (a4_height - 7 * 30) // 6
    
    # Create A4 image
    a4_img = Image.new('RGB', (a4_width, a4_height), 'white')
    
    # Generate individual labels and place them
    for i, item_data in enumerate(items_data):
        if i >= cols * rows:
            break  # Can't fit more labels
        
        # Generate individual label (simplified for A4)
        label_img = generate_a4_single_label(item_data, label_width, label_height)
        if label_img:
            # Calculate position
            col = i % cols
            row = i // cols
            
            margin_x = 40 if "2x4" in label_format else 30
            margin_y = 40 if "2x4" in label_format else 30
            
            x = margin_x + col * (label_width + margin_x)
            y = margin_y + row * (label_height + margin_y)
            
            a4_img.paste(label_img, (x, y))
    
    return a4_img

def generate_a4_single_label(item_data, width, height):
    """Generate a single label optimized for A4 printing"""
    sku, category, brand, size, condition, list_price, markdown_stage = item_data
    current_price = compute_markdown_price(list_price, markdown_stage)
    
    # Create label image
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([(0, 0), (width-1, height-1)], outline="black", width=2)
    
    # Fonts for A4
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
        font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()  
        font_small = ImageFont.load_default()
    
    # Generate small QR code
    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(sku)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((60, 60))
    
    # Layout
    margin = 8
    
    # QR code (top right)
    qr_x = width - 60 - margin
    qr_y = margin
    img.paste(qr_img, (qr_x, qr_y))
    
    # Text content
    y_pos = margin
    
    # SKU (top left)
    draw.text((margin, y_pos), sku, fill="black", font=font_medium)
    y_pos += 25
    
    # Category, brand, size
    item_desc = f"{category}"
    if brand:
        item_desc += f" {brand}"
    if size:
        item_desc += f" {size}"
    
    draw.text((margin, y_pos), item_desc, fill="black", font=font_small)
    y_pos += 20
    
    # Condition
    draw.text((margin, y_pos), f"Estado: {condition}", fill="black", font=font_small)
    y_pos += 20
    
    # Price (bottom, centered)
    price_text = f"R$ {current_price:.2f}"
    bbox = draw.textbbox((0, 0), price_text, font=font_large)
    price_width = bbox[2] - bbox[0]
    price_x = (width - price_width) // 2
    price_y = height - 35
    
    if markdown_stage > 0:
        draw.text((price_x, price_y), price_text, fill="red", font=font_large)
        # Original price
        orig_text = f"(R$ {list_price:.2f})"
        orig_bbox = draw.textbbox((0, 0), orig_text, font=font_small)
        orig_width = orig_bbox[2] - orig_bbox[0]
        orig_x = (width - orig_width) // 2
        draw.text((orig_x, price_y - 18), orig_text, fill="gray", font=font_small)
        # Strike through
        draw.line([(orig_x, price_y - 10), (orig_x + orig_width, price_y - 10)], fill="gray", width=1)
    else:
        draw.text((price_x, price_y), price_text, fill="black", font=font_large)
    
    return img

st.divider()

# Label templates and settings
st.subheader("⚙️ Configurações de Etiqueta")

col1, col2 = st.columns(2)

with col1:
    st.write("**Informações da loja (para etiquetas):**")
    store_name = st.text_input("Nome da loja:", value="Brechó")
    store_contact = st.text_input("Contato:", value="@brecho_bh")
    
    st.write("**Elementos na etiqueta:**")
    include_qr = st.checkbox("QR Code", value=True)
    include_condition = st.checkbox("Estado do item", value=True)
    include_original_price = st.checkbox("Preço original (quando com desconto)", value=True)
    include_store_info = st.checkbox("Info da loja", value=False)

with col2:
    st.write("**Tamanhos de etiqueta disponíveis:**")
    st.info("""
    📏 **58x40mm:** Ideal para impressoras térmicas pequenas
    📏 **70x50mm:** Padrão para a maioria das térmicas  
    📏 **90x60mm:** Etiquetas grandes para itens especiais
    📄 **A4 Grade:** Múltiplas etiquetas em folha A4
    """)
    
    st.write("**Dicas de impressão:**")
    st.markdown("""
    - **Térmica:** Use papel térmico específico
    - **A4:** Papel adesivo ou cole com fita
    - **Qualidade:** 300 DPI recomendado
    - **QR Code:** Teste leitura antes de colar
    """)

# Bulk label operations
st.divider()
st.subheader("🔧 Operações Especiais")

col1, col2 = st.columns(2)

with col1:
    st.write("**Etiquetas de reposição:**")
    if st.button("📋 Itens sem etiqueta"):
        # Find items that might need labels (recently added, no photos/notes about labels)
        st.info("Funcionalidade em desenvolvimento")
    
    st.write("**Etiquetas de desconto:**")
    discount_stage = st.selectbox("Gerar para etapa:", [
        "1º desconto (-10%)",
        "2º desconto (-25%)", 
        "3º desconto (-40%)"
    ])
    if st.button("🏷️ Gerar etiquetas com desconto"):
        stage_map = {"1º desconto (-10%)": 1, "2º desconto (-25%)": 2, "3º desconto (-40%)": 3}
        stage = stage_map[discount_stage]
        
        _, discount_items = fetchall("""
            SELECT sku, category, brand, size, condition, list_price, markdown_stage
            FROM items 
            WHERE active = 1 AND sold_at IS NULL AND markdown_stage = ?
            ORDER BY listed_at DESC
            LIMIT 20
        """, (stage,))
        
        if discount_items:
            st.success(f"Encontrados {len(discount_items)} itens no {discount_stage}")
            # Generate batch labels would go here
        else:
            st.info(f"Nenhum item encontrado no {discount_stage}")

with col2:
    st.write("**Histórico de impressão:**")
    st.info("Em desenvolvimento: rastreamento de etiquetas impressas")
    
    st.write("**Configurações da impressora:**")
    printer_type = st.selectbox("Tipo de impressora:", [
        "Impressora térmica",
        "Impressora a laser/jato",
        "Impressora doméstica"
    ])
    
    if printer_type == "Impressora térmica":
        st.info("💡 Configure sua impressora para 300 DPI, papel térmico")
    else:
        st.info("💡 Use papel adesivo ou cole as etiquetas manualmente")

# Clear session state button
if st.button("🗑️ Limpar etiquetas geradas"):
    for key in ['generated_label', 'batch_labels', 'label_filename']:
        if key in st.session_state:
            del st.session_state[key]
    st.success("✅ Cache de etiquetas limpo")
