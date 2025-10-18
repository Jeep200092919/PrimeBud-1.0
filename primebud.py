# PrimeBud 1.5 – interface atualizada + modos + Groq exclusivo (GPT OSS 120B)
# -----------------------------------------------------
# ✅ Python 3.10–3.12
# ✅ `pip install streamlit requests python-dotenv`
# Apenas usa a API do Groq com o modelo GPT OSS 120B
# Enviar mensagens com Enter
# -----------------------------------------------------

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests
import streamlit as st

APP_NAME = "PrimeBud 1.5"
DATA_DIR = Path(".primebud_data")
USERS_FILE = DATA_DIR / "users_database.json"
CHATS_DIR = DATA_DIR / "chats"

# Cores: preto básico, texto branco, contornos laranja
PB_ORANGE = "#ff7a00"
PB_BG = "#0f0f10"
PB_TEXT = "#ffffff"
PB_CARD = "#17181a"

MODES = {
    "primebud_1_0": {"label": "Primebud 1.0", "desc": "Modo padrão equilibrado."},
    "flash": {"label": "Primebud 1.0 Flash", "desc": "Respostas rápidas e curtas."},
    "helper": {"label": "Primebud 1.0 Helper", "desc": "Perfis: Escola, Professor, Designer, Codificador e Estratégias."},
    "leve": {"label": "Primebud 1.0 leve", "desc": "Versão econômica e objetiva."},
    "pro": {"label": "Primebud 1.0 Pro", "desc": "Foco em codificação e respostas completas."},
    "ultra": {"label": "Primebud 1.0 Ultra", "desc": "Respostas detalhadas e estruturadas."},
    "v15": {"label": "Primebud 1.5", "desc": "Combina Ultra e Pro, com resumos e explicações claras."}
}

PLANS = {
    "free": ["primebud_1_0", "flash", "helper"],
    "pro": ["primebud_1_0", "flash", "helper", "pro", "leve", "v15"],
    "ultra": list(MODES.keys())
}

def ensure_storage():
    DATA_DIR.mkdir(exist_ok=True)
    CHATS_DIR.mkdir(exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({"users": {}}, indent=2), encoding="utf-8")

def load_users():
    ensure_storage()
    try:
        return json.loads(USERS_FILE.read_text())
    except Exception:
        return {"users": {}}

def save_users(db: Dict):
    USERS_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")

def get_user_dir(username: str):
    d = CHATS_DIR / username
    d.mkdir(exist_ok=True)
    return d

def list_chats(username: str):
    d = get_user_dir(username)
    return sorted([p.name for p in d.glob("*.json")])

def read_chat(username: str, chat_file: str):
    p = get_user_dir(username) / chat_file
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {"messages": []}

def write_chat(username: str, chat_file: str, data: Dict):
    p = get_user_dir(username) / chat_file
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")

# =========================================================
# Groq API (GPT OSS 120B)
# =========================================================

def call_llm(messages: List[Dict]):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "[Erro] Defina GROQ_API_KEY para usar o modelo GPT OSS 120B."
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-oss-120b",  # modelo especificado
                "messages": messages,
                "temperature": 0.6,
                "max_tokens": 1500,
            },
            timeout=180,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Erro na Groq API] {e}"

# =========================================================
# Interface visual
# =========================================================

def inject_css():
    st.markdown(f"""
    <style>
    .stApp {{ background:{PB_BG}; color:{PB_TEXT}; }}
    .pb-title {{ text-align:center; margin-top:15vh; font-size:28px; color:{PB_TEXT}; }}
    .stTextArea textarea {{ background:{PB_CARD}; color:{PB_TEXT}; border:1px solid {PB_ORANGE}; border-radius:8px; }}
    .stChatInput textarea {{ background:{PB_CARD}; color:{PB_TEXT}; border:1px solid {PB_ORANGE}; border-radius:8px; }}
    .stButton>button {{ border:1px solid {PB_ORANGE}; color:{PB_TEXT}; background:transparent; }}
    .stButton>button:hover {{ background:{PB_ORANGE}33; }}
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# Login simples (mantido igual)
# =========================================================

def auth_screen():
    st.markdown(f"<div class='pb-title'>Bem-vindo ao <span style='color:{PB_ORANGE}'>{APP_NAME}</span></div>", unsafe_allow_html=True)
    st.write("Login igual ao anterior — apenas o nome e cores foram atualizados.")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        db = load_users()
        u = db["users"].get(username)
        if u and u.get("password") == password:
            st.session_state.user = {"username": username, "plan": u.get("plan", "free")}
            st.success("Login realizado!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    if st.button("Entrar como Convidado"):
        st.session_state.user = {"username": "guest", "plan": "free"}
        st.rerun()

# =========================================================
# Chat + Groq (Enter para enviar)
# =========================================================

def chat_ui(user: Dict):
    inject_css()

    if not st.session_state.get("messages"):
        st.markdown(f"<div class='pb-title'>What can I help with?</div>", unsafe_allow_html=True)

    for m in st.session_state.get("messages", []):
        role = "Você" if m["role"] == "user" else "PrimeBud"
        st.markdown(f"**{role}:** {m['content']}")

    user_input = st.chat_input("Digite e pressione Enter…")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("Pensando…"):
            reply = call_llm(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# =========================================================
# Main
# =========================================================

def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🤖", layout="wide")
    ensure_storage()
    if "user" not in st.session_state:
        st.session_state.user = None
    if not st.session_state.user:
        auth_screen()
        return
    chat_ui(st.session_state.user)

if __name__ == "__main__":
    main()

