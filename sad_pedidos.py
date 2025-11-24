import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from fpdf import FPDF

# --- Configuração da Página ---
st.set_page_config(
    page_title="SAD Profissional de Pedidos",
    layout="wide"
)

st.title("SAD Profissional - Gestão e Prioridade de Pedidos")

# --------------------------
# Controle de acesso
# --------------------------
st.sidebar.header("Login")
usuario = st.sidebar.text_input("Usuário")
senha = st.sidebar.text_input("Senha", type="password")

# Define usuários e datas de acesso
usuarios_validos = {
    "admin": {"senha": "1234", "acesso_ate": datetime(2025, 12, 31)},
    "usuario1": {"senha": "abcd", "acesso_ate": datetime(2025, 11, 30)}
}

acesso_autorizado = False
if usuario in usuarios_validos:
    if senha == usuarios_validos[usuario]["senha"]:
        if datetime.today() <= usuarios_validos[usuario]["acesso_ate"]:
            acesso_autorizado = True
        else:
            st.sidebar.error("⛔ Acesso expirado para este usuário.")
    else:
        st.sidebar.error("Senha incorreta.")

if not acesso_autorizado:
    st.stop()

# --------------------------
# Session State para armazenar pedidos
# --------------------------
if "pedidos" not in st.session_state:
    st.session_state.pedidos = pd.DataFrame(columns=[
        "Pedido", "Urgência", "Complexidade", "Custo", "Pontuação", "Prazo", "Status"
    ])

# --------------------------
# Formulário para adicionar novo pedido
# --------------------------
st.sidebar.header("Adicionar Novo Pedido")
with st.sidebar.form("form_novo_pedido", clear_on_submit=True):
    nome = st.text_input("Nome do Pedido")
    urgencia = st.slider("Urgência (1-10)", 1, 10, 5)
    complexidade = st.slider("Complexidade (1-10)", 1, 10, 5)
    custo = st.slider("Custo (1-10)", 1, 10, 5)
    prazo = st.date_input("Prazo de entrega", datetime.today() + timedelta(days=7))
    submit = st.form_submit_button("Adicionar Pedido")
    
    if submit and nome:
        pontuacao = (urgencia*0.4 + complexidade*0.3 + (10-custo)*0.3)
        novo_pedido = pd.DataFrame([{
            "Pedido": nome,
            "Urgência": urgencia,
            "Complexidade": complexidade,
            "Custo": custo,
            "Pontuação": pontuacao,
            "Prazo": prazo,
            "Status": "Aberto"
        }])
        st.session_state.pedidos = pd.concat([st.session_state.pedidos, novo_pedido], ignore_index=True)
        st.success(f"Pedido '{nome}' adicionado com sucesso!")

# --------------------------
# Dashboard Principal
# --------------------------
st.header("Dashboard de Pedidos")
pedidos_abertos = st.session_state.pedidos[st.session_state.pedidos["Status"]=="Aberto"]

if not pedidos_abertos.empty:
    pedidos_abertos = pedidos_abertos.sort_values(by="Pontuação", ascending=False)

    st.subheader("Pedidos Abertos")
    st.dataframe(pedidos_abertos)

    # Concluir pedidos
    st.subheader("Marcar Pedidos como Concluídos")
    for idx, row in pedidos_abertos.iterrows():
        if st.checkbox(f"Concluir Pedido: {row['Pedido']}", key=f"chk_{idx}"):
            st.session_state.pedidos.at[idx, "Status"] = "Concluído"
            st.experimental_rerun()

    # Gráfico de Prioridade
    st.subheader("Gráfico de Prioridade")
    fig = px.bar(pedidos_abertos, x="Pedido", y="Pontuação", color="Urgência",
                 title="Prioridade dos Pedidos (Maior = mais urgente)")
    st.plotly_chart(fig)

    # Alertas de Prazo
    st.subheader("Alertas de Prazo")
    hoje = datetime.today().date()
    atrasados = pedidos_abertos[pedidos_abertos["Prazo"] < hoje]
    proximos = pedidos_abertos[(pedidos_abertos["Prazo"] >= hoje) & 
                                (pedidos_abertos["Prazo"] <= hoje + timedelta(days=2))]
    if not atrasados.empty:
        st.error(f"⚠️ Pedidos atrasados: {', '.join(atrasados['Pedido'].tolist())}")
    if not proximos.empty:
        st.warning(f"⏰ Pedidos próximos do prazo: {', '.join(proximos['Pedido'].tolist())}")

    # --------------------------
    # Exportar PDF
    # --------------------------
    st.subheader("Exportar PDF da Ordem de Produção")
    if st.button("Gerar PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Ordem de Produção - Pedidos Abertos", ln=True, align="C")
        pdf.ln(10)
        for idx, row in pedidos_abertos.iterrows():
            pdf.cell(0, 10, txt=f"Pedido: {row['Pedido']}, Urgência: {row['Urgência']}, Complexidade: {row['Complexidade']}, Custo: {row['Custo']}, Prazo: {row['Prazo']}", ln=True)
        pdf_file = "ordem_producao.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("Download PDF", f, file_name=pdf_file)
else:
    st.info("Nenhum pedido aberto no momento.")

st.caption("SAD Profissional com PDF, alerta de prazo e controle de acesso por usuário.")

