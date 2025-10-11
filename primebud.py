import streamlit as st
import requests
import json
import os

# ==============================
# CONFIGURAÇÕES INICIAIS
# ==============================
st.set_page_config(page_title="PrimeBud 1.0 — LLaMA 3.3 70B", page_icon="🤖", layout="wide")

# Endpoints
OLLAMA_URL = "http://localhost:11434/api/chat"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Secrets / Env
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL = st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "llama3.3-70b-versatile"))

GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-1.0"

# ==============================
# LOGIN / CONTAS
# ==============================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {
        "teste": {"senha": "0000", "plano": "Free"},
    }

if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "plano" not in st.session_state:
    st.session_state.plano = None

if st.session_state.usuario is None:
    st.title("🤖 PrimeBud 1.0 — LLaMA 3.3 70B")
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
# BACKEND — GROQ + FALLBACK OLLAMA
# ==============================
def usar_groq() -> bool:
    return bool(GROQ_API_KEY)

def _map_options_for_openai_like(options: dict | None) -> dict:
    options = options or {}
    return {
        "temperature": options.get("temperature", 0.6),
        "top_p": options.get("top_p", 0.9),
        "max_tokens": options.get("num_predict", 400),
    }

def chat_api(model: str, prompt: str, historico, options: dict | None = None, timeout: int = 120) -> str:
    """Envia o histórico completo do chat à Groq ou Ollama."""
    messages = [{"role": "system", "content": "Você é o PrimeBud Turbo — claro, rápido e útil."}]
    for m in historico:
        if m["autor"] == "Você":
            messages.append({"role": "user", "content": m["texto"]})
        else:
            messages.append({"role": "assistant", "content": m["texto"]})
    messages.append({"role": "user", "content": prompt})

    if usar_groq():
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "stream": False,
            **_map_options_for_openai_like(options),
        }
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        try:
            r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"❌ Erro Groq: {str(e)}"

    # Fallback: Ollama local
    payload = {"model": model, "stream": False, "messages": messages}
    if options:
        payload["options"] = options
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        data = r.json()
        return data.get("message", {}).get("content", "⚠️ Erro: resposta inválida do Ollama.")
    except Exception as e:
        return f"❌ Erro Ollama: {str(e)}"

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
    "🏫 Escola": "Explicações didáticas do EM.",
    "👨‍🏫 Professor": "Aulas e resumos com exemplos.",
    "🎨 Designer": "Ideias visuais e UI/UX.",
    "💻 Codificador": "Código limpo + explicação curta.",
    "🧩 Estratégias": "Planos práticos com metas e ações.",
}

def gerar_resposta(modo: str, msg: str, historico) -> str:
    """Gera resposta do PrimeBud com memória de conversa e ajuste automático de tokens."""
    base_prompt = MODOS_DESC.get(modo, "Seja direto e útil.")
    full_prompt = f"{base_prompt}\n\n{msg}"

    palavras = len(msg.split())
    if palavras < 40:
        base_tokens = 400
    elif palavras < 120:
        base_tokens = 800
    else:
        base_tokens = 1200

    config = {
        "⚡ Flash": {"temperature": 0.3, "num_predict": min(150, base_tokens)},
        "🔵 Normal": {"temperature": 0.5, "num_predict": min(600, base_tokens + 200)},
        "🍃 Econômico": {"temperature": 0.4, "num_predict": min(250, base_tokens)},
        "💬 Mini": {"temperature": 0.6, "num_predict": min(300, base_tokens)},
        "💎 Pro (Beta)": {"temperature": 0.35, "num_predict": min(900, base_tokens + 300)},
        "☄️ Ultra (Beta)": {"temperature": 0.6, "num_predict": min(1300, base_tokens + 500)},
        "✍️ Escritor": {"temperature": 0.9, "num_predict": min(1000, base_tokens + 300)},
        "🏫 Escola": {"temperature": 0.6, "num_predict": min(800, base_tokens + 200)},
        "👨‍🏫 Professor": {"temperature": 0.4, "num_predict": min(1200, base_tokens + 400)},
        "🎨 Designer": {"temperature": 0.95, "num_predict": min(900, base_tokens + 200)},
        "💻 Codificador": {"temperature": 0.2, "num_predict": min(1000, base_tokens + 300)},
        "🧩 Estratégias": {"temperature": 0.6, "num_predict": min(1100, base_tokens + 400)},
    }

    opt = config.get(modo, {"temperature": 0.6, "num_predict": 800})
    return chat_api(GROQ_MODEL, full_prompt, historico, opt)

# ==============================
# ESTADO E INTERFACE
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
    st.markdown(f"**Plano atual:** {plano}")

    # Trocar plano depois do login
    planos = ["Free", "Pro", "Ultra", "Trabalho", "Professor"]
    novo_plano = st.selectbox("Alterar plano:", planos, index=planos.index(plano))
    if st.button("💼 Atualizar plano"):
        st.session_state.plano = novo_plano
        st.session_state.usuarios[usuario]["plano"] = novo_plano
        st.success(f"Plano alterado para {novo_plano} com sucesso!")
        st.rerun()

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
    # Modos liberados conforme plano
    modos_por_plano = {
        "Free": ["💬 Mini", "🍃 Econômico", "✍️ Escritor", "🏫 Escola", "🔵 Normal"],
        "Pro": ["⚡ Flash", "🔵 Normal", "💎 Pro (Beta)", "✍️ Escritor", "🏫 Escola"],
        "Ultra": list(MODOS_DESC.keys()),
        "Trabalho": ["👨‍🏫 Professor", "🎨 Designer", "💻 Codificador", "🧩 Estratégias", "✍️ Escritor", "🏫 Escola"],
        "Professor": ["👨‍🏫 Professor", "🏫 Escola", "✍️ Escritor", "🔵 Normal"],
    }

    modos_disponiveis = modos_por_plano.get(st.session_state.plano, list(MODOS_DESC.keys()))
    modo = st.selectbox("Modo:", modos_disponiveis, index=0)
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
    with st.spinner("🧠 Pensando..."):
        resposta = gerar_resposta(modo, msg, chat["historico"])
    chat["historico"].append({"autor": "PrimeBud", "texto": resposta})
    st.rerun()

