# =====================================
# 🤖 PRIMEBUD 1.0 - GROQ + GPT-OSS + GPT-IMAGE-1
# =====================================

import streamlit as st
import json, os, hashlib
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64
import requests

# =============================
# CONFIGURAÇÕES INICIAIS
# =============================
st.set_page_config(
    page_title="PrimeBud 1.0",
    page_icon="🤖",
    layout="wide"
)

# =============================
# SISTEMA DE USUÁRIOS
# =============================
USERS_FILE = "users_database.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

users = load_users()

# =============================
# LOGIN
# =============================
st.sidebar.title("🔐 Login do PrimeBud")
menu = st.sidebar.radio("Menu", ["Entrar", "Registrar"])

if menu == "Registrar":
    user = st.sidebar.text_input("Usuário")
    pwd = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Registrar"):
        if user in users:
            st.sidebar.error("Usuário já existe.")
        else:
            users[user] = hash_password(pwd)
            save_users(users)
            st.sidebar.success("Conta criada com sucesso!")

if menu == "Entrar":
    user = st.sidebar.text_input("Usuário")
    pwd = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if user in users and users[user] == hash_password(pwd):
            st.session_state["logged_in"] = True
            st.session_state["user"] = user
        else:
            st.sidebar.error("Usuário ou senha incorretos.")

# =============================
# INTERFACE PRINCIPAL
# =============================
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.title("🤖 PrimeBud 1.0")
    modo = st.sidebar.selectbox("Modo de operação", [
        "Chat", "Imagem", "Professor", "Designer", "Codificador", "Estratégias"
    ])

    # ==================================================
    # MODO CHAT / GROQ / GPT-OSS 120B
    # ==================================================
    if modo == "Chat":
        st.subheader("💬 Conversa Inteligente (Groq/GPT-OSS 120B)")
        prompt = st.text_area("Digite sua mensagem:")
        if st.button("Enviar"):
            if prompt.strip():
                with st.spinner("Gerando resposta..."):
                    try:
                        response = requests.post(
                            "http://localhost:8000/v1/chat/completions",
                            headers={"Content-Type": "application/json"},
                            json={
                                "model": "gpt-oss-120b",
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.7
                            }
                        )
                        data = response.json()
                        st.markdown(data["choices"][0]["message"]["content"])
                    except Exception as e:
                        st.error(f"Erro na conexão com o modelo local: {e}")

    # ==================================================
    # MODO IMAGEM (OpenAI opcional)
    # ==================================================
    elif modo == "Imagem":
        st.subheader("🎨 Gerador de Imagens (gpt-image-1)")
        prompt = st.text_input("Descrição da imagem:", "um boneco palito sorrindo")
        size = st.selectbox("Tamanho", ["256x256", "512x512", "1024x1024"])

        if st.button("Criar Imagem"):
            try:
                # Import protegido — só tenta se a lib existir
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                    result = client.images.generate(
                        model="gpt-image-1",
                        prompt=prompt,
                        size=size
                    )
                    image_base64 = result.data[0].b64_json
                    image_bytes = base64.b64decode(image_base64)
                    img = Image.open(BytesIO(image_bytes))
                    st.image(img, caption="Imagem gerada com sucesso!", use_column_width=True)
                except ModuleNotFoundError:
                    st.error("⚠️ O módulo 'openai' não está instalado. "
                             "Execute `pip install openai` para habilitar o gerador de imagens.")
            except Exception as e:
                st.error(f"Erro ao gerar imagem: {e}")

    # ==================================================
    # OUTROS MODOS (Professor, Designer, Codificador, Estratégias)
    # ==================================================
    else:
        st.subheader(f"🧩 Modo {modo}")
        user_input = st.text_area("Descreva o que deseja:")
        if st.button("Gerar Resposta"):
            try:
                response = requests.post(
                    "http://localhost:8000/v1/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": "gpt-oss-120b",
                        "messages": [
                            {"role": "system", "content": f"Você está no modo {modo} do PrimeBud."},
                            {"role": "user", "content": user_input}
                        ],
                        "temperature": 0.8
                    }
                )
                data = response.json()
                st.markdown(data["choices"][0]["message"]["content"])
            except Exception as e:
                st.error(f"Erro na conexão com o servidor local: {e}")

else:
    st.warning("Faça login para acessar o PrimeBud.")

