import streamlit as st
from chatbot.chatbot_result import run_chatbot

# ⚠️ set_page_config HARUS paling atas sebelum st.* apapun
st.set_page_config(
    page_title="Chatbot Film",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 Chatbot Film")
st.caption(f"Session ID: `{st.session_state.session_id}`")

# Tampilkan riwayat chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input dari user
if prompt := st.chat_input("Ketik pertanyaan kamu…"):

    # Tampilkan pesan user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Panggil chatbot dan tampilkan hasilnya
    with st.chat_message("assistant"):
        with st.spinner("Sedang memproses…"):
            response = run_chatbot(prompt)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})