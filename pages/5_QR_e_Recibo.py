\
import streamlit as st
import io
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="QR & Recibo", layout="wide")
st.title("QR de SKU e Recibo simples (PDF)")

st.subheader("Gerar QR para um SKU")
sku = st.text_input("SKU")
if st.button("Gerar QR"):
    if sku:
        img = qrcode.make(sku)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption=f"QR do SKU {sku}", width=200)
        st.download_button("Baixar QR PNG", buf.getvalue(), file_name=f"{sku}_qr.png", mime="image/png")
    else:
        st.error("Informe um SKU.")

st.divider()
st.subheader("Gerar Recibo simples (PDF)")
store = st.text_input("Nome da Loja", value="Brechó")
cons = st.text_input("Consignante")
date = st.date_input("Data")
itens = st.text_area("Itens (um por linha, formato: SKU | Categoria | Marca | Tamanho | Condição | Preço)")

if st.button("Gerar PDF"):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    w, h = A4
    y = h - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w/2, y, "RECIBO DE CONSIGNAÇÃO — " + store)
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Consignante: {cons}     Data: {date}")
    y -= 20
    c.drawString(40, y, "Itens:")
    y -= 15
    c.setFont("Helvetica", 9)
    for line in itens.splitlines():
        if not line.strip(): 
            continue
        if y < 80:
            c.showPage(); y = h - 60; c.setFont("Helvetica", 9)
        c.drawString(50, y, "• " + line.strip())
        y -= 14
    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(40, y, "Assinatura do Consignante: ________________________________")
    y -= 20
    c.drawString(40, y, "Assinatura da Loja: ______________________________________")
    c.showPage()
    c.save()
    pdf_bytes = packet.getvalue()
    st.download_button("Baixar Recibo PDF", pdf_bytes, file_name="recibo_consignacao.pdf", mime="application/pdf")
