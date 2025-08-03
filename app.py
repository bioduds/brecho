\
import streamlit as st
from db import init_db

st.set_page_config(page_title="Brechó Local", layout="wide")
st.title("Brechó — Sistema Local (SQLite)")

st.sidebar.success("Use o menu de páginas à esquerda para navegar.")
st.markdown(
    """
**O que este app faz agora:**
- Cadastro de **Consignantes**
- Cadastro de **Itens** (com política de desconto por etapas)
- Registro de **Vendas**
- Relatório de **Repasses** por período (automático)
- **Dashboard** com KPIs e análises avançadas
- **Automação** de descontos e rotinas
- Gestão de **Fotos** dos itens
- Gerador de **Etiquetas** profissionais

**Dica:** Rode com `streamlit run app.py`.
"""
)

if "db_ready" not in st.session_state:
    init_db()
    st.session_state["db_ready"] = True

st.markdown("---")
st.markdown("Atalhos rápidos:")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Ir para Consignantes"):
        st.switch_page("pages/1_Consignantes.py")
with c2:
    if st.button("Ir para Itens"):
        st.switch_page("pages/2_Itens.py")
with c3:
    if st.button("Ir para Vendas"):
        st.switch_page("pages/3_Vendas.py")
