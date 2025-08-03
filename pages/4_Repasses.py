\
import streamlit as st
import pandas as pd
from db import fetchall
from utils import compute_payouts

st.set_page_config(page_title="Repasses", layout="wide")
st.title("Repasses (Período)")

c1, c2 = st.columns(2)
with c1:
    start = st.date_input("Período início")
with c2:
    end = st.date_input("Período fim")

if st.button("Calcular repasses"):
    # Aggregate net sales per consignor
    sql = """
    SELECT s.consignor_id, c.name, c.pix_key, COALESCE(c.percent,0.5) AS percent,
           SUM(COALESCE(s.sale_price,0) - COALESCE(s.discount_value,0)) AS total_net,
           COUNT(*) AS qtd
    FROM sales s
    LEFT JOIN consignors c ON c.id = s.consignor_id
    WHERE date >= ? AND date <= ? AND s.consignor_id IS NOT NULL
    GROUP BY s.consignor_id, c.name, c.pix_key, c.percent
    ORDER BY total_net DESC;
    """
    cols, rows = fetchall(sql, (str(start), str(end)))
    rows_dict = [dict(zip(cols, r)) for r in rows]
    payouts = compute_payouts(rows_dict)
    if payouts:
        df = pd.DataFrame(payouts)
        df = df[["consignor_id","name","qtd","total_net","percent","consignor_value","shop_value","pix_key"]]
        df = df.rename(columns={
            "consignor_id":"ConsignanteID","name":"Nome","qtd":"Peças",
            "total_net":"Vendas líquidas (R$)","percent":"% Consignante",
            "consignor_value":"Valor p/ Consignante (R$)","shop_value":"Valor p/ Loja (R$)",
            "pix_key":"Chave Pix"
        })
        st.success("Repasses calculados.")
        st.dataframe(df, use_container_width=True)
        st.download_button("Baixar CSV", df.to_csv(index=False).encode("utf-8"), file_name="repasses.csv", mime="text/csv")
    else:
        st.info("Nenhuma venda no período para consignantes.")
