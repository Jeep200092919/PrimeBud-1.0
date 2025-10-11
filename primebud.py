import streamlit as st
import requests
import json
import os

# ======================================
# CONFIGURAÇÕES INICIAIS
# ======================================
st.set_page_config(page_title="PrimeBud 1.0 — GPT-OSS 120B", page_icon="🧠", layout="wide")

# Endpoints
OLLAMA_URL = "http://localhost:11434/api/chat"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Secrets / Env
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL = st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "gpt-oss-120b"))

GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-1.0"

# ======================================
# LOGIN / CONTAS
# ======================================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"teste": {"senha": "0000", "plano": "Free"}}

if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "plano" not in st.session_state:
    st.session_state.plano = None

if st.session_state.usuario is None:
    st.title("PrimeBud 1.0 — GPT-OSS 120B")
    st.link_button("Ver código-fonte", GITHUB_URL)
    st.divider()

    tabs = st.tabs(["Entrar", "Criar conta", "Convidado (Ultra)"])

    with tabs[0]:
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
                st.rerun()

    with tabs[2]:
        if st.button("Entrar como Convidado (Ultra)"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.rerun()
    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ======================================
# BACKEND — GROQ + FALLBACK OLLAMA
# ======================================
def usar_groq() -> bool:
    return bool(GROQ_API_KEY)

def _map_options_for_openai_like(options: dict | None) -> dict:
    options = options or {}
    return {
        "temperature": options.get("temperature", 0.35),
        "top_p": options.get("top_p", 0.9),
        "max_tokens": options.get("num_predict", 800),
    }

def chat_api(model: str, prompt: str, historico, options: dict | None = None, timeout: int = 120) -> str:
    """Envia o histórico completo do chat para a API."""
    messages = [{"role": "system", "content": (
        "Você é o PrimeBud — um assistente técnico e analítico. "
        "Mantenha um tom profissional, claro e objetivo. "
        "Explique o raciocínio passo a passo quando apropriado, "
        "mas sem improvisar ou inventar dados. "
        "Evite emojis e linguagem coloquial."
    )}]
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
            return f"[Erro Groq] {e}"

    # Fallback local via Ollama
    payload = {"model": model, "stream": False, "messages": messages}
    if options:
        payload["options"] = options
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        data = r.json()
        return data.get("message", {}).get("content", "[Erro Ollama] resposta inválida.")
    except Exception as e:
        return f"[Erro Ollama] {e}"

# ======================================
# MODOS E CONFIGURAÇÕES
# ======================================
MODOS_DESC = {
    "Análise Lógica": "Raciocínio passo a passo e justificativa detalhada.",
    "Explicação Técnica": "Abordagem clara e objetiva sobre temas complexos.",
    "Científico": "Respostas baseadas em evidências e precisão conceitual.",
    "Profissional": "Tom formal e estruturado, adequado para relatórios ou defesa de tese.",
    "Estratégico": "Planejamento detalhado com avaliação de riscos e impacto.",
    "Código": "Geração de código bem documentado e racionalizado.",
    "Resumo": "Síntese técnica e concisa de informações extensas.",
}

def gerar_resposta(modo: str, msg: str, historico) -> str:
    base_prompt = MODOS_DESC.get(modo, "Responda com clareza e profundidade.")
    full_prompt = f"[Modo: {modo}]\n{base_prompt}\n\n{msg}"

    opt = {"temperature": 0.3, "num_predict": 1200}
    return chat_api(GROQ_MODEL, full_prompt, historico, opt)

# ======================================
# ESTADO E INTERFACE
# ======================================
if "chats" not in st.session_state:
    st.session_state.chats = [{"nome": "Sessão 1", "historico": []}]
if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = 0

def novo_chat():
    n = len(st.session_state.chats) + 1
    st.session_state.chats.append({"nome": f"Sessão {n}", "historico": []})
    st.session_state.chat_atual = n - 1
    st.rerun()

# ======================================
# SIDEBAR
# ======================================
with st.sidebar:
    st.title(f"PrimeBud — {usuario}")
    st.caption(f"Plano atual: {plano}")
    planos = ["Free", "Pro", "Ultra", "Trabalho", "Professor"]
    novo_plano = st.selectbox("Alterar plano", planos, index=planos.index(plano))
    if st.button("Atualizar plano"):
        st.session_state.plano = novo_plano
        st.session_state.usuarios[usuario]["plano"] = novo_plano
        st.rerun()

    st.link_button("Repositório GitHub", GITHUB_URL)
    st.divider()
    if st.button("Novo chat"):
        novo_chat()

    nomes = [c["nome"] for c in st.session_state.chats]
    idx = st.radio("Sessões ativas", list(range(len(nomes))),
                   index=st.session_state.chat_atual,
                   format_func=lambda i: nomes[i])
    st.session_state.chat_atual = idx

    st.divider()
    modo = st.selectbox("Modo de análise", list(MODOS_DESC.keys()), index=0)
    st.caption(MODOS_DESC.get(modo, ""))

# ======================================
# ÁREA PRINCIPAL
# ======================================
chat = st.session_state.chats[st.session_state.chat_atual]
st.markdown(f"### Sessão atual: {chat['nome']}")

for m in chat["historico"]:
    bg = "#1e1e1e" if m["autor"] == "Você" else "#2a2a2a"
    color = "#f5f5f5"
    st.markdown(
        f"<div style='background:{bg};color:{color};padding:10px;border-radius:6px;margin:6px 0;'>"
        f"<b>{m['autor']}:</b><br>{m['texto']}</div>",
        unsafe_allow_html=True
    )

msg = st.chat_input("Digite sua solicitação de análise...")
if msg:
    chat["historico"].append({"autor": "Você", "texto": msg})
    with st.spinner("Processando análise..."):
        resposta = gerar_resposta(modo, msg, chat["historico"])
    chat["historico"].append({"autor": "PrimeBud", "texto": resposta})
    st.rerun()
