import streamlit as st
import requests
import json
import os

# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================
st.set_page_config(
    page_title="PrimeBud 1.0 — GPT-OSS 120B + Imagens",
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
    abas = st.tabs(["Entrar", "Criar Conta", "Convidado"])

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
        plano_i = st.selectbox("Plano", ["Free", "Pro", "Ultra", "Trabalho", "Professor"])
        if st.button("Criar conta"):
            db = st.session_state.usuarios
            if novo_u in db:
                st.warning("Usuário já existe.")
            else:
                db[novo_u] = {"senha": nova_s, "plano": plano_i}
                st.session_state.usuario = novo_u
                st.session_state.plano = plano_i
                st.success(f"Conta criada: {novo_u} ({plano_i})")
                st.rerun()

    with abas[2]:
        if st.button("Entrar como Convidado"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.rerun()

    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ============================================================
# MODOS COMPLETOS
# ============================================================
MODOS_DESC = {
    "⚡ Flash": "Respostas curtas e diretas.",
    "🔵 Normal": "Respostas equilibradas e naturais.",
    "🍃 Econômico": "Rápido e com menos tokens.",
    "💬 Mini": "Conversas simples.",
    "💎 Pro": "Código + breve explicação.",
    "☄️ Ultra": "Raciocínio detalhado e extenso.",
    "✍️ Escritor": "Textos criativos e bem escritos.",
    "🏫 Escola": "Explicações didáticas e objetivas.",
    "👨‍🏫 Professor": "Explicações com exemplos e contexto.",
    "🎨 Designer": "Ideias visuais e conceitos criativos.",
    "💻 Codificador": "Códigos bem estruturados e comentados.",
    "🧩 Estratégias": "Planos e análises práticas.",
    "🖼️ Imagem (Beta)": "Cria imagens detalhadas a partir do texto."
}

SYSTEM_PROMPT = (
    "Você é o PrimeBud — uma IA profissional e analítica. "
    "Responda com clareza e complete sempre o raciocínio sem cortar. "
    "Se for pedido código, formate corretamente."
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
# FUNÇÕES PRINCIPAIS
# ============================================================
def corrigir_acentos(txt):
    try:
        return txt.encode("latin1").decode("utf-8")
    except Exception:
        return txt

def chat_stream(messages, temperature=0.6, max_tokens=16000, timeout=600):
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
            except:
                continue

def gerar_imagem(prompt, qtd=1, tamanho="1024x1024"):
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {"model": "gpt-image-1", "prompt": prompt, "n": qtd, "size": tamanho}
    r = requests.post(IMAGE_API, headers=headers, json=payload)
    if r.status_code != 200:
        return [f"Erro: {r.text}"]
    data = r.json()
    return [d["url"] for d in data["data"]]

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
        st.divider()
        st.subheader("🖼️ Gerador de Imagens — Modo Beta")
        qtd = st.slider("Quantidade", 1, 4, 1)
        tamanho = st.selectbox("Tamanho da imagem", ["512x512", "1024x1024", "2048x2048"], index=1)

        if st.button("🎨 Gerar Imagem Agora"):
            with st.spinner("Gerando imagem..."):
                urls = gerar_imagem(msg, qtd=qtd, tamanho=tamanho)
                for u in urls:
                    if "http" in u:
                        st.image(u, caption=f"Imagem gerada ({tamanho})", use_column_width=True)
                        chat["historico"].append({"autor": "PrimeBud", "texto": f"[Imagem gerada: {u}]"})
                    else:
                        st.error(u)

    else:
        with st.spinner("💭 Processando resposta..."):
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
            except Exception as e:
                resposta_final = f"[Erro ao gerar resposta: {e}]"
                st.error(resposta_final)

            chat["historico"].append({"autor": "PrimeBud", "texto": resposta_final})

    st.session_state.chats[st.session_state.chat_atual]["historico"] = chat["historico"]
    st.rerun()

