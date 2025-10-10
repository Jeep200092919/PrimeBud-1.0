import streamlit as st
import requests
import json
import concurrent.futures

# ==========================================
# CONFIGURAÇÕES GERAIS
# ==========================================
st.set_page_config(page_title="PrimeBud Turbo 1.0", page_icon="🤖", layout="wide")

OLLAMA_URL = "http://localhost:11434/api/chat"
GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-Turbo-1.0"

# ==========================================
# MODELOS DISPONÍVEIS
# ==========================================
MODEL_IDS = {
    "LLaMA 3": "llama3",
    "CodeGemma 7B": "codegemma:7b",
    "Phi-3": "phi3",
}

# ==========================================
# BASE DE USUÁRIOS
# ==========================================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"teste": {"senha": "0000", "plano": "Free"}}

# ==========================================
# DESCRIÇÃO DOS MODOS
# ==========================================
MODOS_DESC = {
    "⚡ Flash": "Respostas instantâneas (LLaMA 3 turbo).",
    "🔵 Normal": "Respostas equilibradas e naturais (LLaMA 3 turbo).",
    "🍃 Econômico": "Respostas curtas e otimizadas (LLaMA 3 turbo).",
    "💬 Mini": "Conversas leves e diretas (LLaMA 3 turbo).",
    "💎 Pro (Beta)": "Código + explicação curta (CodeGemma 7B turbo).",
    "☄️ Ultra (Beta)": "Pipeline turbo (LLaMA 3 → CodeGemma 7B → Phi-3).",
    "✍️ Escritor": "Textos criativos de 5–10 linhas (Phi-3 turbo).",
    "🏫 Escola": "Ajuda escolar (Phi-3 + LLaMA 3 turbo).",
    "👨‍🏫 Professor": "Didático e estruturado — LLaMA 3 com clareza e paciência.",
    "🎨 Designer": "Criativo e visual — LLaMA 3 rápido e imaginativo.",
    "💻 Codificador": "Técnico e direto — LLaMA 3 preciso e limpo.",
    "🧩 Estratégias": "Analítico e estruturado — LLaMA 3 equilibrado e estratégico.",
}

# ==========================================
# LIMITES DE MODELOS POR MODO
# ==========================================
MODE_LIMITS = {
    "⚡ Flash": ["LLaMA 3"],
    "🔵 Normal": ["LLaMA 3"],
    "🍃 Econômico": ["LLaMA 3"],
    "💬 Mini": ["LLaMA 3"],
    "💎 Pro (Beta)": ["CodeGemma 7B"],
    "☄️ Ultra (Beta)": ["PIPELINE"],
    "✍️ Escritor": ["Phi-3"],
    "🏫 Escola": ["DUO"],
    "👨‍🏫 Professor": ["WORK"],
    "🎨 Designer": ["WORK"],
    "💻 Codificador": ["WORK"],
    "🧩 Estratégias": ["WORK"],
}

# ==========================================
# FUNÇÃO DE CHAT OLLAMA (SEM TIMEOUT)
# ==========================================
def chat_ollama(model: str, prompt: str, options: dict | None = None) -> str:
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": "Você é o PrimeBud. Seja claro, rápido e útil."},
            {"role": "user", "content": prompt}
        ]
    }
    if options:
        payload["options"] = options

    r = requests.post(OLLAMA_URL, json=payload)
    try:
        data = r.json()
    except json.JSONDecodeError:
        data = json.loads(r.text.strip().split("\n")[0])
    return data["message"]["content"]

# ==========================================
# PIPELINES ESPECIAIS (TURBO)
# ==========================================
def gerar_resposta_ultra(msg: str) -> str:
    with concurrent.futures.ThreadPoolExecutor() as ex:
        f1 = ex.submit(chat_ollama, MODEL_IDS["LLaMA 3"], f"Resuma o problema em 2 linhas: {msg}", {"num_predict": 200})
        llama = f1.result()
        f2 = ex.submit(chat_ollama, MODEL_IDS["CodeGemma 7B"], f"Crie código funcional baseado em: {llama}", {"num_predict": 250})
        code = f2.result()
        phi = chat_ollama(MODEL_IDS["Phi-3"], f"Explique o código abaixo em até 6 linhas:\n{code}", {"num_predict": 250})
    return phi

def gerar_resposta_duo_escola(msg: str) -> str:
    with concurrent.futures.ThreadPoolExecutor() as ex:
        f1 = ex.submit(chat_ollama, MODEL_IDS["Phi-3"], f"Explique didaticamente: {msg}", {"num_predict": 250})
        f2 = ex.submit(chat_ollama, MODEL_IDS["LLaMA 3"], f"Dê 1 exemplo prático: {msg}", {"num_predict": 250})
        r1 = f1.result()
        r2 = f2.result()
    return f"{r1}\n\n📘 Exemplo:\n{r2}"

# ==========================================
# MODOS TRABALHO (APENAS LLaMA 3 TURBO)
# ==========================================
def gerar_resposta_work(modo: str, msg: str) -> str:
    configs = {
        "👨‍🏫 Professor": {
            "prompt": (
                f"Você é o PrimeBud PROFESSOR: didático e paciente.\n"
                f"Explique em passos curtos, com exemplos claros e diretos.\nTema: {msg}"
            ),
            "options": {"temperature": 0.4, "num_predict": 450, "top_p": 0.9}
        },
        "🎨 Designer": {
            "prompt": (
                f"Você é o PrimeBud DESIGNER: criativo e visual.\n"
                f"Gere ideias, esquemas visuais, estilos, cores e tipografia.\nBriefing: {msg}"
            ),
            "options": {"temperature": 0.95, "num_predict": 350, "top_p": 0.95}
        },
        "💻 Codificador": {
            "prompt": (
                f"Você é o PrimeBud CODIFICADOR: técnico e rápido.\n"
                f"Crie código funcional e explique em poucas linhas.\nTarefa: {msg}"
            ),
            "options": {"temperature": 0.2, "num_predict": 400, "top_p": 0.9}
        },
        "🧩 Estratégias": {
            "prompt": (
                f"Você é o PrimeBud ESTRATÉGICO: analítico e equilibrado.\n"
                f"Monte um plano prático com metas, ações e riscos claros.\nDesafio: {msg}"
            ),
            "options": {"temperature": 0.6, "num_predict": 420, "top_p": 0.9}
        },
    }
    cfg = configs.get(modo, configs["🧩 Estratégias"])
    return chat_ollama(MODEL_IDS["LLaMA 3"], cfg["prompt"], cfg["options"])

# ==========================================
# GERADOR PADRÃO (TURBO)
# ==========================================
def gerar_resposta(modelo_display: str | None, modo: str, msg: str) -> str:
    if modo == "☄️ Ultra (Beta)": return gerar_resposta_ultra(msg)
    if modo == "🏫 Escola": return gerar_resposta_duo_escola(msg)
    if MODE_LIMITS.get(modo) == ["WORK"]: return gerar_resposta_work(modo, msg)

    prompt = f"{msg}"
    if modelo_display is None: modelo_display = "LLaMA 3"
    model_id = MODEL_IDS[modelo_display]
    return chat_ollama(model_id, prompt, {"num_predict": 400})

# ==========================================
# LOGIN E SISTEMA DE USUÁRIOS
# ==========================================
if "usuario" not in st.session_state: st.session_state.usuario = None
if "plano" not in st.session_state: st.session_state.plano = None

if st.session_state.usuario is None:
    st.title("🤖 PrimeBud Turbo 1.0 — Login")
    st.link_button("🌐 Ver no GitHub", GITHUB_URL)
    aba = st.tabs(["Entrar", "Criar conta", "Convidado (Ultra)"])

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
        plano_escolhido = st.selectbox("Plano inicial", ["Free", "Pro", "Ultra", "Trabalho", "Professor"])
        if st.button("Criar conta"):
            db = st.session_state.usuarios
            db[novo_u] = {"senha": nova_s, "plano": plano_escolhido}
            st.session_state.usuario = novo_u
            st.session_state.plano = plano_escolhido
            st.rerun()

    with aba[2]:
        if st.button("Entrar como convidado (Ultra)"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.rerun()
    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ==========================================
# MULTICHATS E INTERFACE
# ==========================================
if "chats" not in st.session_state: st.session_state.chats = []
if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = 0
    st.session_state.chats.append({"nome": "Chat 1", "historico": []})

def novo_chat():
    n = len(st.session_state.chats) + 1
    st.session_state.chats.append({"nome": f"Chat {n}", "historico": []})
    st.session_state.chat_atual = len(st.session_state.chats) - 1
    st.rerun()

with st.sidebar:
    st.title(f"🤖 PrimeBud — {usuario}")
    if st.button("➕ Novo chat"): novo_chat()
    chats = [c["nome"] for c in st.session_state.chats]
    idx = st.radio("Seus chats:", list(range(len(chats))), format_func=lambda i: chats[i])
    st.session_state.chat_atual = idx

    modos_por_plano = {
        "Free": ["💬 Mini", "🍃 Econômico", "✍️ Escritor", "🏫 Escola"],
        "Pro": ["⚡ Flash", "🔵 Normal", "💎 Pro (Beta)", "🍃 Econômico", "✍️ Escritor", "🏫 Escola"],
        "Ultra": ["⚡ Flash", "🔵 Normal", "💎 Pro (Beta)", "🍃 Econômico", "💬 Mini",
                  "☄️ Ultra (Beta)", "✍️ Escritor", "🏫 Escola",
                  "👨‍🏫 Professor", "🎨 Designer", "💻 Codificador", "🧩 Estratégias"],
        "Trabalho": ["👨‍🏫 Professor", "🎨 Designer", "💻 Codificador", "🧩 Estratégias",
                     "✍️ Escritor", "🏫 Escola"],
        "Professor": ["👨‍🏫 Professor", "🏫 Escola", "✍️ Escritor"],
    }

    lista_modos = modos_por_plano.get(plano, modos_por_plano["Ultra"])
    modo = st.radio("Modo:", lista_modos)
    st.caption(MODOS_DESC.get(modo, "Modo customizado."))

# ==========================================
# ÁREA PRINCIPAL DE CHAT
# ==========================================
chat = st.session_state.chats[st.session_state.chat_atual]
st.markdown(f"### 💬 {chat['nome']}")

for m in chat["historico"]:
    who = "Você" if m["autor"] == "user" else "PrimeBud"
    color = "#2b313e" if m["autor"] == "user" else "#ececf1"
    text_color = "#fff" if m["autor"] == "user" else "#000"
    st.markdown(f"<div style='background:{color};color:{text_color};padding:10px;border-radius:10px;margin:6px 0;'><b>{who}:</b> {m['texto']}</div>", unsafe_allow_html=True)

msg = st.chat_input("Envie uma mensagem…")
if msg:
    chat["historico"].append({"autor": "user", "texto": msg})
    with st.spinner("Turbo..."):
        resposta = gerar_resposta(None, modo, msg)
    chat["historico"].append({"autor": "bot", "texto": resposta})
    st.rerun()
