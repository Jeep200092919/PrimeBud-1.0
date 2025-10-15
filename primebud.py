# =====================================
# 🤖 PRIMEBUD 1.0 - COMPLETO E CORRIGIDO
# =====================================

import streamlit as st
from openai import OpenAI
from datetime import datetime
import json
import os
import hashlib
from io import BytesIO
from PIL import Image
import base64

# =============================
# CONFIGURAÇÕES INICIAIS
# =============================
st.set_page_config(
    page_title="PrimeBud 1.0",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = load_users()

# =============================
# LOGIN E REGISTRO
# =============================
st.sidebar.title("🔐 Login do PrimeBud")

menu = st.sidebar.radio("Escolha uma opção", ["Entrar", "Registrar"])

if menu == "Registrar":
    st.sidebar.subheader("Criar nova conta")
    new_user = st.sidebar.text_input("Usuário")
    new_pass = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Registrar"):
        if new_user in users:
            st.sidebar.error("Usuário já existe!")
        else:
            users[new_user] = hash_password(new_pass)
            save_users(users)
            st.sidebar.success("Conta criada com sucesso! Faça login para continuar.")

if menu == "Entrar":
    st.sidebar.subheader("Acesso")
    username = st.sidebar.text_input("Usuário")
    password = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if username in users and users[username] == hash_password(password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.sidebar.success(f"Bem-vindo(a), {username}!")
        else:
            st.sidebar.error("Usuário ou senha incorretos.")

# =============================
# ÁREA PRINCIPAL (APÓS LOGIN)
# =============================
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.title("🤖 PrimeBud 1.0")
    st.markdown("**Assistente Inteligente Integrado**")

    # Configuração da API
    if "OPENAI_API_KEY" not in st.secrets:
        st.warning("Adicione sua chave da OpenAI no arquivo secrets.toml!")
    else:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Modo de operação
    modo = st.sidebar.selectbox(
        "Escolha o modo de operação:",
        ["Chat", "Imagem", "Professor", "Designer", "Codificador", "Estratégias"]
    )

    # =========================================
    # MODO CHAT NORMAL
    # =========================================
    if modo == "Chat":
        st.subheader("💬 Conversa Inteligente")

        user_input = st.text_area("Digite sua mensagem:")
        if st.button("Enviar"):
            if user_input.strip():
                with st.spinner("Gerando resposta..."):
                    resposta = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": user_input}]
                    )
                    st.markdown(resposta.choices[0].message.content)

    # =========================================
    # MODO GERADOR DE IMAGEM
    # =========================================
    elif modo == "Imagem":
        st.subheader("🎨 Criador de Imagens (GPT-Image-1)")

        prompt = st.text_input("Descreva a imagem que deseja criar:", "um boneco palito sorrindo")
        tamanho = st.selectbox("Tamanho da imagem:", ["256x256", "512x512", "1024x1024"])

        if st.button("🎨 Criar Imagem"):
            try:
                with st.spinner("Gerando imagem..."):
                    result = client.images.generate(
                        model="gpt-image-1",
                        prompt=prompt,
                        size=tamanho
                    )
                    image_base64 = result.data[0].b64_json
                    image_bytes = base64.b64decode(image_base64)
                    image = Image.open(BytesIO(image_bytes))
                    st.image(image, caption="Imagem gerada com sucesso!", use_column_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar imagem: {e}")

    # =========================================
    # MODO PROFESSOR
    # =========================================
    elif modo == "Professor":
        st.subheader("🧑‍🏫 Modo Professor")
        tema = st.text_input("Tema da aula:")
        if st.button("Gerar Plano de Aula"):
            resposta = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um professor especialista em planejamento de aulas criativas."},
                    {"role": "user", "content": f"Crie um plano de aula sobre {tema} para alunos do ensino fundamental."}
                ]
            )
            st.markdown(resposta.choices[0].message.content)

    # =========================================
    # MODO DESIGNER
    # =========================================
    elif modo == "Designer":
        st.subheader("🎨 Modo Designer Criativo")
        descricao = st.text_area("Descreva o design que deseja criar:")
        if st.button("Gerar Ideia de Design"):
            resposta = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um designer criativo especializado em ideias visuais."},
                    {"role": "user", "content": descricao}
                ]
            )
            st.markdown(resposta.choices[0].message.content)

    # =========================================
    # MODO CODIFICADOR
    # =========================================
    elif modo == "Codificador":
        st.subheader("💻 Modo Codificador")
        codigo = st.text_area("Descreva o que você quer programar:")
        if st.button("Gerar Código"):
            resposta = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um programador especialista em Python e JavaScript."},
                    {"role": "user", "content": codigo}
                ]
            )
            st.code(resposta.choices[0].message.content, language="python")

    # =========================================
    # MODO ESTRATÉGIAS
    # =========================================
    elif modo == "Estratégias":
        st.subheader("🧭 Modo Estratégias")
        objetivo = st.text_input("Qual é o seu objetivo?")
        if st.button("Gerar Estratégia"):
            resposta = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um consultor estratégico especialista em planejamento e inovação."},
                    {"role": "user", "content": f"Crie uma estratégia detalhada para alcançar o seguinte objetivo: {objetivo}"}
                ]
            )
            st.markdown(resposta.choices[0].message.content)

else:
    st.warning("Faça login para acessar o PrimeBud.")

