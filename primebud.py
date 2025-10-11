import streamlit as st
import requests
import json
import concurrent.futures
import os

# ==============================
# CONFIGURAÇÕES INICIAIS
# ==============================
st.set_page_config(page_title="PrimeBud Turbo 1.2", page_icon="🤖", layout="wide")

OLLAMA_URL = "http://localhost:11434/api/chat"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Carrega secrets do Streamlit Cloud ou variáveis locais
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL = st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "llama3-8b"))
GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-1.0"

# ==============================
# SISTEMA DE LOGIN / CONTAS
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

# Tela de login inicial
if st.session_state.usuario is None:
    st.title("🤖 PrimeBud Turbo 1.2 — Login")
    st.caption("Feito por: **Primorix Studios**")
    st.link_button("🌐 Ver no GitHub", GITHUB_URL)
    st.markdown("---")

    aba = st.tabs(["Entrar", "Criar conta", "Convidado (Ultra)"])

    with aba[0]:
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

    with aba[1]:
        novo_u = st.text_input("Novo usuário")
        nova_s = st.text_input("Nova senha", type="password")
        plano_escolhido = st.selectbox("Plano inicial", ["Free", "Pro", "Ultra", "Trabalho", "Professor"])
        if st.button("Criar conta"):
            db = st.session_state.usuarios
            if novo_u in db:
                st.warning("Usuário já existe.")
            else:
                db[novo_u] = {"senha": nova_s, "plano": plano_escolhido}
                st.session_state.usuario = novo_u
                st.session_state.plano = plano_escolhido
                st.success(f"Conta criada e login automático como {novo_u} ({plano_escolhido}).")
                st.rerun()

    with aba[2]:
        if st.button("Entrar como Convidado (Ultra)"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.success("Entrou como convidado — Plano Ultra liberado.")
            st.rerun()
    st.stop()

# ==============================
# FUNÇÕES AUXILIARES
# ==============================
def usar_groq() -> bool:
    """Verifica se há uma API key da Groq disponível."""
    return bool(GROQ_API_KEY)

def _map_options_for_openai_like(options: dict | None) -> dict:
    options = options or {}
    return {
        "temperature": options.get("temperature", 0.6),
        "top_p": options.get("top_p", 0.9),
        "max_tokens": options.get("num_predict", 400),
    }

# ==============================
# FUNÇÃO PRINCIPAL DE CHAT (Groq + Ollama)
# ==============================
def chat_api(model: str, prompt: str, options: dict | None = None, timeout: int = 60) -> str:
    if usar_groq():
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "Você é o PrimeBud Turbo 1.2 — seja claro, rápido e útil."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            **_map_options_for_openai_like(options),
        }
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)

        try:
            data = r.json()
        except Exception:
            return f"❌ Erro: resposta inválida da Groq.\n\nTexto bruto: {r.text[:300]}"

        if "choices" not in data:
            return f"⚠️ Resposta inesperada da Groq:\n\n{json.dumps(data, indent=2)[:700]}"

        return data["choices"][0]["message"]["content"]

    # fallback local (Ollama)
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": "Você é o PrimeBud Turbo. Seja claro, rápido e útil."},
            {"role": "user", "content": prompt},
        ],
    }
    if options:
        payload["options"] = options

    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    try:
        data = r.json()
    except json.JSONDecodeError:
        data = json.loads(r.text.strip().split("\n")[0])
    return data.get("message", {}).get("content", "⚠️ Erro: resposta inválida do Ollama.")

# ==============================
# MODOS E CONFIGURAÇÕES
# ==============================
MODEL_IDS = {
    "LLaMA 3": "llama3-8b",
    "CodeGemma 7B": "llama3-8b",
    "Phi-3": "llama3-8b",
}

MODOS_DESC = {
    "⚡ Flash": "Respostas curtas e instantâneas (LLaMA 3).",
    "🔵 Normal": "Respostas equilibradas e naturais (LLaMA 3).",
    "🍃 Econômico": "Respostas curtas e otimizadas (LLaMA 3).",
    "💬 Mini": "Conversas leves e simples.",
    "💎 Pro (Beta)": "Código + breve explicação (LLaMA 3).",
    "☄️ Ultra (Beta)": "Processamento turbo.",
    "✍️ Escritor": "Textos criativos de 5–10 linhas.",
    "🏫 Escola": "Explicações didáticas do Ensino Médio.",
    "👨‍🏫 Professor": "Explicações completas e exemplos práticos.",
    "🎨 Designer": "Ideias visuais e criativas.",
    "💻 Codificador": "Código limpo com explicação curta.",
    "🧩 Estratégias": "Planos de ação objetivos e mensuráveis.",
}

MODE_LIMITS = {m: ["LLaMA 3"] for m in MODOS_DESC.keys()}

# ==============================
# GERAÇÃO DE RESPOSTAS
# ==============================
def gerar_resposta(modo: str, msg: str) -> str:
    base_prompt = MODOS_DESC.get(modo, "Seja direto e útil.")
    full_prompt = f"{base_prompt}\n\n{msg}"

    config = {
        "⚡ Flash": {"temperature": 0.3, "num_predict": 100},
        "🔵 Normal": {"temperature": 0.5, "num_predict": 220},
        "🍃 Econômico": {"temperature": 0.4, "num_predict": 120},
        "💬 Mini": {"temperature": 0.6, "num_predict": 150},
        "💎 Pro (Beta)": {"temperature": 0.4, "num_predict": 240},
        "☄️ Ultra (Beta)": {"temperature": 0.6, "num_predict": 300},
        "✍️ Escritor": {"temperature": 0.9, "num_predict": 250},
        "🏫 Escola": {"temperature": 0.6, "num_predict": 250},
        "👨‍🏫 Professor": {"temperature": 0.4, "num_predict": 300},
        "🎨 Designer": {"temperature": 0.9, "num_predict": 220},
        "💻 Codificador": {"temperature": 0.2, "num_predict": 280},
        "🧩 Estratégias": {"temperature": 0.6, "num_predict": 260},
    }

    opt = config.get(modo, {"temperature": 0.5, "num_predict": 200})
    return chat_api(MODEL_IDS["LLaMA 3"], full_prompt, opt)

# ==============================
# INTERFACE PRINCIPAL
# ==============================
usuario = st.session_state.usuario
plano = st.session_state.plano

st.sidebar.title(f"🤖 PrimeBud — {usuario}")
st.sidebar.markdown(f"**Plano:** {plano}")
st.sidebar.link_button("🌐 Ver no GitHub", GITHUB_URL)
st.sidebar.divider()

modos_por_plano = {
    "Free": ["💬 Mini", "🍃 Econômico", "✍️ Escritor", "🏫 Escola"],
    "Pro": ["⚡ Flash", "🔵 Normal", "💎 Pro (Beta)", "✍️ Escritor", "🏫 Escola"],
    "Ultra": list(MODOS_DESC.keys()),
    "Trabalho": ["👨‍🏫 Professor", "🎨 Designer", "💻 Codificador", "🧩 Estratégias", "✍️ Escritor"],
    "Professor": ["👨‍🏫 Professor", "🏫 Escola", "✍️ Escritor"],
}

lista_modos = modos_por_plano.get(plano, modos_por_plano["Ultra"])
modo = st.sidebar.selectbox("Modo:", lista_modos)
st.sidebar.info(MODOS_DESC[modo])

# ==============================
# CHAT
# ==============================
st.title("🚀 PrimeBud Turbo 1.2 — Groq + Login")

if "chat" not in st.session_state:
    st.session_state.chat = []

for m in st.session_state.chat:
    estilo = "background:#2b313e;color:#fff" if m["autor"] == "user" else "background:#ececf1;color:#000"
    st.markdown(
        f"<div style='{estilo};padding:10px;border-radius:10px;margin:6px 0;'><b>{m['autor']}:</b> {m['texto']}</div>",
        unsafe_allow_html=True
    )

msg = st.chat_input("Digite sua mensagem...")
if msg:
    st.session_state.chat.append({"autor": "Você", "texto": msg})
    with st.spinner("Processando..."):
        resposta = gerar_resposta(modo, msg)
    st.session_state.chat.append({"autor": "PrimeBud", "texto": resposta})
    st.rerun()
