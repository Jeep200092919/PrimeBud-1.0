import streamlit as st
import requests
import json
import os
import time

# ============================================
# CONFIGS INICIAIS
# ============================================
st.set_page_config(page_title="PrimeBud 1.0 — GPT-OSS 120B", page_icon="🧠", layout="wide")

# Endpoints
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/api/chat"

# Secrets / Env
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL = st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "gpt-oss-120b"))

GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-1.0"

# ============================================
# LOGIN / CONTAS
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

    tabs = st.tabs(["Entrar", "Criar conta", "Convidado (Ultra)"])

    with tabs[0]:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            db = st.session_state.usuarios
            if u in db and db[u]["senha"] == p:
                st.session_state.usuario = u
                st.session_state.plano = db[u]["plano"]
                st.success(f"Bem-vindo, {u}.")
                st.experimental_rerun()
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
                st.experimental_rerun()

    with tabs[2]:
        if st.button("Entrar como Convidado (Ultra)"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.success("Entrou como convidado — Plano Ultra liberado.")
            st.experimental_rerun()
    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ============================================
# BACKEND — GROQ (stream) + OLLAMA (fallback)
# ============================================
def usar_groq() -> bool:
    return bool(GROQ_API_KEY)

def build_messages_from_history(historico, user_msg, system_prompt: str):
    msgs = [{"role": "system", "content": system_prompt}]
    for m in historico:
        if m["autor"] == "Você":
            msgs.append({"role": "user", "content": m["texto"]})
        else:
            msgs.append({"role": "assistant", "content": m["texto"]})
    msgs.append({"role": "user", "content": user_msg})
    return msgs

def stream_groq(messages, temperature=0.35, max_tokens=4000, timeout=300):
    """
    Streaming OpenAI-compatible /chat/completions da Groq.
    Renderiza pedaços conforme chegam.
    """
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": True,                 # <- streaming ON
        "max_tokens": max_tokens,       # saída longa
    }
    with requests.post(GROQ_URL, headers=headers, json=payload, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        for raw_line in r.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            if raw_line.startswith("data: "):
                data = raw_line[len("data: "):]
                if data.strip() == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except Exception:
                    # ignora linhas de controle/keepalive
                    continue

def call_groq(messages, temperature=0.35, max_tokens=4000, timeout=300):
    """Chamada não-stream (para pensamento interno ou usos pontuais)."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": False,
        "max_tokens": max_tokens,
    }
    r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

def call_ollama(messages, temperature=0.35, num_predict=4000, timeout=300, stream=False):
    """Fallback simples ao Ollama local (não obrigatório usar)."""
    payload = {"model": "llama3", "messages": messages, "stream": stream, "options": {
        "temperature": temperature,
        "num_predict": num_predict
    }}
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    if stream:
        # Ollama streama linha a linha em JSON
        full = ""
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                obj = json.loads(line)
                token = obj.get("message", {}).get("content", "")
                if token:
                    full += token
                    yield token
            except Exception:
                continue
    else:
        data = r.json()
        return data.get("message", {}).get("content", "")

# ============================================
# MODOS CLÁSSICOS
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

def modo_to_generation(modo: str):
    """
    Define parâmetros por modo. Todos com max_tokens alto para evitar cortes.
    """
    base = {
        "⚡ Flash":        {"temperature": 0.25, "max_tokens": 800},
        "🔵 Normal":       {"temperature": 0.35, "max_tokens": 2000},
        "🍃 Econômico":    {"temperature": 0.30, "max_tokens": 1000},
        "💬 Mini":         {"temperature": 0.45, "max_tokens": 1000},
        "💎 Pro (Beta)":   {"temperature": 0.25, "max_tokens": 2500},
        "☄️ Ultra (Beta)": {"temperature": 0.40, "max_tokens": 4000},
        "✍️ Escritor":     {"temperature": 0.80, "max_tokens": 3000},
        "🏫 Escola":       {"temperature": 0.50, "max_tokens": 2500},
        "👨‍🏫 Professor":  {"temperature": 0.35, "max_tokens": 3200},
        "🎨 Designer":     {"temperature": 0.70, "max_tokens": 2200},
        "💻 Codificador":  {"temperature": 0.20, "max_tokens": 3200},
        "🧩 Estratégias":  {"temperature": 0.40, "max_tokens": 3200},
    }
    return base.get(modo, {"temperature": 0.35, "max_tokens": 2000})

SYSTEM_PROMPT_FORMAL = (
    "Você é o PrimeBud — uma IA analítica, técnica e objetiva. "
    "Mantenha tom profissional. Explique raciocínio quando solicitado. "
    "Evite informalidades e emojis. Seja claro e estruturado."
)

THINK_PROMPT = (
    "Explique brevemente seu raciocínio interno, de forma lógica e profissional, "
    "em 3–6 frases. Não dê a resposta final; apenas o raciocínio."
)

# ============================================
# ESTADO
# ============================================
if "chats" not in st.session_state:
    st.session_state.chats = [{"nome": "Chat 1", "historico": []}]
if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = 0

def novo_chat():
    n = len(st.session_state.chats) + 1
    st.session_state.chats.append({"nome": f"Chat {n}", "historico": []})
    st.session_state.chat_atual = n - 1
    st.experimental_rerun()

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.title(f"PrimeBud — {usuario}")
    st.caption(f"Plano atual: {plano}")

    # Trocar plano depois do login
    planos = ["Free", "Pro", "Ultra", "Trabalho", "Professor"]
    novo_plano = st.selectbox("Alterar plano", planos, index=planos.index(plano))
    if st.button("Atualizar plano"):
        st.session_state.plano = novo_plano
        st.session_state.usuarios[usuario]["plano"] = novo_plano
        st.success(f"Plano alterado para {novo_plano}.")
        st.experimental_rerun()

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

    st.divider()
    mostrar_pensamento = st.toggle("Mostrar pensamento interno", value=True,
                                   help="Exibe uma análise lógica breve antes da resposta final.")

# ============================================
# UI PRINCIPAL
# ============================================
chat = st.session_state.chats[st.session_state.chat_atual]
st.markdown(f"### Sessão: {chat['nome']}")

# histórico render
for m in chat["historico"]:
    bg = "#1f1f1f" if m["autor"] == "Você" else "#2b2b2b"
    st.markdown(
        f"<div style='background:{bg};color:#eaeaea;padding:10px;border-radius:6px;margin:6px 0;'>"
        f"<b>{m['autor']}:</b><br>{m['texto']}</div>", unsafe_allow_html=True
    )

# entrada
msg = st.chat_input("Digite sua mensagem...")
if msg:
    # salva pergunta do usuário
    chat["historico"].append({"autor": "Você", "texto": msg})

    # 1) Pensamento interno (não-stream) — opcional
    if mostrar_pensamento and usar_groq():
        pensamento_box = st.empty()
        try:
            think_messages = [
                {"role": "system", "content": "Você é uma IA analítica. " + THINK_PROMPT},
                {"role": "user", "content": msg}
            ]
            pensamento = call_groq(think_messages, temperature=0.25, max_tokens=400, timeout=120)
        except Exception as e:
            pensamento = f"[Falha ao gerar pensamento interno: {e}]"
        pensamento_box.markdown(
            f"<div style='background:#2e2e2e;color:#cfcfcf;padding:10px;border-radius:6px;margin:6px 0;'>"
            f"<b>Pensamento interno:</b><br>{pensamento}</div>",
            unsafe_allow_html=True
        )

    # 2) Resposta final (STREAMING)
    answer_box = st.empty()
    params = modo_to_generation(modo)
    try:
        messages = build_messages_from_history(
            chat["historico"], msg, SYSTEM_PROMPT_FORMAL
        )
        full_text = ""
        if usar_groq():
            for token in stream_groq(
                messages=messages,
                temperature=params["temperature"],
                max_tokens=params["max_tokens"],
                timeout=300
            ):
                full_text += token
                answer_box.markdown(
                    f"<div style='background:#2b2b2b;color:#eaeaea;padding:10px;border-radius:6px;margin:6px 0;'>"
                    f"<b>PrimeBud:</b><br>{full_text}</div>", unsafe_allow_html=True
                )
        else:
            # Fallback simples ao Ollama (streaming)
            for token in call_ollama(
                messages=messages,
                temperature=params["temperature"],
                num_predict=min(params["max_tokens"], 4000),
                timeout=300,
                stream=True
            ):
                full_text += token
                answer_box.markdown(
                    f"<div style='background:#2b2b2b;color:#eaeaea;padding:10px;border-radius:6px;margin:6px 0;'>"
                    f"<b>PrimeBud:</b><br>{full_text}</div>", unsafe_allow_html=True
                )
    except Exception as e:
        full_text = f"[Erro ao gerar resposta: {e}]"
        answer_box.markdown(
            f"<div style='background:#2b2b2b;color:#eaeaea;padding:10px;border-radius:6px;margin:6px 0;'>"
            f"<b>PrimeBud:</b><br>{full_text}</div>", unsafe_allow_html=True
        )

    # salva resposta completa no histórico
    chat["historico"].append({"autor": "PrimeBud", "texto": full_text})

    # IMPORTANTE: sem rerun imediato (evita cortar a resposta)
    # O Streamlit já atualiza a UI com as caixas acima.

