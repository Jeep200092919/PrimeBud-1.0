import streamlit as st
import requests
import json
import os

# ============================================
# CONFIGURAÇÕES INICIAIS
# ============================================
st.set_page_config(page_title="PrimeBud 1.0 — GPT-OSS 120B", page_icon="🧠", layout="wide")

# Endpoints
OLLAMA_URL = "http://localhost:11434/api/chat"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Secrets / Env
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL = st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "gpt-oss-120b"))

GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-1.0"

# ============================================
# SISTEMA DE LOGIN
# ============================================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {
        "teste": {"senha": "0000", "plano": "Free"},
    }

if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "plano" not in st.session_state:
    st.session_state.plano = None

if st.session_state.usuario is None:
    st.title("PrimeBud 1.0 — GPT-OSS 120B")
    st.link_button("Ver no GitHub", GITHUB_URL)
    st.divider()

    aba = st.tabs(["Entrar", "Criar conta", "Convidado (Ultra)"])

    # Entrar
    with aba[0]:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            db = st.session_state.usuarios
            if u in db and db[u]["senha"] == p:
                st.session_state.usuario = u
                st.session_state.plano = db[u]["plano"]
                st.success(f"Bem-vindo, {u}.")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    # Criar conta
    with aba[1]:
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

    # Convidado
    with aba[2]:
        if st.button("Entrar como Convidado (Ultra)"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.success("Entrou como convidado — Plano Ultra liberado.")
            st.rerun()
    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ============================================
# BACKEND — GROQ + OLLAMA
# ============================================
def usar_groq():
    return bool(GROQ_API_KEY)

def _map_options_for_openai_like(options=None):
    options = options or {}
    return {
        "temperature": options.get("temperature", 0.35),
        "top_p": options.get("top_p", 0.9),
        "max_tokens": options.get("num_predict", 800),
    }

def chat_api(model, prompt, historico, options=None, timeout=120):
    """Envia histórico completo do chat."""
    mensagens = [{
        "role": "system",
        "content": (
            "Você é o PrimeBud — uma IA analítica e séria. "
            "Mantenha tom técnico, racional e objetivo. "
            "Explique o raciocínio de forma lógica quando necessário. "
            "Evite informalidades e emojis."
        )
    }]
    for m in historico:
        if m["autor"] == "Você":
            mensagens.append({"role": "user", "content": m["texto"]})
        else:
            mensagens.append({"role": "assistant", "content": m["texto"]})
    mensagens.append({"role": "user", "content": prompt})

    if usar_groq():
        payload = {
            "model": GROQ_MODEL,
            "messages": mensagens,
            "stream": False,
            **_map_options_for_openai_like(options),
        }
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
        try:
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except Exception:
            return f"Erro Groq: {r.text[:300]}"

    payload = {"model": model, "stream": False, "messages": mensagens}
    if options:
        payload["options"] = options
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    data = r.json()
    return data.get("message", {}).get("content", "Erro Ollama.")

# ============================================
# MODOS CLÁSSICOS
# ============================================
MODOS_DESC = {
    "⚡ Flash": "Respostas curtas e diretas.",
    "🔵 Normal": "Respostas equilibradas e coerentes.",
    "🍃 Econômico": "Respostas rápidas com foco em economia de tokens.",
    "💬 Mini": "Conversas leves e simples.",
    "💎 Pro (Beta)": "Código + explicação curta.",
    "☄️ Ultra (Beta)": "Respostas longas e analíticas.",
    "✍️ Escritor": "Textos criativos e descritivos.",
    "🏫 Escola": "Explicações didáticas e simples.",
    "👨‍🏫 Professor": "Explicações detalhadas com exemplos.",
    "🎨 Designer": "Sugestões de design e estética.",
    "💻 Codificador": "Código otimizado com explicação técnica.",
    "🧩 Estratégias": "Planos detalhados e estruturados.",
}

def gerar_resposta(modo, msg, historico):
    base = MODOS_DESC.get(modo, "Responda de forma clara e precisa.")
    full_prompt = f"[Modo: {modo}]\n{base}\n\n{msg}"

    config = {
        "⚡ Flash": {"temperature": 0.2, "num_predict": 200},
        "🔵 Normal": {"temperature": 0.35, "num_predict": 800},
        "🍃 Econômico": {"temperature": 0.3, "num_predict": 400},
        "💬 Mini": {"temperature": 0.5, "num_predict": 300},
        "💎 Pro (Beta)": {"temperature": 0.25, "num_predict": 1000},
        "☄️ Ultra (Beta)": {"temperature": 0.4, "num_predict": 1500},
        "✍️ Escritor": {"temperature": 0.8, "num_predict": 1200},
        "🏫 Escola": {"temperature": 0.5, "num_predict": 1000},
        "👨‍🏫 Professor": {"temperature": 0.35, "num_predict": 1200},
        "🎨 Designer": {"temperature": 0.7, "num_predict": 900},
        "💻 Codificador": {"temperature": 0.2, "num_predict": 1100},
        "🧩 Estratégias": {"temperature": 0.4, "num_predict": 1200},
    }
    opt = config.get(modo, {"temperature": 0.35, "num_predict": 800})
    return chat_api(GROQ_MODEL, full_prompt, historico, opt)

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
        st.success(f"Plano alterado para {novo_plano}.")
        st.rerun()

    st.link_button("Repositório GitHub", GITHUB_URL)
    st.divider()

    if st.button("Novo chat"):
        novo_chat()

    nomes = [c["nome"] for c in st.session_state.chats]
    idx = st.radio("Seus chats", list(range(len(nomes))),
                   index=st.session_state.chat_atual,
                   format_func=lambda i: nomes[i])
    st.session_state.chat_atual = idx

    st.divider()
    modo = st.selectbox("Modo:", list(MODOS_DESC.keys()), index=1)
    st.caption(MODOS_DESC.get(modo, ""))

# ============================================
# ÁREA PRINCIPAL
# ============================================
chat = st.session_state.chats[st.session_state.chat_atual]
st.markdown(f"### Sessão: {chat['nome']}")

for m in chat["historico"]:
    bg = "#1f1f1f" if m["autor"] == "Você" else "#2b2b2b"
    st.markdown(
        f"<div style='background:{bg};color:#eaeaea;padding:10px;border-radius:6px;margin:5px 0;'>"
        f"<b>{m['autor']}:</b><br>{m['texto']}</div>",
        unsafe_allow_html=True
    )

msg = st.chat_input("Digite sua mensagem...")
if msg:
    chat["historico"].append({"autor": "Você", "texto": msg})
    with st.spinner("Analisando e gerando resposta..."):
        resposta = gerar_resposta(modo, msg, chat["historico"])
    chat["historico"].append({"autor": "PrimeBud", "texto": resposta})
    st.rerun()

