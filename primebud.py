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

# Estilos CSS customizados - Interface mais limpa
st.markdown("""
<style>
    /* Tema escuro */
    .main {
        background-color: #0e1117;
    }
    
    /* Remover padding extra */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
    
    /* Estilo dos inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #333;
        border-radius: 8px;
    }
    
    .stSelectbox > div > div > select {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #333;
    }
    
    /* Mensagens do chat */
    .chat-message {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
        max-width: 75%;
        word-wrap: break-word;
    }
    
    .user-message {
        background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);
        color: white;
        margin-left: auto;
        margin-right: 0;
        text-align: right;
    }
    
    .assistant-message {
        background-color: #1e1e1e;
        color: #e0e0e0;
        border: 1px solid #333;
        margin-right: auto;
        margin-left: 0;
    }
    
    .message-label {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-bottom: 0.3rem;
        font-weight: 600;
    }
    
    /* Botões */
    .stButton > button {
        background-color: #ff6b35;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #ff8555;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #ff6b35;
        font-weight: 700;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0e1117;
    }
    
    /* Container de mensagens */
    .messages-container {
        height: 60vh;
        overflow-y: auto;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Scrollbar customizada */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e1e1e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #ff6b35;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #ff8555;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #1e1e1e;
        border-left: 4px solid #ff6b35;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1e1e1e;
        border-radius: 8px 8px 0 0;
        color: #ffffff;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ff6b35;
    }
    
    /* Remover espaço extra dos elementos */
    .element-container {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Configuração do banco de dados
def init_db():
    conn = sqlite3.connect('primebud.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            plan TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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

def create_guest_user():
    """Cria um usuário convidado temporário"""
    import random
    guest_id = f"guest_{random.randint(10000, 99999)}"
    return {
        'id': guest_id,
        'username': f'Convidado #{guest_id.split("_")[1]}',
        'plan': 'free',
        'is_guest': True
    }

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
        "name": "🚀 Flash",
        "description": "Rápido e direto",
        "system_prompt": "Você é um assistente rápido e direto. Responda de forma concisa e objetiva.",
        "temperature": 0.3,
        "max_tokens": 500,
    },
    "standard": {
        "name": "⚡ Standard",
        "description": "Equilibrado",
        "system_prompt": "Você é um assistente útil e equilibrado. Forneça respostas completas mas não excessivamente longas.",
        "temperature": 0.7,
        "max_tokens": 1500,
    },
    "light": {
        "name": "💡 Light",
        "description": "Simples e claro",
        "system_prompt": "Você é um assistente que explica conceitos de forma simples e acessível. Use linguagem clara e exemplos práticos.",
        "temperature": 0.5,
        "max_tokens": 1000,
    },
    "pro": {
        "name": "🎯 Pro",
        "description": "Técnico e detalhado",
        "system_prompt": "Você é um assistente técnico especializado. Forneça respostas detalhadas com explicações técnicas precisas.",
        "temperature": 0.8,
        "max_tokens": 2500,
    },
    "ultra": {
        "name": "🔥 Ultra",
        "description": "Análise profunda",
        "system_prompt": "Você é um assistente altamente especializado. Forneça análises profundas, considere múltiplas perspectivas e seja extremamente detalhado.",
        "temperature": 0.9,
        "max_tokens": 4000,
    },
    "helper": {
        "name": "🤝 Helper",
        "description": "Amigável",
        "system_prompt": "Você é um assistente amigável e prestativo. Seja empático, use tom conversacional e ajude o usuário de forma calorosa.",
        "temperature": 0.7,
        "max_tokens": 2000,
    },
    "v1_5": {
        "name": "⭐ v1.5",
        "description": "Híbrido (Recomendado)",
        "system_prompt": "Você é o Primebud 1.5, um assistente híbrido que combina clareza com profundidade. Forneça respostas bem estruturadas, detalhadas quando necessário, mas sempre mantendo a clareza e objetividade.",
        "temperature": 0.75,
        "max_tokens": 3000,
    },
}

# Função para chamar Groq API
def get_groq_response(messages, mode="v1_5"):
    try:
        api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
        if not api_key:
            return "❌ Erro: GROQ_API_KEY não configurada."
        
        client = Groq(api_key=api_key)
        config = MODES_CONFIG[mode]
        
        full_messages = [
            {"role": "system", "content": config["system_prompt"]}
        ] + messages
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=full_messages,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Erro: {str(e)}"

# Inicializar banco de dados
init_db()

# Inicializar session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'guest_chats' not in st.session_state:
    st.session_state.guest_chats = {}
if 'guest_messages' not in st.session_state:
    st.session_state.guest_messages = {}

# Interface de autenticação
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🤖 PrimeBud 2.0")
        st.markdown("### Seu assistente de IA inteligente")
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Cadastro", "👤 Convidado"])
        
        with tab1:
            st.markdown("#### Entre com sua conta")
            login_username = st.text_input("Usuário", key="login_user")
            login_password = st.text_input("Senha", type="password", key="login_pass")
            
            if st.button("Entrar", key="login_btn", use_container_width=True):
                user = verify_user(login_username, login_password)
                if user:
                    st.session_state.user = {
                        'id': user[0],
                        'username': user[1],
                        'plan': user[2],
                        'is_guest': False
                    }
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos")
        
        with tab2:
            st.markdown("#### Criar nova conta")
            signup_username = st.text_input("Usuário", key="signup_user")
            signup_password = st.text_input("Senha", type="password", key="signup_pass")
            signup_password_confirm = st.text_input("Confirmar Senha", type="password", key="signup_pass_confirm")
            
            if st.button("Cadastrar", key="signup_btn", use_container_width=True):
                if signup_password != signup_password_confirm:
                    st.error("❌ As senhas não coincidem")
                elif len(signup_password) < 6:
                    st.error("❌ A senha deve ter pelo menos 6 caracteres")
                elif create_user(signup_username, signup_password):
                    st.success("✅ Conta criada! Faça login para continuar.")
                else:
                    st.error("❌ Nome de usuário já existe")
        
        with tab3:
            st.markdown("#### Acesso rápido sem cadastro")
            st.info("💡 Como convidado, seus chats não serão salvos permanentemente.")
            
            if st.button("🚀 Entrar como Convidado", key="guest_btn", use_container_width=True):
                st.session_state.user = create_guest_user()
                st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; opacity: 0.7;'>
            <p><strong>7 Modos de IA</strong> • <strong>Powered by Groq</strong> • <strong>GPT-OSS 120B</strong></p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Interface principal
    with st.sidebar:
        st.markdown("### 🤖 PrimeBud 2.0")
        st.markdown(f"**{st.session_state.user['username']}**")
        st.markdown(f"*{st.session_state.user['plan']}*")
        st.markdown("---")
        
        if st.button("➕ Novo Chat", use_container_width=True):
            if st.session_state.user.get('is_guest'):
                # Criar chat para convidado
                import random
                chat_id = f"guest_chat_{random.randint(10000, 99999)}"
                st.session_state.guest_chats[chat_id] = {
                    'name': f"Chat {len(st.session_state.guest_chats) + 1}",
                    'mode': 'v1_5'
                }
                st.session_state.guest_messages[chat_id] = []
                st.session_state.current_chat_id = chat_id
            else:
                chats = get_user_chats(st.session_state.user['id'])
                chat_name = f"Chat {len(chats) + 1}"
                chat_id = create_chat(st.session_state.user['id'], chat_name)
                st.session_state.current_chat_id = chat_id
            st.rerun()
        
        st.markdown("#### 💬 Chats")
        
        # Listar chats
        if st.session_state.user.get('is_guest'):
            chats = [(k, v['name'], v['mode'], '') for k, v in st.session_state.guest_chats.items()]
        else:
            chats = get_user_chats(st.session_state.user['id'])
        
        if not chats:
            st.info("Crie um novo chat!")
        else:
            for chat in chats:
                chat_id, chat_name, chat_mode, _ = chat
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    is_current = chat_id == st.session_state.current_chat_id
                    if st.button(
                        f"{'📌 ' if is_current else ''}{chat_name}",
                        key=f"chat_{chat_id}",
                        use_container_width=True
                    ):
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{chat_id}"):
                        if st.session_state.user.get('is_guest'):
                            del st.session_state.guest_chats[chat_id]
                            if chat_id in st.session_state.guest_messages:
                                del st.session_state.guest_messages[chat_id]
                        else:
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 Modos Disponíveis
            
            - 🚀 **Flash** - Rápido e direto
            - ⚡ **Standard** - Equilibrado
            - 💡 **Light** - Simples e claro
            - 🎯 **Pro** - Técnico e detalhado
            """)
        
        with col2:
            st.markdown("""
            ### 
            
            - 🔥 **Ultra** - Análise profunda
            - 🤝 **Helper** - Amigável
            - ⭐ **v1.5** - Híbrido (Recomendado)
            """)
        
        st.info("💡 Crie um novo chat ou selecione um existente para começar!")
    
    else:
        # Obter informações do chat
        if st.session_state.user.get('is_guest'):
            chat_info = (
                st.session_state.guest_chats[st.session_state.current_chat_id]['name'],
                st.session_state.guest_chats[st.session_state.current_chat_id]['mode']
            )
        else:
            conn = sqlite3.connect('primebud.db')
            c = conn.cursor()
            c.execute('SELECT name, mode FROM chats WHERE id = ?', (st.session_state.current_chat_id,))
            chat_info = c.fetchone()
            conn.close()
        
        if chat_info:
            chat_name, current_mode = chat_info
            
            # Cabeçalho compacto
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### 💬 {chat_name}")
            
            with col2:
                mode_options = {k: v["name"] for k, v in MODES_CONFIG.items()}
                selected_mode = st.selectbox(
                    "Modo",
                    options=list(mode_options.keys()),
                    format_func=lambda x: mode_options[x],
                    index=list(mode_options.keys()).index(current_mode),
                    key="mode_selector",
                    label_visibility="collapsed"
                )
                
                if selected_mode != current_mode:
                    if st.session_state.user.get('is_guest'):
                        st.session_state.guest_chats[st.session_state.current_chat_id]['mode'] = selected_mode
                    else:
                        update_chat_mode(st.session_state.current_chat_id, selected_mode)
                    st.rerun()
            
            st.caption(MODES_CONFIG[current_mode]['description'])
            st.markdown("---")
            
            # Área de mensagens com altura fixa
            messages_container = st.container()
            
            with messages_container:
                if st.session_state.user.get('is_guest'):
                    messages = st.session_state.guest_messages.get(st.session_state.current_chat_id, [])
                else:
                    messages = get_chat_messages(st.session_state.current_chat_id)
                
                if not messages:
                    st.info("🤖 Olá! Como posso ajudar você hoje?")
                else:
                    for msg in messages:
                        if st.session_state.user.get('is_guest'):
                            role, content = msg['role'], msg['content']
                        else:
                            role, content, _ = msg
                        
                        if role == "user":
                            st.markdown(f'<div class="chat-message user-message"><div class="message-label">Você</div>{content}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message assistant-message"><div class="message-label">🤖 PrimeBud</div>{content}</div>', unsafe_allow_html=True)
            
            # Input de mensagem - apenas Enter para enviar
            st.markdown("---")
            
            # Usar form para capturar Enter
            with st.form(key="message_form", clear_on_submit=True):
                user_input = st.text_area(
                    "Digite sua mensagem e pressione Ctrl+Enter:",
                    key="user_input",
                    height=80,
                    placeholder="Digite aqui... (Ctrl+Enter para enviar)"
                )
                
                submitted = st.form_submit_button("📤 Enviar", use_container_width=True)
                
                if submitted and user_input.strip():
                    # Salvar mensagem do usuário
                    if st.session_state.user.get('is_guest'):
                        if st.session_state.current_chat_id not in st.session_state.guest_messages:
                            st.session_state.guest_messages[st.session_state.current_chat_id] = []
                        st.session_state.guest_messages[st.session_state.current_chat_id].append({
                            'role': 'user',
                            'content': user_input
                        })
                        messages = st.session_state.guest_messages[st.session_state.current_chat_id]
                    else:
                        save_message(st.session_state.current_chat_id, "user", user_input)
                        messages = get_chat_messages(st.session_state.current_chat_id)
                    
                    # Preparar histórico
                    api_messages = []
                    for msg in messages:
                        if st.session_state.user.get('is_guest'):
                            api_messages.append({"role": msg['role'], "content": msg['content']})
                        else:
                            role, content, _ = msg
                            api_messages.append({"role": role, "content": content})
                    
                    # Obter resposta
                    with st.spinner("🤔 Pensando..."):
                        response = get_groq_response(api_messages, current_mode)
                    
                    # Salvar resposta
                    if st.session_state.user.get('is_guest'):
                        st.session_state.guest_messages[st.session_state.current_chat_id].append({
                            'role': 'assistant',
                            'content': response
                        })
                    else:
                        save_message(st.session_state.current_chat_id, "assistant", response)
                    
                    st.rerun()

