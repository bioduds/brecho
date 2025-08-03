\
import streamlit as st
import pandas as pd
from db import upsert, delete, fetchall

st.set_page_config(page_title="Consignantes", layout="wide")
st.title("Consignantes")

# Initialize form data in session state if not exists
if 'consignor_form_data' not in st.session_state:
    st.session_state.consignor_form_data = {
        'id': '',
        'name': '',
        'whatsapp': '',
        'email': '',
        'pix_key': '',
        'percent': 0.5,
        'notes': '',
        'active': True
    }

# Form without auto-clear
with st.form("add_consignor", clear_on_submit=False):
    st.subheader("Adicionar / Atualizar")
    id_ = st.text_input("ID (ex.: C0001)", value=st.session_state.consignor_form_data['id'])
    name = st.text_input("Nome", value=st.session_state.consignor_form_data['name'])
    whatsapp = st.text_input("WhatsApp", value=st.session_state.consignor_form_data['whatsapp'])
    email = st.text_input("Email", value=st.session_state.consignor_form_data['email'])
    pix_key = st.text_input("Chave Pix", value=st.session_state.consignor_form_data['pix_key'])
    percent = st.number_input("Percentual consignante (0–1)", 
                             value=st.session_state.consignor_form_data['percent'], 
                             step=0.05)
    notes = st.text_area("Observações", value=st.session_state.consignor_form_data['notes'])
    active = st.checkbox("Ativo", value=st.session_state.consignor_form_data['active'])
    
    col1, col2 = st.columns([1, 1])
    with col1:
        submitted = st.form_submit_button("Salvar", type="primary")
    with col2:
        clear_form = st.form_submit_button("Limpar Formulário")
    
    if submitted:
        # Update session state with current form values
        st.session_state.consignor_form_data.update({
            'id': id_,
            'name': name,
            'whatsapp': whatsapp,
            'email': email,
            'pix_key': pix_key,
            'percent': percent,
            'notes': notes,
            'active': active
        })
        
        if not id_ or not name:
            st.error("❌ ID e Nome são obrigatórios.")
        else:
            try:
                upsert("consignors", "id", dict(
                    id=id_, name=name, whatsapp=whatsapp, email=email, pix_key=pix_key,
                    percent=percent, notes=notes, active=int(active)
                ))
                st.success(f"✅ Consignante {id_} salvo com sucesso!")
                
                # Clear form only after successful save
                st.session_state.consignor_form_data = {
                    'id': '',
                    'name': '',
                    'whatsapp': '',
                    'email': '',
                    'pix_key': '',
                    'percent': 0.5,
                    'notes': '',
                    'active': True
                }
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar consignante: {e}")
    
    if clear_form:
        # Clear form data
        st.session_state.consignor_form_data = {
            'id': '',
            'name': '',
            'whatsapp': '',
            'email': '',
            'pix_key': '',
            'percent': 0.5,
            'notes': '',
            'active': True
        }
        st.rerun()

st.divider()
st.subheader("Lista")
cols, rows = fetchall("SELECT id,name,whatsapp,email,pix_key,percent,active FROM consignors ORDER BY id;")
df = pd.DataFrame(rows, columns=cols)
st.dataframe(df, use_container_width=True)

delete_id = st.text_input("Excluir consignante (ID)")
if st.button("Excluir"):
    if delete_id:
        delete("consignors", "id", delete_id)
        st.success(f"Consignante {delete_id} excluído (se existia).")
    else:
        st.error("Informe um ID.")
