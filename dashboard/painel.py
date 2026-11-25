"""Painel Streamlit. Rodar: streamlit run dashboard/painel.py"""
import streamlit as st

import consultas

st.set_page_config(page_title="Mandantes por estado", layout="wide")
st.title("Desempenho como mandante por estado")
st.caption("Brasileirão Série A, 2003–2024. Fonte: camada Ouro (DuckDB).")

a0, a1 = consultas.anos()
ini, fim = st.sidebar.slider("Anos", a0, a1, (a0, a1))
minimo = st.sidebar.number_input("Mínimo de jogos por estado", 1, 1000, 100)

estados = consultas.por_estado(ini, fim, minimo)
media = consultas.media_geral(ini, fim)

c1, c2, c3 = st.columns(3)
c1.metric("Média geral (pontos/jogo)", f"{media:.2f}")
c2.metric("Estados no gráfico", len(estados))
c3.metric("Jogos", int(estados["jogos"].sum()))

st.subheader("Pontos médios por jogo em casa")
st.bar_chart(estados.set_index("uf")["pontos_medios"])
st.dataframe(estados, hide_index=True, use_container_width=True)

uf = st.selectbox("Ver os times de um estado", estados["uf"])
st.dataframe(consultas.por_time(uf, ini, fim), hide_index=True,
             use_container_width=True)
