\
import streamlit as st
import pandas as pd
from db import upsert, delete, fetchall
from utils import compute_markdown_price

# Function to generate next SKU
def generate_next_sku():
    from datetime import datetime
    year_month = datetime.now().strftime("%y%m")  # YYMM format
    
    cols, rows = fetchall(f"SELECT sku FROM items WHERE sku LIKE 'BH-{year_month}-%' ORDER BY sku DESC LIMIT 1")
    if rows:
        last_sku = rows[0][0]
        # Extract number from BH-2508-0001 format
        try:
            last_num = int(last_sku.split('-')[2])
            next_num = last_num + 1
            return f"BH-{year_month}-{next_num:04d}"
        except:
            return f"BH-{year_month}-0001"
    else:
        return f"BH-{year_month}-0001"

st.set_page_config(page_title="Itens", layout="wide")
st.title("Itens")

# Initialize form data in session state if not exists
if 'item_form_data' not in st.session_state:
    st.session_state.item_form_data = {
        'sku': '',
        'consignor_id': '',
        'consignor_search': '',
        'acquisition_type': 'consignação',
        'category': 'Vestido',
        'subcategory': '',
        'brand': '',
        'gender': 'F',
        'size': '',
        'fit': 'Regular',
        'color': '',
        'fabric': '',
        'condition': 'A',
        'flaws': '',
        'bust': 0.0,
        'waist': 0.0,
        'length': 0.0,
        'cost': 0.0,
        'list_price': 0.0,
        'stage': 0,
        'acquired_at': None,
        'listed_at': None,
        'channel_listed': 'Loja',
        'photos_url': '',
        'notes': '',
        'active': True,
        'is_editing': False
    }

with st.form("add_item", clear_on_submit=False):
    st.subheader("Adicionar / Atualizar Item")
    
    # Get current form values from session state
    form_data = st.session_state.item_form_data
    
    # Auto-generate SKU for new items, or show existing SKU for editing
    if st.session_state.item_form_data['is_editing']:
        sku = st.text_input("SKU", value=form_data['sku'], disabled=True)
        st.caption("SKU não pode ser alterado durante edição")
    else:
        if not st.session_state.item_form_data['sku']:
            auto_sku = generate_next_sku()
            st.session_state.item_form_data['sku'] = auto_sku
        
        sku = st.text_input("SKU (gerado automaticamente)", 
                           value=form_data['sku'], 
                           disabled=True)
        st.caption("SKU será gerado automaticamente no formato BH-YYMM-NNNN")
    
    # Consignor search with auto-complete
    st.write("**Consignante:**")
    consignor_search = st.text_input("Digite o nome do consignante (ou deixe vazio para doação)", 
                                    value=form_data.get('consignor_search', ''),
                                    key="consignor_search_input")
    
    # Get all consignors for search
    cols, consignor_rows = fetchall("SELECT id, name FROM consignors WHERE active = 1 ORDER BY name")
    consignor_options = []
    selected_consignor_id = form_data['consignor_id']
    
    if consignor_rows:
        consignor_options = [(row[0], row[1]) for row in consignor_rows]
        
        # Filter consignors based on search input
        if consignor_search:
            filtered_consignors = [
                (id_, name) for id_, name in consignor_options 
                if consignor_search.lower() in name.lower()
            ]
            
            if filtered_consignors:
                st.write("**Consignantes encontrados:**")
                for id_, name in filtered_consignors[:5]:  # Show max 5 results
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{name}** ({id_})")
                    with col2:
                        if st.button("Selecionar", key=f"select_{id_}"):
                            st.session_state.item_form_data['consignor_id'] = id_
                            st.session_state.item_form_data['consignor_search'] = name
                            st.rerun()
            else:
                st.warning("Nenhum consignante encontrado com esse nome.")
    
    # Show selected consignor
    if selected_consignor_id:
        # Find the name of the selected consignor
        selected_name = next((name for id_, name in consignor_options if id_ == selected_consignor_id), "")
        st.success(f"✅ Consignante selecionado: **{selected_name}** ({selected_consignor_id})")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Limpar seleção"):
                st.session_state.item_form_data['consignor_id'] = ''
                st.session_state.item_form_data['consignor_search'] = ''
                st.rerun()
    else:
        st.info("💝 Item será cadastrado como **doação** (sem consignante)")
    
    consignor_id = selected_consignor_id  # Use the selected ID
    
    acquisition_type = st.selectbox("Tipo de aquisição", ["consignação", "doação", "compra"], 
                                   index=["consignação", "doação", "compra"].index(form_data['acquisition_type']))
    
    categories = ["Vestido","Camisa","Camiseta","Calça","Jeans","Saia","Blazer","Casaco","Short","Macacão","Sapato","Bolsa","Acessório"]
    category = st.selectbox("Categoria", categories, 
                           index=categories.index(form_data['category']) if form_data['category'] in categories else 0)
    subcategory = st.text_input("Subcategoria", value=form_data['subcategory'])
    brand = st.text_input("Marca", value=form_data['brand'])
    
    genders = ["F","M","Unissex"]
    gender = st.selectbox("Gênero", genders,
                         index=genders.index(form_data['gender']) if form_data['gender'] in genders else 0)
    size = st.text_input("Tamanho (ex.: M, 40)", value=form_data['size'])
    
    fits = ["Ajustada","Regular","Ampla"]
    fit = st.selectbox("Modelagem", fits,
                      index=fits.index(form_data['fit']) if form_data['fit'] in fits else 1)
    color = st.text_input("Cor", value=form_data['color'])
    fabric = st.text_input("Tecido", value=form_data['fabric'])
    
    conditions = ["A","A-","B","C"]
    condition = st.selectbox("Condição", conditions,
                            index=conditions.index(form_data['condition']) if form_data['condition'] in conditions else 0)
    flaws = st.text_area("Defeitos (se houver)", value=form_data['flaws'])
    bust = st.number_input("Busto (cm)", value=form_data['bust'], step=0.5)
    waist = st.number_input("Cintura (cm)", value=form_data['waist'], step=0.5)
    length = st.number_input("Comprimento (cm)", value=form_data['length'], step=0.5)
    cost = st.number_input("Custo (R$)", value=form_data['cost'], step=1.0)
    list_price = st.number_input("Preço de lista (R$)", value=form_data['list_price'], step=1.0)
    stage = st.selectbox("Etapa de desconto", [0,1,2,3], index=form_data['stage'])
    
    # Handle dates carefully
    import datetime
    today = datetime.date.today()
    acquired_at = st.date_input("Entrada em", value=form_data['acquired_at'] if form_data['acquired_at'] else today)
    listed_at = st.date_input("Listado em", value=form_data['listed_at'] if form_data['listed_at'] else today)
    
    channels = ["Loja","Instagram","WhatsApp","Online"]
    channel_listed = st.selectbox("Canal listagem", channels,
                                 index=channels.index(form_data['channel_listed']) if form_data['channel_listed'] in channels else 0)
    photos_url = st.text_input("URL de fotos (opcional)", value=form_data['photos_url'])
    notes = st.text_area("Observações", value=form_data['notes'])
    active = st.checkbox("Ativo", value=form_data['active'])
    
    col1, col2 = st.columns([1, 1])
    with col1:
        submitted = st.form_submit_button("Salvar", type="primary")
    with col2:
        clear_form = st.form_submit_button("Limpar Formulário")
    
    if submitted:
        # Generate final SKU if creating new item
        if not st.session_state.item_form_data['is_editing']:
            final_sku = generate_next_sku()
        else:
            final_sku = sku
        
        # Update session state with current form values
        st.session_state.item_form_data.update({
            'sku': final_sku,
            'consignor_id': consignor_id,
            'acquisition_type': acquisition_type,
            'category': category,
            'subcategory': subcategory,
            'brand': brand,
            'gender': gender,
            'size': size,
            'fit': fit,
            'color': color,
            'fabric': fabric,
            'condition': condition,
            'flaws': flaws,
            'bust': bust,
            'waist': waist,
            'length': length,
            'cost': cost,
            'list_price': list_price,
            'stage': stage,
            'acquired_at': acquired_at,
            'listed_at': listed_at,
            'channel_listed': channel_listed,
            'photos_url': photos_url,
            'notes': notes,
            'active': active
        })
        
        if not category or list_price <= 0:
            st.error("❌ Categoria e Preço de lista são obrigatórios.")
        else:
            try:
                upsert("items", "sku", dict(
                    sku=final_sku, consignor_id=consignor_id or None, acquisition_type=acquisition_type,
                    category=category, subcategory=subcategory, brand=brand, gender=gender, size=size, fit=fit,
                    color=color, fabric=fabric, condition=condition, flaws=flaws, bust=bust, waist=waist, length=length,
                    cost=cost, list_price=list_price, markdown_stage=int(stage), acquired_at=str(acquired_at), listed_at=str(listed_at),
                    channel_listed=channel_listed, sold_at=None, sale_price=None, channel_sold=None, days_on_hand=None,
                    photos_url=photos_url, notes=notes, active=int(active)
                ))
                current_price = compute_markdown_price(list_price, int(stage))
                st.success(f"✅ Item {final_sku} salvo com sucesso! Preço atual: R$ {current_price:.2f}")
                
                # Clear form only after successful save
                st.session_state.item_form_data = {
                    'sku': '',
                    'consignor_id': '',
                    'consignor_search': '',
                    'acquisition_type': 'consignação',
                    'category': 'Vestido',
                    'subcategory': '',
                    'brand': '',
                    'gender': 'F',
                    'size': '',
                    'fit': 'Regular',
                    'color': '',
                    'fabric': '',
                    'condition': 'A',
                    'flaws': '',
                    'bust': 0.0,
                    'waist': 0.0,
                    'length': 0.0,
                    'cost': 0.0,
                    'list_price': 0.0,
                    'stage': 0,
                    'acquired_at': None,
                    'listed_at': None,
                    'channel_listed': 'Loja',
                    'photos_url': '',
                    'notes': '',
                    'active': True,
                    'is_editing': False
                }
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar item: {e}")
    
    if clear_form:
        # Clear form data
        st.session_state.item_form_data = {
            'sku': '',
            'consignor_id': '',
            'consignor_search': '',
            'acquisition_type': 'consignação',
            'category': 'Vestido',
            'subcategory': '',
            'brand': '',
            'gender': 'F',
            'size': '',
            'fit': 'Regular',
            'color': '',
            'fabric': '',
            'condition': 'A',
            'flaws': '',
            'bust': 0.0,
            'waist': 0.0,
            'length': 0.0,
            'cost': 0.0,
            'list_price': 0.0,
            'stage': 0,
            'acquired_at': None,
            'listed_at': None,
            'channel_listed': 'Loja',
            'photos_url': '',
            'notes': '',
            'active': True,
            'is_editing': False
        }
        st.rerun()

st.divider()
st.subheader("Estoque")
query = """
SELECT sku, consignor_id, acquisition_type, category, brand, size, condition,
       list_price, markdown_stage, ROUND(list_price * (1-CASE markdown_stage
           WHEN 0 THEN 0.0 WHEN 1 THEN 0.10 WHEN 2 THEN 0.25 WHEN 3 THEN 0.40 ELSE 0 END),2) AS preco_atual,
       channel_listed, listed_at, photos_url, active
FROM items
ORDER BY listed_at DESC, sku DESC;
"""
cols, rows = fetchall(query)
df = pd.DataFrame(rows, columns=cols)
st.dataframe(df, use_container_width=True)

del_sku = st.text_input("Excluir item (SKU)")
if st.button("Excluir item"):
    if del_sku:
        delete("items", "sku", del_sku)
        st.success(f"Item {del_sku} excluído (se existia).")
    else:
        st.error("Informe um SKU.")
