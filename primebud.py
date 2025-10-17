# ===========================================
# 🤖 PRIMEBUD 1.0 - COMPLETO E CORRIGIDO (PLANOS + MODOS)
# ===========================================

import streamlit as st
import json, os, hashlib, base64
from io import BytesIO
from PIL import Image
from datetime import datetime

# =============================
# CONFIGURAÇÃO INICIAL
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

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

users = load_users()

# =============================
# LOGIN / CONVIDADO
# =============================
st.sidebar.title("🔐 Login do PrimeBud")

menu = st.sidebar.radio("Selecione", ["Entrar", "Registrar", "Convidado"])

if menu == "Registrar":
    u = st.sidebar.text_input("Novo usuário")
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Registrar"):
        if u in users:
            st.sidebar.error("Usuário já existe!")
        else:
            users[u] = hash_password(p)
            save_users(users)
            st.sidebar.success("Conta criada com sucesso!")

elif menu == "Entrar":
    u = st.sidebar.text_input("Usuário")
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in users and users[u] == hash_password(p):
            st.session_state["user"] = u
            st.session_state["logged"] = True
            st.sidebar.success(f"Bem-vindo(a), {u}!")
        else:
            st.sidebar.error("Usuário ou senha incorretos.")

elif menu == "Convidado":
    if st.sidebar.button("Entrar como Convidado"):
        st.session_state["user"] = "Convidado"
        st.session_state["logged"] = True
        st.sidebar.success("Acesso concedido!")

# =============================
# PLANOS
# =============================
planos_info = {
    "🆓 Free": {
        "icone": "💬",
        "preco": "R$ 0,00 / mês",
        "tokens": "100 000 tokens",
        "modos": "⚡ Flash, 🔵 Normal",
        "descricao": "Acesso básico, ideal para iniciantes. Limite mensal e apenas modos principais."
    },
    "⭐ Pro": {
        "icone": "💻",
        "preco": "R$ 10,00 / mês",
        "tokens": "500 000 tokens",
        "modos": "⚡ Flash, 🔵 Normal, 🍃 Econômico, 💬 Mini",
        "descricao": "Plano intermediário — respostas rápidas e mais modos. Ideal para estudo e uso cotidiano."
    },
    "👑 Deluxe": {
        "icone": "💎",
        "preco": "R$ 20,00 / mês",
        "tokens": "1 000 000 tokens",
        "modos": "⚡ Flash, 🔵 Normal, 🍃 Econômico, 💬 Mini, 💎 Pro, ☄️ Ultra",
        "descricao": "Acesso completo. Todos os modos, velocidade máxima e sem limites. Ideal para criadores e uso profissional."
    }
}

plano_escolhido = st.sidebar.selectbox("💎 Escolha seu plano:", list(planos_info.keys()))
plano = planos_info[plano_escolhido]

with st.sidebar.expander("📋 Detalhes do Plano"):
    st.markdown(f"**Plano:** {plano_escolhido}")
    st.markdown(f"**Ícone:** {plano['icone']}")
    st.markdown(f"**Preço:** {plano['preco']}")
    st.markdown(f"**Tokens Mensais:** {plano['tokens']}")
    st.markdown(f"**Modos Disponíveis:** {plano['modos']}")
    st.markdown(f"**Descrição:** {plano['descricao']}")

# =============================
# ÁREA PRINCIPAL
# =============================
if "logged" in st.session_state and st.session_state["logged"]:
    st.title("🤖 PRIMEBUD 1.0")
    st.caption(f"Modo ativo: **{plano_escolhido}** • Usuário: **{st.session_state['user']}**")

    modo = st.sidebar.selectbox(
        "Selecione o modo:",
        ["⚡ Flash", "🔵 Normal", "🍃 Econômico", "💬 Mini", "💎 Pro", "☄️ Ultra", 
         "Professor", "Designer", "Codificador", "Estratégias", "Imagem"]
    )

    # =====================================
    # FLASH MODE
    # =====================================
    if modo == "⚡ Flash":
        st.subheader("⚡ Modo Flash (respostas instantâneas)")
        pergunta = st.text_area("Digite sua pergunta:")
        if st.button("Responder"):
            if pergunta.strip():
                st.success(f"Resposta rápida para: **{pergunta}**")
            else:
                st.warning("Digite algo primeiro.")

    # =====================================
    # NORMAL MODE
    # =====================================
    elif modo == "🔵 Normal":
        st.subheader("🔵 Modo Normal")
        texto = st.text_area("Digite seu texto:")
        if st.button("Gerar resposta"):
            if texto.strip():
                st.info(f"🧠 Processando: **{texto}**")
            else:
                st.warning("Digite algo antes.")

    # =====================================
    # ECONÔMICO
    # =====================================
    elif modo == "🍃 Econômico":
        st.subheader("🍃 Modo Econômico (baixo custo de tokens)")
        conteudo = st.text_area("Entrada de texto:")
        if st.button("Executar"):
            if conteudo.strip():
                st.success("💡 Resposta leve e econômica gerada com sucesso.")
            else:
                st.warning("Digite um texto primeiro.")

    # =====================================
    # MINI
    # =====================================
    elif modo == "💬 Mini":
        st.subheader("💬 Modo Mini (respostas curtas)")
        pergunta = st.text_input("Pergunta:")
        if st.button("Gerar Mini Resposta"):
            if pergunta.strip():
                st.info(f"👉 Mini resposta: {pergunta[:50]}...")
            else:
                st.warning("Digite algo.")

    # =====================================
    # PRO
    # =====================================
    elif modo == "💎 Pro":
        st.subheader("💎 Modo Pro (respostas detalhadas)")
        comando = st.text_area("Digite sua solicitação detalhada:")
        if st.button("Executar Pro"):
            if comando.strip():
                st.success("✅ Resposta detalhada gerada com sucesso.")
            else:
                st.warning("Digite algo antes.")

    # =====================================
    # ULTRA
    # =====================================
    elif modo == "☄️ Ultra":
        st.subheader("☄️ Modo Ultra (potência máxima)")
        texto = st.text_area("Digite sua entrada:")
        if st.button("Rodar Ultra"):
            if texto.strip():
                st.success("🚀 Ultra processamento concluído com sucesso.")
            else:
                st.warning("Digite um comando primeiro.")

    # =====================================
    # PROFESSOR
    # =====================================
    elif modo == "Professor":
        st.subheader("🧑‍🏫 Modo Professor")
        tema = st.text_input("Tema da aula:")
        if st.button("Gerar Plano de Aula"):
            if tema.strip():
                st.success(f"📘 Plano de aula gerado sobre: **{tema}**")
            else:
                st.warning("Digite o tema.")

    # =====================================
    # DESIGNER
    # =====================================
    elif modo == "Designer":
        st.subheader("🎨 Modo Designer")
        ideia = st.text_area("Descreva o design:")
        if st.button("Gerar Ideia"):
            if ideia.strip():
                st.info(f"💡 Ideia criada com base em: **{ideia}**")
            else:
                st.warning("Digite algo.")

    # =====================================
    # CODIFICADOR
    # =====================================
    elif modo == "Codificador":
        st.subheader("💻 Modo Codificador")
        comando = st.text_area("Descreva o código que deseja gerar:")
        if st.button("Gerar Código"):
            if comando.strip():
                st.code(f"# Código baseado em: {comando}\nprint('PrimeBud 1.0 funcionando!')", language="python")
            else:
                st.warning("Descreva o código desejado.")

    # =====================================
    # ESTRATÉGIAS
    # =====================================
    elif modo == "Estratégias":
        st.subheader("🧭 Modo Estratégias")
        objetivo = st.text_input("Qual é o seu objetivo?")
        if st.button("Gerar Estratégia"):
            if objetivo.strip():
                st.success(f"🎯 Estratégia para atingir: **{objetivo}**")
            else:
                st.warning("Digite um objetivo.")

    # =====================================
    # IMAGEM
    # =====================================
    elif modo == "Imagem":
        st.subheader("🖼️ Gerador de Imagens")
        prompt = st.text_input("Descreva a imagem:", "um boneco palito sorrindo")
        size = st.selectbox("Tamanho:", ["256x256", "512x512", "1024x1024"])
        if st.button("Gerar Imagem"):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                result = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)
                img_data = base64.b64decode(result.data[0].b64_json)
                img = Image.open(BytesIO(img_data))
                st.image(img, caption="Imagem gerada com sucesso!", use_column_width=True)
            except ModuleNotFoundError:
                st.error("⚠️ Instale a biblioteca `openai` para usar o gerador de imagens.")
            except Exception as e:
                st.error(f"Erro ao gerar imagem: {e}")

else:
    st.warning("Faça login ou entre como convidado para acessar o PrimeBud.")

