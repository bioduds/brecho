\
import streamlit as st
import pandas as pd
from db import upsert, delete, fetchall
from utils import compute_markdown_price

st.set_page_config(page_title="Itens", layout="wide")
st.title("Itens")

# Initialize form data in session state if not exists
if 'item_form_data' not in st.session_state:
    st.session_state.item_form_data = {
        'sku': '',
        'consignor_id': '',
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
        'active': True
    }

with st.form("add_item", clear_on_submit=False):
    st.subheader("Adicionar / Atualizar")
    
    # Get current form values from session state
    form_data = st.session_state.item_form_data
    
    sku = st.text_input("SKU (ex.: BH-2508-0001)", value=form_data['sku'])
    consignor_id = st.text_input("ConsignanteID (ou deixe vazio para doação)", value=form_data['consignor_id'])
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
        # Update session state with current form values
        st.session_state.item_form_data.update({
            'sku': sku,
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
        
        if not sku:
            st.error("❌ SKU é obrigatório.")
        else:
            try:
                upsert("items", "sku", dict(
                    sku=sku, consignor_id=consignor_id or None, acquisition_type=acquisition_type,
                    category=category, subcategory=subcategory, brand=brand, gender=gender, size=size, fit=fit,
                    color=color, fabric=fabric, condition=condition, flaws=flaws, bust=bust, waist=waist, length=length,
                    cost=cost, list_price=list_price, markdown_stage=int(stage), acquired_at=str(acquired_at), listed_at=str(listed_at),
                    channel_listed=channel_listed, sold_at=None, sale_price=None, channel_sold=None, days_on_hand=None,
                    photos_url=photos_url, notes=notes, active=int(active)
                ))
                current_price = compute_markdown_price(list_price, int(stage))
                st.success(f"✅ Item {sku} salvo com sucesso! Preço atual com desconto: R$ {current_price:.2f}")
                
                # Clear form only after successful save
                st.session_state.item_form_data = {
                    'sku': '',
                    'consignor_id': '',
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
                    'active': True
                }
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar item: {e}")
    
    if clear_form:
        # Clear form data
        st.session_state.item_form_data = {
            'sku': '',
            'consignor_id': '',
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
            'active': True
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
