\
import streamlit as st
import pandas as pd
from db import upsert, delete, fetchall

st.set_page_config(page_title="Vendas", layout="wide")
st.title("Vendas")

# Initialize form data in session state if not exists
if 'sale_form_data' not in st.session_state:
    st.session_state.sale_form_data = {
        'sale_id': '',
        'date': None,
        'sku': '',
        'price': 0.0,
        'discount': 0.0,
        'channel': 'Loja',
        'customer_name': '',
        'customer_whatsapp': '',
        'payment': 'Pix',
        'notes': ''
    }

with st.form("add_sale", clear_on_submit=False):
    st.subheader("Registrar venda")
    
    # Get current form values from session state
    form_data = st.session_state.sale_form_data
    
    sale_id = st.text_input("VendaID (ex.: V0001)", value=form_data['sale_id'])
    
    import datetime
    today = datetime.date.today()
    date = st.date_input("Data", value=form_data['date'] if form_data['date'] else today)
    
    sku = st.text_input("SKU (deve existir em Itens)", value=form_data['sku'])
    price = st.number_input("Preço de venda (R$)", value=form_data['price'], step=1.0)
    discount = st.number_input("Desconto (R$)", value=form_data['discount'], step=1.0)
    
    channels = ["Loja","Instagram","WhatsApp","Online"]
    channel = st.selectbox("Canal", channels,
                          index=channels.index(form_data['channel']) if form_data['channel'] in channels else 0)
    customer_name = st.text_input("Cliente (opcional)", value=form_data['customer_name'])
    customer_whatsapp = st.text_input("WhatsApp (opcional)", value=form_data['customer_whatsapp'])
    
    payments = ["Débito","Crédito","Pix","Dinheiro"]
    payment = st.selectbox("Pagamento", payments,
                          index=payments.index(form_data['payment']) if form_data['payment'] in payments else 2)
    notes = st.text_area("Observações", value=form_data['notes'])
    
    col1, col2 = st.columns([1, 1])
    with col1:
        submitted = st.form_submit_button("Salvar venda", type="primary")
    with col2:
        clear_form = st.form_submit_button("Limpar Formulário")
    
    if submitted:
        # Update session state with current form values
        st.session_state.sale_form_data.update({
            'sale_id': sale_id,
            'date': date,
            'sku': sku,
            'price': price,
            'discount': discount,
            'channel': channel,
            'customer_name': customer_name,
            'customer_whatsapp': customer_whatsapp,
            'payment': payment,
            'notes': notes
        })
        
        if not sale_id or not sku:
            st.error("❌ VendaID e SKU são obrigatórios.")
        else:
            try:
                # Find consignor_id from item
                cols, rows = fetchall("SELECT consignor_id FROM items WHERE sku=?", (sku,))
                consignor_id = rows[0][0] if rows else None
                
                upsert("sales", "id", dict(
                    id=sale_id, date=str(date), sku=sku, sale_price=price, discount_value=discount,
                    channel=channel, customer_name=customer_name, customer_whatsapp=customer_whatsapp,
                    payment_method=payment, notes=notes, consignor_id=consignor_id
                ))
                # Mark item as sold
                fetchall("UPDATE items SET sold_at=?, sale_price=?, channel_sold=? WHERE sku=?", 
                        (str(date), price, channel, sku))
                st.success(f"✅ Venda {sale_id} registrada com sucesso! Consignante: {consignor_id or '—'}")
                
                # Clear form only after successful save
                st.session_state.sale_form_data = {
                    'sale_id': '',
                    'date': None,
                    'sku': '',
                    'price': 0.0,
                    'discount': 0.0,
                    'channel': 'Loja',
                    'customer_name': '',
                    'customer_whatsapp': '',
                    'payment': 'Pix',
                    'notes': ''
                }
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao registrar venda: {e}")
    
    if clear_form:
        # Clear form data
        st.session_state.sale_form_data = {
            'sale_id': '',
            'date': None,
            'sku': '',
            'price': 0.0,
            'discount': 0.0,
            'channel': 'Loja',
            'customer_name': '',
            'customer_whatsapp': '',
            'payment': 'Pix',
            'notes': ''
        }
        st.rerun()

st.divider()
st.subheader("Histórico de vendas")
cols, rows = fetchall("""
SELECT s.id, s.date, s.sku, i.category, i.brand, i.size,
       s.sale_price, s.discount_value, (s.sale_price - s.discount_value) AS liquido,
       s.channel, s.payment_method, s.consignor_id
FROM sales s
LEFT JOIN items i ON s.sku = i.sku
ORDER BY s.date DESC, s.id DESC;
""")
df = pd.DataFrame(rows, columns=cols)
st.dataframe(df, use_container_width=True)

del_id = st.text_input("Excluir venda (VendaID)")
if st.button("Excluir venda"):
    if del_id:
        delete("sales", "id", del_id)
        st.success(f"Venda {del_id} excluída (se existia).")
    else:
        st.error("Informe um VendaID.")
