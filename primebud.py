import streamlit as st
import requests
import json
import concurrent.futures

# ==============================
# CONFIGURAÇÕES GERAIS
# ==============================
st.set_page_config(page_title="PrimeBud Turbo 1.0", page_icon="🤖", layout="wide")

OLLAMA_URL = "http://localhost:11434/api/chat"
GITHUB_URL = "https://github.com/Jeep200092919/PrimeBud-Turbo-1.0"

# ==============================
# MODELOS (LLaMA 3 no lugar do Mistral)
# ==============================
MODEL_IDS = {
    "LLaMA 3": "llama3",
    "CodeGemma 7B": "codegemma:7b",
    "Phi-3": "phi3",
}

# ==============================
# BASE DE USUÁRIOS (começa simples)
# ==============================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"teste": {"senha": "0000", "plano": "Free"}}

# ==============================
# DESCRIÇÕES DE MODO
# ==============================
MODOS_DESC = {
    "⚡ Flash": "Respostas curtas e instantâneas (LLaMA 3).",
    "🔵 Normal": "Respostas equilibradas e naturais (LLaMA 3, turbo).",
    "🍃 Econômico": "Respostas curtas e otimizadas (LLaMA 3).",
    "💬 Mini": "Conversas leves e sem código (LLaMA 3).",
    "💎 Pro (Beta)": "Código + explicação técnica curta (CodeGemma 7B).",
    "☄️ Ultra (Beta)": "Pipeline turbo (LLaMA 3 → CodeGemma 7B → Phi-3).",
    "✍️ Escritor": "Textos criativos (5–10 linhas) muito rápidos (Phi-3).",
    "🏫 Escola": "Ajuda escolar (1º–3º EM) — dupla rápida (Phi-3 + LLaMA 3).",
    # Modos profissionais (Assinatura Trabalho / Ultra / Professor)
    "👨‍🏫 Professor": "Explica conteúdos, cria plano de aula e exercícios (pipeline LLaMA 3 → CodeGemma → Phi-3).",
    "🎨 Designer": "Ideias visuais, UI/UX, prompts de imagem e estrutura de layout (pipeline LLaMA 3 → CodeGemma → Phi-3).",
    "💻 Codificador": "Gera, corrige e explica código limpo (pipeline LLaMA 3 → CodeGemma → Phi-3).",
    "🧩 Estratégias": "Estratégias de negócio/marketing/tech claras e acionáveis (pipeline LLaMA 3 → CodeGemma → Phi-3).",
}

# ==============================
# LIMITES DE MODELOS POR MODO
# ==============================
MODE_LIMITS = {
    "⚡ Flash": ["LLaMA 3"],
    "🔵 Normal": ["LLaMA 3"],
    "🍃 Econômico": ["LLaMA 3"],
    "💬 Mini": ["LLaMA 3"],
    "💎 Pro (Beta)": ["CodeGemma 7B"],
    "☄️ Ultra (Beta)": ["PIPELINE"],  # LLaMA3 -> CodeGemma -> Phi-3
    "✍️ Escritor": ["Phi-3"],
    "🏫 Escola": ["DUO"],             # Phi-3 + LLaMA 3
    # Modos Trabalho / Professor usam pipeline WORK dedicada
    "👨‍🏫 Professor": ["WORK"],
    "🎨 Designer": ["WORK"],
    "💻 Codificador": ["WORK"],
    "🧩 Estratégias": ["WORK"],
}

# ==============================
# PROMPTS DE ESTILO (objetivos = maior velocidade)
# ==============================
MODE_PROMPTS = {
    "⚡ Flash": "Responda em até 2 frases, direto e sem rodeios.",
    "🔵 Normal": "Explique de forma clara e breve (até 6 linhas).",
    "🍃 Econômico": "Máx. 3 linhas, direto ao ponto.",
    "💬 Mini": "Converse de modo leve e simples. Não gere código.",
    "💎 Pro (Beta)": "Forneça o código e breve explicação técnica (≤5 linhas).",
    "✍️ Escritor": "Crie um texto coeso e criativo de 5–10 linhas.",
    "🏫 Escola": "Explique e resolva dúvidas do Ensino Médio de forma didática e rápida.",
}

# ==============================
# FUNÇÃO BÁSICA DE CHAMADA AO OLLAMA (com timeout e stream=False)
# ==============================
def chat_ollama(model: str, prompt: str, options: dict | None = None, timeout: int = 30) -> str:
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": "Você é o PrimeBud. Seja objetivo, claro e útil."},
            {"role": "user", "content": prompt}
        ]
    }
    if options:
        payload["options"] = options

    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    try:
        data = r.json()
    except json.JSONDecodeError:
        # fallback caso venham múltiplas linhas JSON no buffer
        data = json.loads(r.text.strip().split("\n")[0])
    return data["message"]["content"]

# ==============================
# PIPELINES OTIMIZADAS (Turbo)
# ==============================

# Ultra: LLaMA 3 (resumo/entendimento) -> CodeGemma (código) -> Phi-3 (refino/explicação)
def gerar_resposta_ultra(msg: str) -> str:
    with concurrent.futures.ThreadPoolExecutor() as ex:
        f1 = ex.submit(chat_ollama, MODEL_IDS["LLaMA 3"], f"Resuma o problema com exatidão em 2 linhas: {msg}", {"num_predict": 100}, 15)
        llama = f1.result(timeout=15)
        f2 = ex.submit(chat_ollama, MODEL_IDS["CodeGemma 7B"], f"Gere código curto e funcional baseado em: {llama}", {"num_predict": 180}, 20)
        code = f2.result(timeout=20)
        phi = chat_ollama(MODEL_IDS["Phi-3"], f"Explique o código abaixo em até 5 linhas e cite 2 melhorias:\n{code}",
                          {"num_predict": 160}, 20)
    return phi

# Escola: duas respostas rápidas em paralelo e combinadas
def gerar_resposta_duo_escola(msg: str) -> str:
    with concurrent.futures.ThreadPoolExecutor() as ex:
        f1 = ex.submit(chat_ollama, MODEL_IDS["Phi-3"], f"Explique didaticamente para aluno do EM: {msg}", {"num_predict": 160}, 20)
        f2 = ex.submit(chat_ollama, MODEL_IDS["LLaMA 3"], f"Dê 1 exemplo prático simples sobre: {msg}", {"num_predict": 140}, 20)
        r1 = f1.result(timeout=20)
        r2 = f2.result(timeout=20)
    return f"{r1}\n\n📘 Exemplo:\n{r2}"

# Pipeline de Trabalho/Professor (WORK): LLaMA 3 -> CodeGemma -> Phi-3 com prompt específico por modo
def gerar_resposta_work(modo: str, msg: str) -> str:
    # 1) LLaMA 3: estrutura o plano/ideias iniciais
    if modo == "👨‍🏫 Professor":
        p1 = (f"Crie um plano de resposta educacional claro: objetivo, tópicos em bullets e sequência didática. "
              f"Foque em clareza para ensino médio.\nTema: {msg}")
    elif modo == "🎨 Designer":
        p1 = (f"Faça um esboço textual de ideias visuais (layout, hierarquia, tipografia, cores) em bullets. "
              f"Seja específico e prático para UI/UX.\nBriefing: {msg}")
    elif modo == "💻 Codificador":
        p1 = (f"Liste requisitos e estratégia de implementação em bullets curtos. "
              f"Em seguida, proponha uma arquitetura mínima.\nTarefa: {msg}")
    elif modo == "🧩 Estratégias":
        p1 = (f"Defina uma estratégia objetiva com metas, ações táticas e métricas (bullets). "
              f"Seja sucinto e acionável.\nDesafio: {msg}")
    else:
        p1 = f"Organize um plano objetivo em bullets para: {msg}"

    etapa1 = chat_ollama(MODEL_IDS["LLaMA 3"], p1, {"num_predict": 160}, 20)

    # 2) CodeGemma: converte o plano em material aplicável (código/estrutura/propostas)
    if modo == "💻 Codificador":
        p2 = (f"Com base no plano abaixo, gere um código curto e funcional (≤50 linhas) "
              f"e adicione comentários essenciais. Plano:\n{etapa1}")
    elif modo == "🎨 Designer":
        p2 = (f"Transforme o plano abaixo em entregáveis textuais (componentes, seções, grid, guidelines). "
              f"Inclua 1 estrutura de página em bullets. Plano:\n{etapa1}")
    elif modo == "👨‍🏫 Professor":
        p2 = (f"Transforme o plano abaixo em um mini-plano de aula + 3 exercícios com gabarito. "
              f"Plano:\n{etapa1}")
    else:  # Estratégias
        p2 = (f"Converta o plano abaixo em um playbook prático com ações sequenciadas (1-2 semanas). "
              f"Plano:\n{etapa1}")

    etapa2 = chat_ollama(MODEL_IDS["CodeGemma 7B"], p2, {"num_predict": 240}, 25)

    # 3) Phi-3: refina e entrega instruções finais curtas e claras
    p3 = (f"Refine o material abaixo em até 8 linhas, com passos claros e recomendações finais objetivas:\n{etapa2}")
    etapa3 = chat_ollama(MODEL_IDS["Phi-3"], p3, {"num_predict": 160}, 20)

    return etapa3

# ==================================
# GERADOR PADRÃO POR MODO
# ==================================
def gerar_resposta(modelo_display: str | None, modo: str, msg: str) -> str:
    # modos especiais com pipelines
    if modo == "☄️ Ultra (Beta)":
        return gerar_resposta_ultra(msg)
    if modo == "🏫 Escola":
        return gerar_resposta_duo_escola(msg)
    if MODE_LIMITS.get(modo) == ["WORK"]:
        return gerar_resposta_work(modo, msg)

    # modo Escritor turbo (Phi-3)
    if modo == "✍️ Escritor":
        prompt = (
            "Crie um texto de ALTA QUALIDADE com 5–10 linhas, direto ao ponto, coeso e sem enrolação.\n\n"
            f"Tema: {msg}"
        )
        return chat_ollama(
            MODEL_IDS["Phi-3"], prompt,
            {"temperature": 0.4, "num_predict": 200, "top_p": 0.8, "repeat_penalty": 1.1},
            25
        )

    # Pro Beta (CodeGemma)
    if modo == "💎 Pro (Beta)":
        prompt = f"{MODE_PROMPTS[modo]}\n\n{msg}"
        return chat_ollama(MODEL_IDS["CodeGemma 7B"], prompt, {"num_predict": 220}, 25)

    # Normal (LLaMA 3 turbo)
    if modo == "🔵 Normal":
        prompt = f"{MODE_PROMPTS[modo]}\n\nPergunta: {msg}"
        return chat_ollama(MODEL_IDS["LLaMA 3"], prompt, {"num_predict": 180}, 25)

    # Demais modos com seu modelo fixo/selecionado
    prompt = f"{MODE_PROMPTS.get(modo, 'Seja claro e objetivo.')}\n\nPergunta: {msg}"
    if modelo_display is None:
        # fallback seguro
        modelo_display = "LLaMA 3"
    model_id = MODEL_IDS[modelo_display]
    return chat_ollama(model_id, prompt, {"num_predict": 140}, 20)

# ==============================
# LOGIN / SIGN-UP / CONVIDADO
# ==============================
if "usuario" not in st.session_state: st.session_state.usuario = None
if "plano" not in st.session_state: st.session_state.plano = None

if st.session_state.usuario is None:
    st.title("🤖 PrimeBud Turbo 1.0")
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
                st.success("Login bem-sucedido!")
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
        if st.button("Entrar como convidado (Plano Ultra)"):
            st.session_state.usuario = "Convidado"
            st.session_state.plano = "Ultra"
            st.success("Entrou como convidado — Plano Ultra liberado.")
            st.rerun()
    st.stop()

usuario = st.session_state.usuario
plano = st.session_state.plano

# ==============================
# MÚLTIPLOS CHATS
# ==============================
if "chats" not in st.session_state: st.session_state.chats = []
if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = 0
    st.session_state.chats.append({"nome": "Chat 1", "historico": []})

def novo_chat():
    n = len(st.session_state.chats) + 1
    st.session_state.chats.append({"nome": f"Chat {n}", "historico": []})
    st.session_state.chat_atual = len(st.session_state.chats) - 1
    st.success(f"Novo chat criado — Chat {n}")
    st.rerun()

# ==============================
# SIDEBAR (estilo ChatGPT)
# ==============================
with st.sidebar:
    st.title(f"🤖 PrimeBud — {usuario}")
    st.markdown(f"**Plano:** {plano}")
    st.warning("💾 Conversas **não são salvas permanentemente**.")
    if st.button("➕ Novo chat"):
        novo_chat()

    # Lista de chats
    chats = [c["nome"] for c in st.session_state.chats]
    idx = st.radio("Seus chats:", list(range(len(chats))), format_func=lambda i: chats[i])
    st.session_state.chat_atual = idx

    # Modos por plano (incluindo a nova assinatura Trabalho e Professor)
    modos_por_plano = {
        "Free": ["💬 Mini", "🍃 Econômico", "✍️ Escritor", "🏫 Escola"],
        "Pro": ["⚡ Flash", "🔵 Normal", "💎 Pro (Beta)", "🍃 Econômico", "✍️ Escritor", "🏫 Escola"],
        "Ultra": ["⚡ Flash", "🔵 Normal", "💎 Pro (Beta)", "🍃 Econômico", "💬 Mini",
                  "☄️ Ultra (Beta)", "✍️ Escritor", "🏫 Escola",
                  "👨‍🏫 Professor", "🎨 Designer", "💻 Codificador", "🧩 Estratégias"],
        "Trabalho": ["👨‍🏫 Professor", "🎨 Designer", "💻 Codificador", "🧩 Estratégias",
                     "✍️ Escritor", "🏫 Escola"],
        "Professor": ["👨‍🏫 Professor", "🏫 Escola", "✍️ Escritor"],  # assinatura focada
    }

    # segurança: se plano desconhecido, cai no Ultra
    lista_modos = modos_por_plano.get(plano, modos_por_plano["Ultra"])
    modo = st.radio("Modo:", lista_modos)
    st.markdown(f"**Descrição:** {MODOS_DESC.get(modo, 'Modo customizado.')}")

    # Mostrar/ocultar seleção de LLM dependendo do modo
    allowed = MODE_LIMITS.get(modo, ["LLaMA 3"])
    if "PIPELINE" in allowed:
        st.info("☄️ Ultra (Beta) usa automaticamente: LLaMA 3 → CodeGemma 7B → Phi-3.")
        modelo_display = None
    elif "DUO" in allowed:
        st.info("🏫 Escola usa automaticamente: Phi-3 + LLaMA 3.")
        modelo_display = None
    elif "WORK" in allowed:
        st.info("Assinatura Trabalho (pipeline): LLaMA 3 → CodeGemma 7B → Phi-3.")
        modelo_display = None
    else:
        if len(allowed) == 1:
            modelo_display = allowed[0]
            st.success(f"LLM deste modo: **{modelo_display}**")
        else:
            modelo_display = st.selectbox("LLM:", allowed)
            st.success(f"LLM ativo: **{modelo_display}**")

# ==============================
# ÁREA PRINCIPAL DO CHAT
# ==============================
chat = st.session_state.chats[st.session_state.chat_atual]
st.markdown(f"### 💬 {chat['nome']}")

st.markdown("""
<style>
.chat-container{max-width:900px;margin:auto;}
.user-bubble{background:#2b313e;color:#fff;padding:10px;border-radius:10px;margin:6px 0;}
.bot-bubble{background:#ececf1;color:#000;padding:10px;border-radius:10px;margin:6px 0;}
</style>
""", unsafe_allow_html=True)
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

# Render histórico
for m in chat["historico"]:
    bubble = "user-bubble" if m["autor"] == "user" else "bot-bubble"
    st.markdown(f"<div class='{bubble}'><b>{'Você' if m['autor']=='user' else 'PrimeBud'}:</b> {m['texto']}</div>", unsafe_allow_html=True)

# Entrada
msg = st.chat_input("Envie uma mensagem…")
if msg:
    chat["historico"].append({"autor": "user", "texto": msg})
    with st.spinner("Processando… (máx ~30 s)"):
        resposta = gerar_resposta(modelo_display, modo, msg)
    chat["historico"].append({"autor": "bot", "texto": resposta})
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

