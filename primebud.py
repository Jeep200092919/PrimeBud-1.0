import streamlit as st
import requests
import json
import os
import time

# ============================================
# CONFIGURAÇÕES INICIAIS
# ============================================
st.set_page_config(page_title="PrimeBud 1.0 — GPT-OSS 120B", page_icon="🧠", layout="wide")

OLLAMA_URL = "http://localhost:11434/api/chat"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL = st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "gpt-oss-120b"))

GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-1.0"

# ============================================
# SISTEMA DE LOGIN
# ============================================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"teste": {"senha": "0000", "plano": "Free"}}

if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "plano" not in st.session_state:
    st.session_state.plano = None

if st.session_state.usuario is None:
    st.title("PrimeBud 1.0 — GPT-OSS 120B")
    st.link_button("Ver no GitHub", GITHUB_URL)
    st.divider()

    abas = st.tabs(["Entrar", "Criar conta", "Convidado (Ultra)"])

    with abas[0]:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            db = st.session_state.usuarios
            if u in db and db[u]["senha"] == p:
                st.session_state.usuario = u
                st.session_state.plano = db[u]["plano"]
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with abas[1]:
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
                st.rerun()

    with abas[2]:
        if st.button("Entrar como Convidado (Ultra)"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.rerun()
    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ============================================
# BACKEND — GROQ + OLLAMA
# ============================================
def usar_groq():
    return bool(GROQ_API_KEY)

def chat_api(model, messages, options=None, timeout=120):
    """Chamada direta à API, sem Stream."""
    if usar_groq():
        payload = {"model": model, "messages": messages, "stream": False}
        if options:
            payload.update(options)
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        try:
            r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Erro Groq] {e}"
    else:
        payload = {"model": model, "stream": False, "messages": messages}
        if options:
            payload["options"] = options
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            data = r.json()
            return data.get("message", {}).get("content", "[Erro Ollama]")
        except Exception as e:
            return f"[Erro Ollama] {e}"

# ============================================
# MODOS
# ============================================
MODOS_DESC = {
    "⚡ Flash": "Respostas curtas e diretas.",
    "🔵 Normal": "Respostas equilibradas e coerentes.",
    "🍃 Econômico": "Respostas rápidas e eficientes.",
    "💬 Mini": "Conversas simples e objetivas.",
    "💎 Pro (Beta)": "Código + breve explicação.",
    "☄️ Ultra (Beta)": "Respostas longas e analíticas.",
    "✍️ Escritor": "Textos criativos e claros.",
    "🏫 Escola": "Explicações didáticas e acessíveis.",
    "👨‍🏫 Professor": "Explicações detalhadas e exemplos.",
    "🎨 Designer": "Ideias visuais e UI/UX.",
    "💻 Codificador": "Código limpo e comentado.",
    "🧩 Estratégias": "Planos com metas e raciocínio tático.",
}

# ============================================
# GERAÇÃO DE RESPOSTA
# ============================================
def gerar_resposta(modo, msg, historico):
    base = MODOS_DESC.get(modo, "Responda com clareza e objetividade.")
    # Fase 1: pensamento interno
    pensamento_prompt = [
        {"role": "system", "content": "Explique brevemente seu raciocínio interno, de forma lógica e profissional. Não formule a resposta final, apenas o raciocínio."},
        {"role": "user", "content": f"{msg}\n\n[MODO ATUAL: {modo}] {base}"}
    ]
    pensamento = chat_api(GROQ_MODEL, pensamento_prompt, {"temperature": 0.25, "max_tokens": 400})

    # Fase 2: resposta final
    mensagens = [{"role": "system", "content": "Você é o PrimeBud — uma IA analítica, objetiva e profissional."}]
    for m in historico:
        if m["autor"] == "Você":
            mensagens.append({"role": "user", "content": m["texto"]})
        else:
            mensagens.append({"role": "assistant", "content": m["texto"]})
    mensagens.append({"role": "user", "content": msg})
    resposta_final = chat_api(GROQ_MODEL, mensagens, {"temperature": 0.35, "max_tokens": 1200})

    return pensamento, resposta_final

# ============================================
# ESTADO DE CHAT
# ============================================
if "chats" not in st.session_state:
    st.session_state.chats = [{"nome": "Chat 1", "historico": []}]
if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = 0

def novo_chat():
    n = len(st.session_state.chats) + 1
    st.session_state.chats.append({"nome": f"Chat {n}", "historico": []})
    st.session_state.chat_atual = n - 1
    st.rerun()

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.title(f"PrimeBud — {usuario}")
    st.caption(f"Plano atual: {plano}")
    planos = ["Free", "Pro", "Ultra", "Trabalho", "Professor"]
    novo_plano = st.selectbox("Alterar plano", planos, index=planos.index(plano))
    if st.button("Atualizar plano"):
        st.session_state.plano = novo_plano
        st.session_state.usuarios[usuario]["plano"] = novo_plano
        st.success("Plano alterado com sucesso.")
        st.rerun()

    st.link_button("Repositório GitHub", GITHUB_URL)
    st.divider()

    if st.button("Novo chat"):
        novo_chat()

    nomes = [c["nome"] for c in st.session_state.chats]
    idx = st.radio("Chats ativos", list(range(len(nomes))),
                   index=st.session_state.chat_atual,
                   format_func=lambda i: nomes[i])
    st.session_state.chat_atual = idx

    st.divider()
    modo = st.selectbox("Modo:", list(MODOS_DESC.keys()), index=1)
    st.caption(MODOS_DESC.get(modo, ""))

# ============================================
# INTERFACE PRINCIPAL
# ============================================
chat = st.session_state.chats[st.session_state.chat_atual]
st.markdown(f"### Sessão: {chat['nome']}")

for m in chat["historico"]:
    bg = "#181818" if m["autor"] == "Você" else "#242424"
    st.markdown(
        f"<div style='background:{bg};color:#eaeaea;padding:10px;border-radius:6px;margin:5px 0;'>"
        f"<b>{m['autor']}:</b><br>{m['texto']}</div>",
        unsafe_allow_html=True
    )

msg = st.chat_input("Digite sua mensagem...")
if msg:
    chat["historico"].append({"autor": "Você", "texto": msg})
    with st.spinner("Analisando contexto e raciocinando..."):
        pensamento, resposta = gerar_resposta(modo, msg, chat["historico"])

    st.markdown(f"<div style='background:#2b2b2b;color:#cfcfcf;padding:10px;border-radius:6px;margin:5px 0;'><b>Pensamento interno:</b><br>{pensamento}</div>", unsafe_allow_html=True)
    time.sleep(0.8)
    chat["historico"].append({"autor": "PrimeBud", "texto": resposta})
    st.rerun()

