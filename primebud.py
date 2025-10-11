import streamlit as st
import requests
import json
import concurrent.futures
import os

# ==============================
# CONFIGURAÇÕES INICIAIS
# ==============================
st.set_page_config(page_title="PrimeBud Turbo 1.1", page_icon="🤖", layout="wide")

# URLs principais
OLLAMA_URL = "http://localhost:11434/api/chat"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Carrega secrets (Streamlit Cloud) ou variáveis locais
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL = st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "llama3-8b-8192"))

GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-1.0"

# ==============================
# DETECÇÃO AUTOMÁTICA DE BACKEND
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
# CHAMADAS DE IA
# ==============================
def chat_api(model: str, prompt: str, options: dict | None = None, timeout: int = 60) -> str:
    """
    Usa Groq (LLaMA3 online) se houver chave; senão usa Ollama local.
    Mantém compatibilidade com todos os modos do PrimeBud.
    """
    # Se houver chave da Groq → usa o modelo hospedado
    if usar_groq():
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "Você é o PrimeBud Turbo 1.1 — seja claro, rápido e útil."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            **_map_options_for_openai_like(options),
        }
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
        data = r.json()
        return data["choices"][0]["message"]["content"]

    # Caso contrário, usa o Ollama local
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
    return data["message"]["content"]

# ==============================
# MODELOS E MODOS
# ==============================
MODEL_IDS = {
    "LLaMA 3": "llama3-8b-8192",
    "CodeGemma 7B": "llama3-8b-8192",
    "Phi-3": "llama3-8b-8192",
}

MODOS_DESC = {
    "⚡ Flash": "Respostas curtas e instantâneas (LLaMA 3).",
    "🔵 Normal": "Respostas equilibradas e naturais (LLaMA 3).",
    "🍃 Econômico": "Respostas curtas e otimizadas (LLaMA 3).",
    "💬 Mini": "Conversas leves e simples.",
    "💎 Pro (Beta)": "Código + breve explicação (LLaMA 3).",
    "☄️ Ultra (Beta)": "Processamento turbo em múltiplas etapas.",
    "✍️ Escritor": "Textos criativos de 5–10 linhas.",
    "🏫 Escola": "Explicações didáticas do Ensino Médio.",
    "👨‍🏫 Professor": "Explicações completas e exemplos práticos.",
    "🎨 Designer": "Ideias visuais e criativas.",
    "💻 Codificador": "Código limpo com explicação curta.",
    "🧩 Estratégias": "Planos de ação objetivos e mensuráveis.",
}

MODE_LIMITS = {m: ["LLaMA 3"] for m in MODOS_DESC.keys()}

# ==============================
# FUNÇÕES DE RESPOSTA POR MODO
# ==============================
def gerar_resposta(modo: str, msg: str) -> str:
    base_prompt = MODOS_DESC.get(modo, "Seja direto e útil.")
    full_prompt = f"{base_prompt}\n\n{msg}"

    # Parâmetros distintos simulando "velocidades"
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
# LOGIN SIMPLES
# ==============================
if "usuario" not in st.session_state:
    st.session_state.usuario = "Convidado"
    st.session_state.plano = "Ultra"

st.sidebar.title(f"🤖 PrimeBud — {st.session_state.usuario}")
st.sidebar.markdown(f"**Plano:** {st.session_state.plano}")
st.sidebar.link_button("🌐 Ver no GitHub", GITHUB_URL)
st.sidebar.divider()

modo = st.sidebar.selectbox("Modo:", list(MODOS_DESC.keys()), index=1)
st.sidebar.info(MODOS_DESC[modo])

# ==============================
# ÁREA DO CHAT
# ==============================
st.title("🚀 PrimeBud Turbo 1.1 — Groq Edition")

if "chat" not in st.session_state:
    st.session_state.chat = []

for m in st.session_state.chat:
    estilo = "background:#2b313e;color:#fff" if m["autor"] == "user" else "background:#ececf1;color:#000"
    st.markdown(f"<div style='{estilo};padding:10px;border-radius:10px;margin:6px 0;'><b>{m['autor']}:</b> {m['texto']}</div>", unsafe_allow_html=True)

msg = st.chat_input("Digite sua mensagem...")
if msg:
    st.session_state.chat.append({"autor": "Você", "texto": msg})
    with st.spinner("Processando..."):
        resposta = gerar_resposta(modo, msg)
    st.session_state.chat.append({"autor": "PrimeBud", "texto": resposta})
    st.rerun()

