import streamlit as st
import requests
import json
import os

# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================
st.set_page_config(
    page_title="PrimeBud 1.0 — GPT-OSS 120B Ultimate",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CHAVES E ENDPOINTS
# ============================================================
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL = st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "gpt-oss-120b"))

IMAGE_API = "https://api.openai.com/v1/images/generations"
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

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
    st.title("PrimeBud 1.0 — GPT-OSS 120B Ultimate")
    st.link_button("🌐 GitHub", GITHUB_URL)
    st.divider()

    aba = st.tabs(["Entrar", "Criar conta", "Convidado"])

    with aba[0]:
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

    with aba[1]:
        novo_u = st.text_input("Novo usuário")
        nova_s = st.text_input("Nova senha", type="password")
        plano_i = st.selectbox("Plano", ["Free", "Pro", "Ultra", "Trabalho", "Professor"])
        if st.button("Criar conta"):
            db = st.session_state.usuarios
            if novo_u in db:
                st.warning("Usuário já existe.")
            else:
                db[novo_u] = {"senha": nova_s, "plano": plano_i}
                st.session_state.usuario = novo_u
                st.session_state.plano = plano_i
                st.rerun()

    with aba[2]:
        if st.button("Entrar como Convidado"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.rerun()

    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ============================================================
# MODOS
# ============================================================
MODOS_DESC = {
    "⚡ Flash": "Respostas curtas e diretas.",
    "🔵 Normal": "Respostas completas e naturais.",
    "☄️ Ultra": "Análises longas e complexas.",
    "💻 Codificador": "Códigos longos e explicados.",
    "🧠 Explicador": "Explicações detalhadas e didáticas.",
    "🖼️ Imagem (Beta)": "Cria imagens com base em descrições de texto."
}

SYSTEM_PROMPT = (
    "Você é o PrimeBud, uma IA avançada de raciocínio analítico. "
    "Responda sempre até o fim do raciocínio, sem cortar o conteúdo. "
    "Escreva com clareza, lógica e profundidade."
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
    st.title(f"👤 Usuário: {usuario}")
    st.caption(f"Plano: {plano}")
    if st.button("➕ Novo Chat"):
        novo_chat()

    nomes = [c["nome"] for c in st.session_state.chats]
    idx = st.radio("Chats", list(range(len(nomes))),
                   index=st.session_state.chat_atual,
                   format_func=lambda i: nomes[i])
    st.session_state.chat_atual = idx

    st.divider()
    modo = st.selectbox("Modo", list(MODOS_DESC.keys()), index=1)
    st.caption(MODOS_DESC[modo])

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def corrigir_acentos(texto):
    try:
        return texto.encode("latin1").decode("utf-8")
    except Exception:
        return texto

def gerar_imagem(prompt: str):
    """Gera imagem via API"""
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {"model": "gpt-image-1", "prompt": prompt, "size": "1024x1024"}
    r = requests.post(IMAGE_API, headers=headers, json=payload)
    if r.status_code != 200:
        return f"Erro: {r.text}"
    return r.json()["data"][0]["url"]

def chat_stream(messages, temperature=0.5, max_tokens=16000, timeout=600):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": True,
        "max_tokens": max_tokens
    }
    with requests.post(GROQ_URL, headers=headers, json=payload, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        r.encoding = "utf-8"
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data = line[len("data: "):]
            if data.strip() == "[DONE]":
                break
            try:
                obj = json.loads(data)
                delta = obj["choices"][0]["delta"].get("content", "")
                if delta:
                    yield corrigir_acentos(delta)
            except Exception:
                continue

# ============================================================
# ÁREA PRINCIPAL
# ============================================================
chat = st.session_state.chats[st.session_state.chat_atual]
st.markdown(f"### 💬 Sessão: {chat['nome']}")

for m in chat["historico"]:
    bg = "#1e1e1e" if m["autor"] == "Você" else "#2a2a2a"
    st.markdown(
        f"<div style='background:{bg};color:#eaeaea;padding:10px;border-radius:8px;margin:6px 0;'>"
        f"<b>{m['autor']}:</b> {m['texto']}</div>",
        unsafe_allow_html=True
    )

msg = st.chat_input("Digite sua mensagem...")

if msg:
    chat["historico"].append({"autor": "Você", "texto": msg})

    if modo == "🖼️ Imagem (Beta)":
        with st.spinner("🎨 Gerando imagem..."):
            url = gerar_imagem(msg)
            if "http" in url:
                st.image(url, caption="Imagem gerada pelo PrimeBud", use_column_width=True)
                chat["historico"].append({"autor": "PrimeBud", "texto": f"[Imagem gerada: {url}]"})
            else:
                st.error(url)
    else:
        with st.spinner("🧠 Raciocinando..."):
            mensagens = [{"role": "system", "content": SYSTEM_PROMPT}]
            for h in chat["historico"]:
                role = "user" if h["autor"] == "Você" else "assistant"
                mensagens.append({"role": role, "content": h["texto"]})
            mensagens.append({"role": "user", "content": msg})

            resposta_final = ""
            try:
                for token in chat_stream(mensagens):
                    resposta_final += token
                    st.markdown(
                        f"<div style='background:#2a2a2a;color:#eaeaea;padding:10px;border-radius:8px;'>"
                        f"<b>PrimeBud:</b><br>{resposta_final}</div>",
                        unsafe_allow_html=True
                    )
                if not resposta_final.strip().endswith(('.', '!', '?')):
                    resposta_final += "..."
            except Exception as e:
                resposta_final = f"[Erro ao completar resposta: {e}]"

            chat["historico"].append({"autor": "PrimeBud", "texto": resposta_final})

    st.session_state.chats[st.session_state.chat_atual]["historico"] = chat["historico"]
    st.rerun()

