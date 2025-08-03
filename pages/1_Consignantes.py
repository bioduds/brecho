\
import streamlit as st
import pandas as pd
from db import upsert, delete, fetchall

st.set_page_config(page_title="Consignantes", layout="wide")
st.title("Consignantes")

# Function to generate next consignor ID
def generate_next_consignor_id():
    cols, rows = fetchall("SELECT id FROM consignors WHERE id LIKE 'C%' ORDER BY id DESC LIMIT 1")
    if rows:
        last_id = rows[0][0]
        # Extract number from C0001 format
        try:
            last_num = int(last_id[1:])
            next_num = last_num + 1
            return f"C{next_num:04d}"
        except:
            return "C0001"
    else:
        return "C0001"

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
        'active': True,
        'is_editing': False
    }

# Form without auto-clear
with st.form("add_consignor", clear_on_submit=False):
    st.subheader("Adicionar / Atualizar Consignante")
    
    # Auto-generate ID for new consignors, or show existing ID for editing
    if st.session_state.consignor_form_data['is_editing']:
        id_ = st.text_input("ID", value=st.session_state.consignor_form_data['id'], disabled=True)
        st.caption("ID não pode ser alterado durante edição")
    else:
        if not st.session_state.consignor_form_data['id']:
            auto_id = generate_next_consignor_id()
            st.session_state.consignor_form_data['id'] = auto_id
        
        id_ = st.text_input("ID (gerado automaticamente)", 
                           value=st.session_state.consignor_form_data['id'], 
                           disabled=True)
        st.caption("ID será gerado automaticamente ao salvar")
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
        # Generate final ID if creating new consignor
        if not st.session_state.consignor_form_data['is_editing']:
            final_id = generate_next_consignor_id()
        else:
            final_id = id_
        
        # Update session state with current form values
        st.session_state.consignor_form_data.update({
            'id': final_id,
            'name': name,
            'whatsapp': whatsapp,
            'email': email,
            'pix_key': pix_key,
            'percent': percent,
            'notes': notes,
            'active': active
        })
        
        if not name:
            st.error("❌ Nome é obrigatório.")
        else:
            try:
                upsert("consignors", "id", dict(
                    id=final_id, name=name, whatsapp=whatsapp, email=email, pix_key=pix_key,
                    percent=percent, notes=notes, active=int(active)
                ))
                st.success(f"✅ Consignante {final_id} salvo com sucesso!")
                
                # Clear form only after successful save
                st.session_state.consignor_form_data = {
                    'id': '',
                    'name': '',
                    'whatsapp': '',
                    'email': '',
                    'pix_key': '',
                    'percent': 0.5,
                    'notes': '',
                    'active': True,
                    'is_editing': False
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
            'active': True,
            'is_editing': False
        }
        st.rerun()

st.divider()
st.subheader("Lista de Consignantes")

# Display table with edit functionality
cols, rows = fetchall("SELECT id,name,whatsapp,email,pix_key,percent,active FROM consignors ORDER BY id;")
if rows:
    df = pd.DataFrame(rows, columns=cols)
    
    # Add edit buttons
    st.write("**Clique em 'Editar' para modificar um consignante:**")
    
    for idx, row in df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
        
        with col1:
            if st.button(f"Editar", key=f"edit_{row['id']}"):
                # Load data into form for editing
                st.session_state.consignor_form_data = {
                    'id': row['id'],
                    'name': row['name'],
                    'whatsapp': row['whatsapp'] or '',
                    'email': row['email'] or '',
                    'pix_key': row['pix_key'] or '',
                    'percent': float(row['percent']),
                    'notes': '',  # We don't store notes in the display query
                    'active': bool(row['active']),
                    'is_editing': True
                }
                st.rerun()
        
        with col2:
            st.write(f"**{row['id']}** - {row['name']}")
        
        with col3:
            whatsapp_text = row['whatsapp'] if row['whatsapp'] else "—"
            st.write(f"📱 {whatsapp_text}")
        
        with col4:
            percent_text = f"{float(row['percent']*100):.0f}%"
            st.write(f"💰 {percent_text}")
        
        with col5:
            status = "✅ Ativo" if row['active'] else "❌ Inativo"
            st.write(status)
    
    st.divider()
    
    # Full dataframe view
    st.write("**Tabela completa:**")
    st.dataframe(df, use_container_width=True)
    
else:
    st.info("Nenhum consignante cadastrado ainda.")

delete_id = st.text_input("Excluir consignante (ID)")
if st.button("Excluir"):
    if delete_id:
        delete("consignors", "id", delete_id)
        st.success(f"Consignante {delete_id} excluído (se existia).")
    else:
        st.error("Informe um ID.")
