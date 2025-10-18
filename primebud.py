# PrimeBud 1.5 – unified UI + new modes + subscriptions
# -----------------------------------------------------
# ✅ Python 3.10–3.12
# ✅ `pip install streamlit requests python-dotenv`
# Optional providers (auto-detected): Ollama (local), Groq API, OpenAI API
# 
# Run: streamlit run app.py
# -----------------------------------------------------

from __future__ import annotations
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
import streamlit as st

# =============================
# Files & constants
# =============================
APP_NAME = "PrimeBud 1.5"
DATA_DIR = Path(".primebud_data")
USERS_FILE = DATA_DIR / "users_database.json"
CHATS_DIR = DATA_DIR / "chats"

# Theme colors (dark with orange accents)
PB_ORANGE = "#ff7a00"
PB_BG = "#0f0f10"
PB_TEXT = "#f6f6f7"
PB_MUTED = "#b7b7b9"
PB_CARD = "#17181a"

# =============================
# Modes & Plans (per user message)
# =============================
# NOTE: display names are exactly as requested.
MODES: Dict[str, Dict] = {
    "primebud_1_0": {
        "key": "primebud_1_0",
        "label": "PrimeBud 1.0",
        "desc": "Equilíbrio entre qualidade e velocidade.",
        "style": "balanced",
        "default_model": {
            "ollama": "llama3:8b",
            "groq": "llama-3.1-8b-instant",
            "openai": "gpt-4o-mini"
        }
    },
    "flash": {
        "key": "flash",
        "label": "PrimeBud 1.0 Flash",
        "desc": "Respostas curtas e muito rápidas.",
        "style": "flash",
        "default_model": {
            "ollama": "llama3.2:3b",
            "groq": "llama-3.1-8b-instant",
            "openai": "gpt-4o-mini"
        }
    },
    "helper": {
        "key": "helper",
        "label": "PrimeBud 1.0 Helper",
        "desc": "Modo unificado com perfis: Escola, Professor, Designer, Codificador e Estratégias.",
        "style": "helper",
        "profiles": ["Escola", "Professor", "Designer", "Codificador", "Estratégias"],
        "default_model": {
            "ollama": "llama3:8b",
            "groq": "llama-3.1-70b-versatile",
            "openai": "gpt-4o"
        }
    },
    "leve": {
        "key": "leve",
        "label": "PrimeBud 1.0 leve",
        "desc": "Econômico em tokens; objetiva e sucinta.",
        "style": "economy",
        "default_model": {
            "ollama": "qwen2:7b",
            "groq": "gemma2-9b-it",
            "openai": "gpt-4o-mini"
        }
    },
    "pro": {
        "key": "pro",
        "label": "PrimeBud 1.0 Pro",
        "desc": "Responde qualquer pergunta, com foco especial em CODIFICAÇÃO.",
        "style": "coder",
        "default_model": {
            "ollama": "codellama:13b-instruct",
            "groq": "llama-3.1-70b-versatile",
            "openai": "gpt-4.1"
        }
    },
    "ultra": {
        "key": "ultra",
        "label": "PrimeBud 1.0 Ultra",
        "desc": "Máxima profundidade, raciocínio estruturado e multimodal.",
        "style": "ultra",
        "default_model": {
            "ollama": "llama3:70b",
            "groq": "llama-3.1-70b-versatile",
            "openai": "gpt-4.1"
        }
    },
    "v15": {
        "key": "v15",
        "label": "PrimeBud 1.5",
        "desc": "Híbrido de Ultra + Pro: explica melhor, resume rápido, respostas que se destacam.",
        "style": "hybrid",
        "default_model": {
            "ollama": "llama3:70b",
            "groq": "llama-3.1-70b-versatile",
            "openai": "gpt-4.1"
        }
    },
}

PLANS = {
    "free": ["primebud_1_0", "flash", "helper"],
    "pro": ["primebud_1_0", "flash", "helper", "pro", "leve", "v15"],
    "ultra": list(MODES.keys()),  # all
}

# Removed: mini; Removed: professor/work subscription bundles

# =============================
# Utilities
# =============================

def ensure_storage():
    DATA_DIR.mkdir(exist_ok=True)
    CHATS_DIR.mkdir(exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({"users": {}}, ensure_ascii=False, indent=2), encoding="utf-8")


def load_users() -> Dict:
    ensure_storage()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"users": {}}


def save_users(db: Dict):
    ensure_storage()
    USERS_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def get_user_dir(username: str) -> Path:
    d = CHATS_DIR / username
    d.mkdir(exist_ok=True)
    return d


def list_chats(username: str) -> List[str]:
    d = get_user_dir(username)
    return sorted([p.name for p in d.glob("*.json")])


def read_chat(username: str, chat_file: str) -> Dict:
    p = get_user_dir(username) / chat_file
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"title": "Novo chat", "created": time.time(), "messages": []}


def write_chat(username: str, chat_file: str, data: Dict):
    p = get_user_dir(username) / chat_file
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# =============================
# Provider detection & calls
# =============================

def available_provider_for(mode_key: str) -> Dict:
    """Pick a provider based on env. Priority: Ollama (local) > Groq > OpenAI. Returns dict with 'name' and 'model'."""
    mode = MODES[mode_key]
    # Ollama
    if os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST"):
        return {"provider": "ollama", "model": mode["default_model"]["ollama"], "base_url": os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST")}
    # Groq
    if os.environ.get("GROQ_API_KEY"):
        return {"provider": "groq", "model": mode["default_model"]["groq"], "api_key": os.environ.get("GROQ_API_KEY")}
    # OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        return {"provider": "openai", "model": mode["default_model"]["openai"], "api_key": os.environ.get("OPENAI_API_KEY")}
    # Offline stub
    return {"provider": "stub", "model": "echo"}


def system_prompt_for(mode_key: str, helper_profile: Optional[str]) -> str:
    style = MODES[mode_key]["style"]
    base = [
        f"You are {APP_NAME}. Always be helpful, safe, and precise.",
        "Answer in the user's language (pt-BR if unclear).",
    ]
    if style == "flash":
        base.append("Be ultra-concise. 3–6 lines max unless asked.")
    elif style == "economy":
        base.append("Token-economy mode: short bullets, no fluff, cite steps succinctly.")
    elif style == "coder":
        base.append("Coding-first: when relevant, provide runnable code with comments, edge cases, and tests. Keep explanations compact.")
    elif style == "ultra":
        base.append("Go deep: structure, trade-offs, comparisons, and quick TL;DR at top.")
    elif style == "hybrid":
        base.append("Hybrid Ultra+Pro: detailed but clear; start with TL;DR, then Deep Dive; add quick summary bullets at end.")
    elif style == "helper":
        base.append("Unified Helper: adapt tone and structure to the selected profile.")
        if helper_profile:
            base.append(f"Active profile: {helper_profile}. Prioritize tasks and examples from this profile.")
            profile_tips = {
                "Escola": "Planejamento semanal, atividades práticas, rubricas simples e linguagem acessível a famílias.",
                "Professor": "CLIL/WIDA quando útil, objetivos de aprendizagem e critérios de avaliação.",
                "Designer": "Foco em UX limpo, hierarquia visual e componentes reutilizáveis.",
                "Codificador": "Passo a passo, estrutura de pastas, dependências e snippets testáveis.",
                "Estratégias": "Raciocínio estratégico, OKRs, roadmap em fases e riscos/mitigações.",
            }
            base.append("Perfil guidance: " + profile_tips.get(helper_profile, ""))
    else:
        base.append("Balanced mode: good detail and speed.")
    return "\n".join(base)


def call_llm(messages: List[Dict], mode_key: str, helper_profile: Optional[str] = None) -> str:
    sel = available_provider_for(mode_key)
    sp = system_prompt_for(mode_key, helper_profile)
    # prepend system
    wire = [{"role": "system", "content": sp}] + messages

    if sel["provider"] == "ollama":
        base = sel.get("base_url", "http://localhost:11434")
        try:
            r = requests.post(
                f"{base.rstrip('/')}/api/chat",
                json={"model": sel["model"], "messages": wire, "stream": False},
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("message", {}).get("content", "") or data.get("response", "")
        except Exception as e:
            return f"[Ollama offline] {e}\n\nResumo: {fallback_answer(messages, mode_key)}"

    if sel["provider"] == "groq":
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {sel['api_key']}", "Content-Type": "application/json"},
                json={
                    "model": sel["model"],
                    "messages": wire,
                    "temperature": 0.6,
                    "max_tokens": 1200,
                },
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[Groq não respondeu] {e}\n\nResumo: {fallback_answer(messages, mode_key)}"

    if sel["provider"] == "openai":
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {sel['api_key']}", "Content-Type": "application/json"},
                json={
                    "model": sel["model"],
                    "messages": wire,
                    "temperature": 0.6,
                    "max_tokens": 1200,
                },
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[OpenAI não respondeu] {e}\n\nResumo: {fallback_answer(messages, mode_key)}"

    # Stub – works offline
    return fallback_answer(messages, mode_key)


def fallback_answer(messages: List[Dict], mode_key: str) -> str:
    """Local fallback so the app always responds."""
    last_q = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    style = MODES[mode_key]["style"]
    if style in {"flash", "economy"}:
        return f"(Modo offline) Resposta breve: {last_q[:200]} → foco nos pontos-chave em 3 bullets."
    if style == "coder":
        return (
            "(Modo offline) Exemplo de solução em Python:\n\n"
            "```python\n# sua lógica aqui\nprint('Hello PrimeBud!')\n```\n\n"
            "Explique o objetivo, entradas/saídas e como testar."
        )
    if style in {"ultra", "hybrid"}:
        return (
            "**TL;DR:** resposta resumida em 2–3 linhas.\n\n"
            "**Análise:** passos, trade-offs, estrutura sugerida.\n\n"
            "**Próximos passos:** 1) … 2) … 3) …"
        )
    return f"(Modo offline) Resposta equilibrada para: {last_q[:180]}"


# =============================
# UI: theming
# =============================

def inject_css():
    st.markdown(
        f"""
        <style>
            .stApp {{ background:{PB_BG}; color:{PB_TEXT}; }}
            .pb-title {{
                font-size: 28px; font-weight: 800; text-align:center; margin: 14vh 0 12px 0;
                color:{PB_TEXT}; letter-spacing: 0.5px;
            }}
            .pb-subtitle {{ color:{PB_MUTED}; text-align:center; margin-bottom: 26px; }}
            .pb-frame {{ border: 1px solid {PB_ORANGE}; border-radius: 14px; padding: 16px; background:{PB_CARD}; }}
            .pb-accent {{ color:{PB_ORANGE}; }}
            .pb-chip {{
                display:inline-block; padding:6px 10px; border:1px solid {PB_ORANGE}; border-radius: 999px; margin:2px 6px 2px 0;
                font-size:12px; color:{PB_TEXT};
            }}
            div[data-baseweb="select"]>div {{ background:{PB_CARD}; }}
            .stTextInput>div>div>input, textarea {{ color:{PB_TEXT} !important; }}
            .stButton>button {{ border:1px solid {PB_ORANGE}; background:transparent; color:{PB_TEXT}; }}
            .stButton>button:hover {{ background:{PB_ORANGE}22; }}
            .stRadio>div>div {{ background:transparent; }}
            .pb-chatbox {{ position: fixed; bottom: 22px; left: 50%; transform: translateX(-50%); width: min(820px, 90vw); }}
            .pb-divider {{ height:1px; background:{PB_ORANGE}; opacity:.25; margin:12px 0 18px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================
# Auth
# =============================

def auth_screen() -> Optional[Dict]:
    st.markdown(f"<div class='pb-title'>Bem-vindo ao <span class='pb-accent'>{APP_NAME}</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='pb-subtitle'>Faça login, crie sua conta ou entre como convidado.</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Entrar")
        with st.container(border=True):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            if st.button("Login"):
                db = load_users()
                u = db["users"].get(username)
                if u and u.get("password") == password:
                    st.session_state.user = {"username": username, "plan": u.get("plan", "free")}
                    st.success("Login realizado!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
    with col2:
        st.markdown("### Criar conta")
        with st.container(border=True):
            nu = st.text_input("Novo usuário")
            npw = st.text_input("Nova senha", type="password")
            plan = st.selectbox("Plano", ["free", "pro", "ultra"], index=0, help="Você pode alternar depois editando o banco local.")
            if st.button("Registrar"):
                if not nu or not npw:
                    st.warning("Preencha usuário e senha.")
                else:
                    db = load_users()
                    if nu in db["users"]:
                        st.error("Usuário já existe.")
                    else:
                        db["users"][nu] = {"password": npw, "plan": plan}
                        save_users(db)
                        st.success("Conta criada! Faça login à esquerda.")

    st.divider()
    if st.button("Continuar como Convidado (Plano Free)"):
        st.session_state.user = {"username": "guest", "plan": "free"}
        st.success("Entrou como convidado.")
        st.rerun()

    # Footer badge showing the requested branding: "PrimeBud 1.5"
    st.markdown(
        f"<div style='text-align:center;margin-top:22px;opacity:.8'>Interface {APP_NAME} — laranja de contorno, fundo escuro e texto branco.</div>",
        unsafe_allow_html=True,
    )
    return None


# =============================
# Sidebar (chats, modes, plan)
# =============================

def sidebar(user: Dict):
    with st.sidebar:
        st.markdown(f"#### Conta: `{user['username']}`  · Plano: **{user['plan'].upper()}**")
        st.markdown("<div class='pb-divider'></div>", unsafe_allow_html=True)

        # Mode selection respecting plan
        allowed = [k for k in PLANS[user["plan"]]]
        labels = [MODES[k]["label"] for k in allowed]
        idx = 0
        if "selected_mode" in st.session_state and st.session_state.selected_mode in allowed:
            idx = allowed.index(st.session_state.selected_mode)
        choice = st.selectbox("Modo", labels, index=idx)
        selected_key = allowed[labels.index(choice)]
        st.session_state.selected_mode = selected_key
        st.caption(MODES[selected_key]["desc"])

        helper_profile = None
        if selected_key == "helper":
            helper_profile = st.selectbox("Perfil do Helper", MODES["helper"]["profiles"], index=0)
            st.session_state.helper_profile = helper_profile
        else:
            st.session_state.helper_profile = None

        st.markdown("<div class='pb-divider'></div>", unsafe_allow_html=True)

        # Chat management
        st.markdown("#### Conversas")
        chats = list_chats(user["username"]) or []
        show_label = "(novo)"
        if "current_chat" not in st.session_state:
            st.session_state.current_chat = None
        selected_chat = st.selectbox("Abrir chat salvo", [show_label] + chats, index=0)

        colA, colB, colC = st.columns([1,1,1])
        with colA:
            if st.button("Novo"):
                st.session_state.messages = []
                st.session_state.current_chat = None
                st.toast("Novo chat iniciado.")
        with colB:
            if st.button("Salvar"):
                now = datetime.now().strftime("%Y%m%d-%H%M%S")
                title = generate_title_from_messages(st.session_state.messages) or f"chat-{now}"
                fname = f"{title}.json"
                data = {"title": title, "created": time.time(), "mode": st.session_state.selected_mode, "messages": st.session_state.messages}
                write_chat(user["username"], fname, data)
                st.session_state.current_chat = fname
                st.toast("Chat salvo.")
        with colC:
            if st.button("Excluir"):
                if selected_chat != show_label:
                    p = get_user_dir(user["username"]) / selected_chat
                    try:
                        p.unlink(missing_ok=True)
                        st.toast("Chat excluído.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
                else:
                    st.info("Selecione um chat salvo para excluir.")

        if selected_chat != show_label:
            data = read_chat(user["username"], selected_chat)
            st.session_state.messages = data.get("messages", [])
            st.session_state.current_chat = selected_chat

        st.markdown("<div class='pb-divider'></div>", unsafe_allow_html=True)

        # Provider info
        sel = available_provider_for(st.session_state.selected_mode)
        st.markdown(f"**Provider:** `{sel['provider']}` · **Model:** `{sel['model']}`")
        if sel["provider"] == "stub":
            st.info("Nenhum provedor detectado. Rodando em modo offline (respostas de demonstração).\n\nPara ativar: defina OLLAMA_BASE_URL ou GROQ_API_KEY ou OPENAI_API_KEY.")


def generate_title_from_messages(msgs: List[Dict]) -> str:
    if not msgs:
        return "novo-chat"
    txt = next((m["content"] for m in msgs if m["role"] == "user"), msgs[0]["content"])[:40]
    safe = "".join(c for c in txt if c.isalnum() or c in ("-", "_", " ")).strip().replace(" ", "-")
    return safe or "chat"


# =============================
# Chat screen
# =============================

def chat_ui(user: Dict):
    inject_css()

    # Empty state header similar to the reference image
    if not st.session_state.get("messages"):
        st.markdown("""
            <div class='pb-title'>What can I help with?</div>
        """, unsafe_allow_html=True)

    # Render history
    for m in st.session_state.get("messages", []):
        with st.container(border=True):
            if m["role"] == "user":
                st.markdown(f"**Você:**\n\n{m['content']}")
            else:
                st.markdown(f"**{MODES[st.session_state.selected_mode]['label']}:**\n\n{m['content']}")

    st.markdown("""
    <div class='pb-chatbox'>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        prompt = st.text_area("", placeholder="Pergunte qualquer coisa…", height=80)
        c1, c2, c3 = st.columns([1,1,3])
        send = c1.button("Enviar", use_container_width=True)
        clear = c2.button("Limpar", use_container_width=True)
        if clear:
            st.session_state.messages = []
            st.rerun()

    st.markdown("""
    </div>
    """, unsafe_allow_html=True)

    if send and prompt.strip():
        st.session_state.messages = st.session_state.get("messages", [])
        st.session_state.messages.append({"role": "user", "content": prompt.strip(), "ts": time.time()})
        with st.spinner("Pensando…"):
            ans = call_llm(
                messages=st.session_state.messages,
                mode_key=st.session_state.selected_mode,
                helper_profile=st.session_state.get("helper_profile")
            )
        st.session_state.messages.append({"role": "assistant", "content": ans, "ts": time.time()})
        st.rerun()


# =============================
# Main
# =============================

def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
    ensure_storage()

    if "user" not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        auth_screen()
        return

    # Sidebar & chat
    sidebar(st.session_state.user)
    chat_ui(st.session_state.user)


if __name__ == "__main__":
    main()

