import streamlit as st
import sqlite3
import hashlib
import json
from datetime import datetime
from groq import Groq
import os

# Configuração da página
st.set_page_config(
    page_title="PrimeBud 2.0",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS customizados
st.markdown("""
<style>
    .main {
        background-color: #1a1a1a;
    }
    .stTextInput > div > div > input {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    .stSelectbox > div > div > select {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #ff6b35;
        color: white;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #2d2d2d;
        color: white;
        margin-right: 20%;
        border: 1px solid #404040;
    }
    .stButton > button {
        background-color: #ff6b35;
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #ff8555;
    }
    h1, h2, h3 {
        color: #ff6b35;
    }
    .sidebar .sidebar-content {
        background-color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

# Configuração do banco de dados
def init_db():
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            plan TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de chats
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            mode TEXT DEFAULT 'v1_5',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Tabela de mensagens
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Funções de autenticação
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                  (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    c.execute('SELECT id, username, plan FROM users WHERE username = ? AND password_hash = ?',
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

# Funções de chat
def create_chat(user_id, name, mode='v1_5'):
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    c.execute('INSERT INTO chats (user_id, name, mode) VALUES (?, ?, ?)',
              (user_id, name, mode))
    chat_id = c.lastrowid
    conn.commit()
    conn.close()
    return chat_id

def get_user_chats(user_id):
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    c.execute('SELECT id, name, mode, created_at FROM chats WHERE user_id = ? ORDER BY updated_at DESC',
              (user_id,))
    chats = c.fetchall()
    conn.close()
    return chats

def get_chat_messages(chat_id):
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    c.execute('SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY created_at',
              (chat_id,))
    messages = c.fetchall()
    conn.close()
    return messages

def save_message(chat_id, role, content):
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    c.execute('INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)',
              (chat_id, role, content))
    c.execute('UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (chat_id,))
    conn.commit()
    conn.close()

def update_chat_mode(chat_id, mode):
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    c.execute('UPDATE chats SET mode = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
              (mode, chat_id))
    conn.commit()
    conn.close()

def delete_chat(chat_id):
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    c.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
    c.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
    conn.commit()
    conn.close()

# Configuração dos modos
MODES_CONFIG = {
    "flash": {
        "name": "🚀 Primebud 1.0 Flash",
        "description": "Respostas rápidas e diretas",
        "system_prompt": "Você é um assistente rápido e direto. Responda de forma concisa e objetiva.",
        "temperature": 0.3,
        "max_tokens": 500,
    },
    "standard": {
        "name": "⚡ Primebud 1.0",
        "description": "Equilíbrio entre velocidade e qualidade",
        "system_prompt": "Você é um assistente útil e equilibrado. Forneça respostas completas mas não excessivamente longas.",
        "temperature": 0.7,
        "max_tokens": 1500,
    },
    "light": {
        "name": "💡 Primebud 1.0 Leve",
        "description": "Respostas simples e fáceis de entender",
        "system_prompt": "Você é um assistente que explica conceitos de forma simples e acessível. Use linguagem clara e exemplos práticos.",
        "temperature": 0.5,
        "max_tokens": 1000,
    },
    "pro": {
        "name": "🎯 Primebud 1.0 Pro",
        "description": "Respostas técnicas e detalhadas",
        "system_prompt": "Você é um assistente técnico especializado. Forneça respostas detalhadas com explicações técnicas precisas.",
        "temperature": 0.8,
        "max_tokens": 2500,
    },
    "ultra": {
        "name": "🔥 Primebud 1.0 Ultra",
        "description": "Análises profundas e abrangentes",
        "system_prompt": "Você é um assistente altamente especializado. Forneça análises profundas, considere múltiplas perspectivas e seja extremamente detalhado.",
        "temperature": 0.9,
        "max_tokens": 4000,
    },
    "helper": {
        "name": "🤝 Primebud 1.0 Helper",
        "description": "Assistente amigável e prestativo",
        "system_prompt": "Você é um assistente amigável e prestativo. Seja empático, use tom conversacional e ajude o usuário de forma calorosa.",
        "temperature": 0.7,
        "max_tokens": 2000,
    },
    "v1_5": {
        "name": "⭐ Primebud 1.5",
        "description": "Híbrido - clareza e profundidade",
        "system_prompt": "Você é o Primebud 1.5, um assistente híbrido que combina clareza com profundidade. Forneça respostas bem estruturadas, detalhadas quando necessário, mas sempre mantendo a clareza e objetividade.",
        "temperature": 0.75,
        "max_tokens": 3000,
    },
}

# Função para chamar Groq API
def get_groq_response(messages, mode="v1_5"):
    try:
        # Verificar se a API key está configurada
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "❌ Erro: GROQ_API_KEY não configurada. Configure a variável de ambiente GROQ_API_KEY com sua chave da API Groq."
        
        client = Groq(api_key=api_key)
        config = MODES_CONFIG[mode]
        
        # Adicionar system prompt
        full_messages = [
            {"role": "system", "content": config["system_prompt"]}
        ] + messages
        
        # Chamar API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=full_messages,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Erro ao chamar API Groq: {str(e)}"

# Inicializar banco de dados
init_db()

# Inicializar session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None

# Interface de autenticação
if st.session_state.user is None:
    st.title("🤖 PrimeBud 2.0")
    st.subheader("Seu assistente de IA mais inteligente")
    
    tab1, tab2 = st.tabs(["Login", "Cadastro"])
    
    with tab1:
        st.markdown("### Entrar")
        login_username = st.text_input("Usuário", key="login_user")
        login_password = st.text_input("Senha", type="password", key="login_pass")
        
        if st.button("Entrar", key="login_btn"):
            user = verify_user(login_username, login_password)
            if user:
                st.session_state.user = {
                    'id': user[0],
                    'username': user[1],
                    'plan': user[2]
                }
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos")
    
    with tab2:
        st.markdown("### Criar Conta")
        signup_username = st.text_input("Usuário", key="signup_user")
        signup_password = st.text_input("Senha", type="password", key="signup_pass")
        signup_password_confirm = st.text_input("Confirmar Senha", type="password", key="signup_pass_confirm")
        
        if st.button("Cadastrar", key="signup_btn"):
            if signup_password != signup_password_confirm:
                st.error("❌ As senhas não coincidem")
            elif len(signup_password) < 6:
                st.error("❌ A senha deve ter pelo menos 6 caracteres")
            elif create_user(signup_username, signup_password):
                st.success("✅ Conta criada com sucesso! Faça login para continuar.")
            else:
                st.error("❌ Nome de usuário já existe")
    
    # Informações sobre o app
    st.markdown("---")
    st.markdown("""
    ### 🌟 Características do PrimeBud 2.0
    
    - 🚀 **7 Modos de Resposta** - Do Flash ao Ultra
    - 💾 **Múltiplos Chats** - Organize suas conversas
    - 🔒 **Seguro** - Seus dados são protegidos
    - 🎨 **Interface Moderna** - Design limpo e intuitivo
    - ⚡ **Powered by Groq** - GPT-OSS 120B
    """)

else:
    # Interface principal
    with st.sidebar:
        st.title("🤖 PrimeBud 2.0")
        st.markdown(f"**Usuário:** {st.session_state.user['username']}")
        st.markdown(f"**Plano:** {st.session_state.user['plan']}")
        st.markdown("---")
        
        # Botão novo chat
        if st.button("➕ Novo Chat", use_container_width=True):
            chats = get_user_chats(st.session_state.user['id'])
            chat_name = f"Chat {len(chats) + 1}"
            chat_id = create_chat(st.session_state.user['id'], chat_name)
            st.session_state.current_chat_id = chat_id
            st.rerun()
        
        st.markdown("### 💬 Seus Chats")
        
        # Listar chats
        chats = get_user_chats(st.session_state.user['id'])
        
        if not chats:
            st.info("Nenhum chat ainda. Crie um novo!")
        else:
            for chat in chats:
                chat_id, chat_name, chat_mode, created_at = chat
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if st.button(
                        f"{'📌 ' if chat_id == st.session_state.current_chat_id else ''}{chat_name}",
                        key=f"chat_{chat_id}",
                        use_container_width=True
                    ):
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{chat_id}"):
                        delete_chat(chat_id)
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                        st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None
            st.session_state.current_chat_id = None
            st.rerun()
    
    # Área principal
    if st.session_state.current_chat_id is None:
        st.title("👋 Bem-vindo ao PrimeBud 2.0!")
        st.markdown("""
        ### Comece criando um novo chat ou selecionando um existente
        
        #### 🎯 Modos Disponíveis:
        
        - 🚀 **Flash** - Respostas rápidas e diretas
        - ⚡ **Standard** - Equilíbrio entre velocidade e qualidade
        - 💡 **Light** - Explicações simples e acessíveis
        - 🎯 **Pro** - Respostas técnicas detalhadas
        - 🔥 **Ultra** - Análises profundas e abrangentes
        - 🤝 **Helper** - Assistente amigável e prestativo
        - ⭐ **v1.5** - Híbrido com clareza e profundidade (Recomendado)
        """)
    else:
        # Obter informações do chat atual
        conn = sqlite3.connect('primebud.db')
        c = conn.cursor()
        c.execute('SELECT name, mode FROM chats WHERE id = ?', (st.session_state.current_chat_id,))
        chat_info = c.fetchone()
        conn.close()
        
        if chat_info:
            chat_name, current_mode = chat_info
            
            # Cabeçalho do chat
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.title(f"💬 {chat_name}")
            
            with col2:
                # Seletor de modo
                mode_options = {k: v["name"] for k, v in MODES_CONFIG.items()}
                selected_mode = st.selectbox(
                    "Modo",
                    options=list(mode_options.keys()),
                    format_func=lambda x: mode_options[x],
                    index=list(mode_options.keys()).index(current_mode),
                    key="mode_selector"
                )
                
                if selected_mode != current_mode:
                    update_chat_mode(st.session_state.current_chat_id, selected_mode)
                    st.rerun()
            
            st.markdown(f"**{MODES_CONFIG[current_mode]['description']}**")
            st.markdown("---")
            
            # Área de mensagens
            messages = get_chat_messages(st.session_state.current_chat_id)
            
            if not messages:
                st.info("🤖 Olá! Como posso ajudar você hoje?")
            else:
                for role, content, created_at in messages:
                    if role == "user":
                        st.markdown(f'<div class="chat-message user-message"><strong>Você:</strong><br>{content}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-message assistant-message"><strong>🤖 PrimeBud:</strong><br>{content}</div>', unsafe_allow_html=True)
            
            # Input de mensagem
            st.markdown("---")
            user_input = st.text_area("Digite sua mensagem:", key="user_input", height=100)
            
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                send_button = st.button("📤 Enviar", use_container_width=True)
            
            with col2:
                clear_button = st.button("🗑️ Limpar Chat", use_container_width=True)
            
            if send_button and user_input.strip():
                # Salvar mensagem do usuário
                save_message(st.session_state.current_chat_id, "user", user_input)
                
                # Preparar histórico para API
                api_messages = []
                for role, content, _ in messages:
                    api_messages.append({"role": role, "content": content})
                api_messages.append({"role": "user", "content": user_input})
                
                # Obter resposta
                with st.spinner("🤔 Pensando..."):
                    response = get_groq_response(api_messages, current_mode)
                
                # Salvar resposta
                save_message(st.session_state.current_chat_id, "assistant", response)
                
                st.rerun()
            
            if clear_button:
                conn = sqlite3.connect('primebud.db')
                c = conn.cursor()
                c.execute('DELETE FROM messages WHERE chat_id = ?', (st.session_state.current_chat_id,))
                conn.commit()
                conn.close()
                st.rerun()

