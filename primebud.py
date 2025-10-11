import streamlit as st
import requests
import json
import os

# ==============================
# CONFIGURAÇÕES INICIAIS
# ==============================
st.set_page_config(page_title="PrimeBud Turbo 1.2", page_icon="🤖", layout="wide")

# Endpoint do Ollama local
OLLAMA_URL = "http://localhost:11434/api/chat"

# Modelo padrão (você pode mudar aqui ou na aba Secrets)
MODEL_DEFAULT = st.secrets.get("MODEL_NAME", os.getenv("MODEL_NAME", "llama3.3:70b"))

# Link do projeto
GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-1.0"

# ==============================
# LOGIN / CONTAS
# ==============================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {
        "admin": {"senha": "1234", "plano": "Ultra"},
        "teste": {"senha": "0000", "plano": "Free"},
    }
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "plano" not in st.session_state:
    st.session_state.plano = None

if st.session_state.usuario is None:
    st.title("🤖 PrimeBud Turbo 1.2 — Login")
    st.link_button("🌐 Ver no GitHub", GITHUB_URL)
    st.markdown("---")

    tabs = st.tabs(["Entrar", "Criar conta", "Convidado (Ultra)"])

    with tabs[0]:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            db = st.session_state.usuarios
            if u in db and db[u]["senha"] == p:
                st.session_state.usuario = u
                st.session_state.plano = db[u]["plano"]
                st.success(f"Bem-vindo, {u}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with tabs[1]:
        novo_u = st.text_input("Novo usuário")
        nova_s = st.text_input("Nova senha", type="password")
        plano_i = st.selectbox("Plano inicial", ["Free", "Pro", "Ultra", "Trabalho", "Professor"])
        if st.button("Criar conta"):
            db = st.session_state.usuarios
            if novo_u in db:
                st.warning("Usuário já existe.")
            else:
                db[novo_u] = {"senha": nova_s, "plano": plano_i}
                st.session_state.usuario = novo_u
                st.session_state.plano = plano_i
                st.success(f"Conta criada e login automático como {novo_u} ({plano_i}).")
                st.rerun()

    with tabs[2]:
        if st.button("Entrar como Convidado (Ultra)"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.success("Entrou como convidado — Plano Ultra liberado.")
            st.rerun()
    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ==============================
# BACKEND — OLLAMA LOCAL
# ==============================
def chat_api(model: str, prompt: str, options: dict | None = None, timeout: int = 120) -> str:
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": "Você é o PrimeBud Turbo — claro, direto e útil."},
            {"role": "user", "content": prompt},
        ],
    }
    if options:
        payload["options"] = options

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        data = r.json()
        return data.get("message", {}).get("content", "⚠️ Erro: resposta vazia do Ollama.")
    except Exception as e:
        return f"❌ Erro ao conectar ao Ollama: {str(e)}"

# ==============================
# MODOS E CONFIGURAÇÕES
# ==============================
MODOS_DESC = {
    "⚡ Flash": "Respostas curtíssimas e instantâneas.",
    "🔵 Normal": "Respostas equilibradas e naturais.",
    "🍃 Econômico": "Respostas curtas e otimizadas.",
    "💬 Mini": "Conversa leve e simples.",
    "💎 Pro (Beta)": "Código + breve explicação.",
    "☄️ Ultra (Beta)": "Mais tokens e contexto.",
    "✍️ Escritor": "Texto criativo de 5–10 linhas.",
    "🏫 Escola": "Explicações didáticas do Ensino Médio.",
    "👨‍🏫 Professor": "Aulas, resumos e exemplos práticos.",
    "🎨 Designer": "Ideias visuais, UI e UX.",
    "💻 Codificador": "Código limpo + explicação curta.",
    "🧩 Estratégias": "Planos práticos com metas e ações.",
}

def gerar_resposta(modo: str, msg: str) -> str:
    base_prompt = MODOS_DESC.get(modo, "Seja direto e útil.")
    full_prompt = f"{base_prompt}\n\n{msg}"

    config = {
        "⚡ Flash": {"temperature": 0.3, "num_predict": 100},
        "🔵 Normal": {"temperature": 0.5, "num_predict": 250},
        "🍃 Econômico": {"temperature": 0.4, "num_predict": 120},
        "💬 Mini": {"temperature": 0.6, "num_predict": 150},
        "💎 Pro (Beta)": {"temperature": 0.35, "num_predict": 240},
        "☄️ Ultra (Beta)": {"temperature": 0.7, "num_predict": 400},
        "✍️ Escritor": {"temperature": 0.9, "num_predict": 260},
        "🏫 Escola": {"temperature": 0.6, "num_predict": 250},
        "👨‍🏫 Professor": {"temperature": 0.4, "num_predict": 320},
        "🎨 Designer": {"temperature": 0.95, "num_predict": 220},
        "💻 Codificador": {"temperature": 0.2, "num_predict": 280},
        "🧩 Estratégias": {"temperature": 0.6, "num_predict": 260},
    }
    opt = config.get(modo, {"temperature": 0.5, "num_predict": 200})
    return chat_api(MODEL_DEFAULT, full_prompt, opt)

# ==============================
# GERENCIAMENTO DE CHATS
# ==============================
if "chats" not in st.session_state:
    st.session_state.chats = [{"nome": "Chat 1", "historico": []}]
if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = 0

def novo_chat():
    n = len(st.session_state.chats) + 1
    st.session_state.chats.append({"nome": f"Chat {n}", "historico": []})
    st.session_state.chat_atual = n - 1
    st.success(f"Novo chat criado — Chat {n}")
    st.rerun()

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.title(f"🤖 PrimeBud — {usuario}")
    st.markdown(f"**Plano:** {plano}")
    st.link_button("🌐 GitHub", GITHUB_URL)

    st.divider()
    if st.button("➕ Novo chat"):
        novo_chat()

    nomes = [c["nome"] for c in st.session_state.chats]
    idx = st.radio("Seus chats:", list(range(len(nomes))),
                   index=st.session_state.chat_atual,
                   format_func=lambda i: nomes[i])
    st.session_state.chat_atual = idx

    st.divider()
    modos_por_plano = {
        "Free": ["💬 Mini", "🍃 Econômico", "✍️ Escritor", "🏫 Escola"],
        "Pro": ["⚡ Flash", "🔵 Normal", "💎 Pro (Beta)", "✍️ Escritor", "🏫 Escola"],
        "Ultra": list(MODOS_DESC.keys()),
        "Trabalho": ["👨‍🏫 Professor", "🎨 Designer", "💻 Codificador", "🧩 Estratégias", "✍️ Escritor"],
        "Professor": ["👨‍🏫 Professor", "🏫 Escola", "✍️ Escritor"],
    }
    lista = modos_por_plano.get(plano, modos_por_plano["Ultra"])
    modo = st.selectbox("Modo:", lista, index=0)
    st.caption(MODOS_DESC.get(modo, ""))

# ==============================
# ÁREA PRINCIPAL DO CHAT
# ==============================
chat = st.session_state.chats[st.session_state.chat_atual]
st.markdown(f"### 💬 {chat['nome']}")

for m in chat["historico"]:
    bubble_bg = "#2b313e" if m["autor"] == "Você" else "#ececf1"
    color = "#fff" if m["autor"] == "Você" else "#000"
    st.markdown(
        f"<div style='background:{bubble_bg};color:{color};padding:10px;border-radius:10px;margin:6px 0;'>"
        f"<b>{m['autor']}:</b> {m['texto']}</div>",
        unsafe_allow_html=True
    )

msg = st.chat_input("Digite sua mensagem...")
if msg:
    chat["historico"].append({"autor": "Você", "texto": msg})
    with st.spinner("Processando..."):
        resposta = gerar_resposta(modo, msg)
    chat["historico"].append({"autor": "PrimeBud", "texto": resposta})
    st.rerun()

