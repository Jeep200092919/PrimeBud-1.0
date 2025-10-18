import streamlit as st
import requests
import json
import os

# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================
st.set_page_config(
    page_title="PrimeBud 1.5 — GPT-OSS 120B",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CORES E ESTILO
# ============================================================
PRIMARY_BG = "#0f0f10"
PRIMARY_TEXT = "#ffffff"
ACCENT_COLOR = "#ff7a00"

st.markdown(f"""
<style>
.stApp {{ background-color: {PRIMARY_BG}; color: {PRIMARY_TEXT}; }}
.stTextInput>div>div>input, textarea {{ color: {PRIMARY_TEXT} !important; background-color: #1a1a1a; border: 1px solid {ACCENT_COLOR}; }}
.stButton>button {{ color: {PRIMARY_TEXT}; border: 1px solid {ACCENT_COLOR}; background-color: transparent; }}
.stButton>button:hover {{ background-color: {ACCENT_COLOR}33; }}
.block-container {{ padding-top: 0.5rem; }}
.sidebar .stButton>button {{ width: 100%; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CHAVES E ENDPOINTS
# ============================================================
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL = st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "gpt-oss-120b"))
GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-1.0"

# ============================================================
# LOGIN / CONTAS
# ============================================================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {}
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "plano" not in st.session_state:
    st.session_state.plano = None

if st.session_state.usuario is None:
    st.markdown(f"<h1 style='text-align:center;color:{ACCENT_COLOR};'>PrimeBud 1.5 — GPT-OSS 120B</h1>", unsafe_allow_html=True)
    st.link_button("Repositório GitHub", GITHUB_URL)
    st.divider()

    abas = st.tabs(["Entrar", "Criar conta", "Convidado"])

    with abas[0]:
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

    with abas[1]:
        novo_u = st.text_input("Novo usuário")
        nova_s = st.text_input("Nova senha", type="password")
        plano_i = st.selectbox("Plano", ["Free", "Pro", "Ultra"])
        if st.button("Criar conta"):
            db = st.session_state.usuarios
            if novo_u in db:
                st.warning("Usuário já existe.")
            else:
                db[novo_u] = {"senha": nova_s, "plano": plano_i}
                st.session_state.usuario = novo_u
                st.session_state.plano = plano_i
                st.success(f"Conta criada: {novo_u} ({plano_i}).")
                st.rerun()

    with abas[2]:
        if st.button("Entrar como Convidado"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.success("Entrou como convidado (todos os modos liberados).")
            st.rerun()

    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ============================================================
# MODOS (RENOMEADOS)
# ============================================================
MODOS_DESC = {
    "Primebud 1.0 Flash": "Respostas curtas e diretas.",
    "Primebud 1.0": "Respostas equilibradas e coerentes.",
    "Primebud 1.0 leve": "Respostas rápidas e eficientes.",
    "Primebud 1.0 Pro": "Código + explicações claras.",
    "Primebud 1.0 Ultra": "Respostas longas e analíticas.",
    "Primebud 1.0 Helper": "Perfis: Escola, Professor, Designer, Codificador e Estratégias."
}

SYSTEM_PROMPT = (
    "Você é o PrimeBud 1.5 — uma IA analítica, lógica e objetiva. "
    "Responda com clareza, raciocínio completo e linguagem profissional."
)

THINK_PROMPT = (
    "Descreva seu raciocínio interno em até 5 frases técnicas, "
    "sem entregar a resposta final. Seja objetivo e preciso."
)

# ============================================================
# HISTÓRICO
# ============================================================
if "chats" not in st.session_state:
    st.session_state.chats = [{"nome": "Chat 1", "historico": []}]
if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = 0

def novo_chat():
    n = len(st.session_state.chats) + 1
    st.session_state.chats.append({"nome": f"Chat {n}", "historico": []})
    st.session_state.chat_atual = n - 1
    st.rerun()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.subheader(f"Usuário: {usuario}")
    st.caption(f"Plano atual: {plano}")
    planos = ["Free", "Pro", "Ultra"]
    novo_plano = st.selectbox("Alterar plano", planos, index=planos.index(plano))
    if st.button("Atualizar plano"):
        st.session_state.plano = novo_plano
        st.session_state.usuarios[usuario]["plano"] = novo_plano
        st.success("Plano alterado.")
        st.rerun()

    st.divider()
    st.button("Novo Chat", on_click=novo_chat)

    nomes = [c["nome"] for c in st.session_state.chats]
    idx = st.radio("Seus chats", list(range(len(nomes))),
                   index=st.session_state.chat_atual,
                   format_func=lambda i: nomes[i])
    st.session_state.chat_atual = idx

    st.divider()
    modo = st.selectbox("Modo de resposta", list(MODOS_DESC.keys()), index=1)
    st.caption(MODOS_DESC[modo])
    pensamento_visivel = st.toggle("Mostrar pensamento interno", value=True)

# ============================================================
# FUNÇÕES GROQ
# ============================================================
def corrigir_acentos(texto):
    try:
        return texto.encode("latin1").decode("utf-8")
    except Exception:
        return texto

def chat_stream(messages, temperature=0.35, max_tokens=4000, timeout=300):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": True,
        "max_tokens": max_tokens,
    }
    with requests.post(GROQ_URL, headers=headers, json=payload, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        r.encoding = "utf-8"
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data = line[len("data: ") :]
            if data.strip() == "[DONE]":
                break
            try:
                obj = json.loads(data)
                delta = obj["choices"][0]["delta"].get("content", "")
                if delta:
                    yield corrigir_acentos(delta)
            except:
                continue

# ============================================================
# INTERFACE PRINCIPAL
# ============================================================
chat = st.session_state.chats[st.session_state.chat_atual]
st.markdown(f"<h3 style='color:{ACCENT_COLOR};'>Sessão: {chat['nome']}</h3>", unsafe_allow_html=True)

for m in chat["historico"]:
    border = f"1px solid {ACCENT_COLOR}" if m["autor"] == "PrimeBud" else "none"
    bg = "#1a1a1a" if m["autor"] == "Você" else "#1c1c1c"
    st.markdown(
        f"<div style='background:{bg};border:{border};color:{PRIMARY_TEXT};padding:10px;border-radius:8px;margin:6px 0;'>"
        f"<b>{m['autor']}:</b> {m['texto']}</div>",
        unsafe_allow_html=True,
    )

msg = st.chat_input("Digite sua mensagem...")

if msg:
    chat["historico"].append({"autor": "Você", "texto": msg})
    st.session_state.chats[st.session_state.chat_atual]["historico"] = chat["historico"]

    answer_box = st.empty()
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in chat["historico"]:
        role = "user" if h["autor"] == "Você" else "assistant"
        mensagens.append({"role": role, "content": h["texto"]})

    full = ""
    try:
        for token in chat_stream(mensagens):
            full += token
            answer_box.markdown(
                f"<div style='background:#1c1c1c;border:1px solid {ACCENT_COLOR};color:{PRIMARY_TEXT};padding:10px;border-radius:8px;'>"
                f"<b>PrimeBud 1.5:</b><br>{full}</div>",
                unsafe_allow_html=True,
            )
    except Exception as e:
        full = f"[Erro: {e}]"
        answer_box.markdown(f"<div>{full}</div>", unsafe_allow_html=True)

    chat["historico"].append({"autor": "PrimeBud", "texto": full})
    st.session_state.chats[st.session_state.chat_atual]["historico"] = chat["historico"]

