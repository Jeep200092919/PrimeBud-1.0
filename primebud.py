import streamlit as st
import sqlite3
import hashlib
import re
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

# Estilos CSS - Tema claro moderno
st.markdown("""
<style>
    /* Tema escuro elegante */
    .main {
        background-color: #1a1d23;
    }
    
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 0.5rem;
        max-width: 1200px;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #2d3139;
        color: #e8e8e8;
        border: 2px solid #3d4149;
        border-radius: 10px;
        font-size: 0.95rem;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #ff6b35;
        box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.3);
    }
    
    .stTextArea > div > div > textarea {
        min-height: 60px !important;
        max-height: 60px !important;
    }
    
    .stSelectbox > div > div > select {
        background-color: #2d3139;
        color: #e8e8e8;
        border: 2px solid #3d4149;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Mensagens do chat */
    .chat-message {
        padding: 1.2rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        max-width: 80%;
        word-wrap: break-word;
        line-height: 1.6;
        animation: fadeIn 0.3s ease-in;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);
        color: white;
        margin-left: auto;
        margin-right: 0;
    }
    
    .assistant-message {
        background-color: #2d3139;
        color: #e8e8e8;
        border: 2px solid #3d4149;
        margin-right: auto;
        margin-left: 0;
    }
    
    .message-label {
        font-size: 0.7rem;
        opacity: 0.7;
        margin-bottom: 0.5rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Botões */
    .stButton > button {
        background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(255, 107, 53, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 107, 53, 0.4);
    }
    
    /* Botão de copiar código */
    .copy-button {
        background: #4CAF50;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.4rem 1rem;
        font-size: 0.8rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        margin-top: 0.5rem;
    }
    
    .copy-button:hover {
        background: #45a049;
        transform: scale(1.05);
    }
    
    /* Títulos */
    h1 {
        color: #ff6b35;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    h2, h3 {
        color: #ff6b35;
        font-weight: 700;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1d23;
        border-right: 2px solid #2d3139;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: #2d3139;
        border: 2px solid #3d4149;
        color: #e8e8e8;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);
        border: none;
        color: white;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1d23;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #ff8555;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #1e3a5f;
        border-left: 4px solid #2196F3;
        border-radius: 8px;
        color: #e8e8e8;
    }
    
    .stSuccess {
        background-color: #1e4620;
        border-left: 4px solid #4CAF50;
        color: #e8e8e8;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2d3139;
        border-radius: 10px;
        color: #888;
        padding: 12px 24px;
        font-weight: 600;
        border: 2px solid #3d4149;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);
        color: white;
        border: none;
    }
    
    /* Badge do modo */
    .mode-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);
        color: white;
        margin-left: 0.5rem;
    }
    
    /* Container de chat */
    .chat-container {
        background-color: #0f1115;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        min-height: 60vh;
        max-height: 60vh;
        overflow-y: auto;
        border: 2px solid #2d3139;
    }
    
    /* Código com syntax highlighting */
    pre {
        background-color: #1e1e1e !important;
        color: #d4d4d4 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        overflow-x: auto !important;
        margin: 1rem 0 !important;
        border: 2px solid #333 !important;
    }
    
    code {
        background-color: #1e1e1e !important;
        color: #d4d4d4 !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 4px !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Download button */
    .download-button {
        background: #2196F3;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        margin-top: 0.5rem;
        display: inline-block;
    }
    
    .download-button:hover {
        background: #1976D2;
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# Função para detectar e formatar código
def format_message_with_code(content):
    """Detecta blocos de código e adiciona syntax highlighting"""
    # Detectar blocos de código com ```
    code_pattern = r'```(\w+)?\n(.*?)```'
    
    def replace_code(match):
        language = match.group(1) or 'text'
        code = match.group(2)
        # Escapar HTML
        code = code.replace('<', '&lt;').replace('>', '&gt;')
        return f'''
        <div style="position: relative;">
            <pre><code class="language-{language}">{code}</code></pre>
            <button class="copy-button" onclick="navigator.clipboard.writeText(`{code.replace('`', '\\`')}`)">📋 Copiar Código</button>
        </div>
        '''
    
    formatted = re.sub(code_pattern, replace_code, content, flags=re.DOTALL)
    
    # Detectar código inline com `
    inline_pattern = r'`([^`]+)`'
    formatted = re.sub(inline_pattern, r'<code>\1</code>', formatted)
    
    return formatted

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
            mode TEXT DEFAULT 'primebud_1_5',
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
    import random
    guest_id = f"guest_{random.randint(10000, 99999)}"
    return {
        'id': guest_id,
        'username': f'Convidado #{guest_id.split("_")[1]}',
        'plan': 'free',
        'is_guest': True
    }

# Funções de chat
def create_chat(user_id, name, mode='primebud_1_5'):
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

# Função para exportar chat
def export_chat_to_text(messages, chat_name):
    """Exporta o histórico do chat para texto"""
    text = f"# {chat_name}\n"
    text += f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
    text += "="*50 + "\n\n"
    
    for msg in messages:
        if isinstance(msg, dict):
            role, content = msg['role'], msg['content']
        else:
            role, content, _ = msg
        
        if role == "user":
            text += f"👤 VOCÊ:\n{content}\n\n"
        else:
            text += f"🤖 PRIMEBUD:\n{content}\n\n"
        
        text += "-"*50 + "\n\n"
    
    return text

# Configuração dos 4 modos principais
MODES_CONFIG = {
    "primebud_1_0_flash": {
        "name": "⚡ PrimeBud 1.0 Flash",
        "short_name": "Flash",
        "description": "Respostas ultrarrápidas e diretas",
        "system_prompt": "Você é o PrimeBud 1.0 Flash. Forneça respostas extremamente rápidas, diretas e concisas. Vá direto ao ponto sem rodeios.",
        "temperature": 0.3,
        "max_tokens": 500,
    },
    "primebud_1_0": {
        "name": "🔵 PrimeBud 1.0",
        "short_name": "1.0",
        "description": "Versão clássica balanceada",
        "system_prompt": "Você é o PrimeBud 1.0, a versão clássica. Forneça respostas equilibradas, completas e bem estruturadas, mantendo clareza e objetividade.",
        "temperature": 0.7,
        "max_tokens": 2000,
    },
    "primebud_1_5": {
        "name": "⭐ PrimeBud 1.5",
        "short_name": "1.5",
        "description": "Híbrido inteligente (Recomendado)",
        "system_prompt": "Você é o PrimeBud 1.5, a versão híbrida premium. Combine clareza com profundidade, sendo detalhado quando necessário mas sempre mantendo objetividade e estrutura clara. Quando fornecer código, use blocos de código markdown com ```linguagem para melhor formatação.",
        "temperature": 0.75,
        "max_tokens": 3000,
    },
    "primebud_2_0": {
        "name": "🚀 PrimeBud 2.0",
        "short_name": "2.0",
        "description": "Versão avançada com máxima capacidade",
        "system_prompt": "Você é o PrimeBud 2.0, a versão mais avançada. Forneça análises profundas, respostas extremamente detalhadas e completas, explorando múltiplas perspectivas e nuances. Seja o mais abrangente possível. Quando fornecer código, sempre use blocos de código markdown com ```linguagem.",
        "temperature": 0.85,
        "max_tokens": 4000,
    },
}

# Função para chamar Groq API
def get_groq_response(messages, mode="primebud_1_5"):
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
        return f"❌ Erro ao processar: {str(e)}"

# Inicializar
init_db()

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
        st.markdown("<h1 style='text-align: center;'>🤖 PrimeBud 2.0</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.1rem; color: #666;'>Assistente de IA de Nova Geração</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Cadastro", "👤 Convidado"])
        
        with tab1:
            st.markdown("#### Entre com sua conta")
            login_username = st.text_input("Usuário", key="login_user", placeholder="Digite seu usuário")
            login_password = st.text_input("Senha", type="password", key="login_pass", placeholder="Digite sua senha")
            
            if st.button("🚀 Entrar", key="login_btn", use_container_width=True):
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
            signup_username = st.text_input("Usuário", key="signup_user", placeholder="Escolha um usuário")
            signup_password = st.text_input("Senha", type="password", key="signup_pass", placeholder="Mínimo 6 caracteres")
            signup_password_confirm = st.text_input("Confirmar Senha", type="password", key="signup_pass_confirm", placeholder="Digite novamente")
            
            if st.button("✨ Criar Conta", key="signup_btn", use_container_width=True):
                if signup_password != signup_password_confirm:
                    st.error("❌ As senhas não coincidem")
                elif len(signup_password) < 6:
                    st.error("❌ A senha deve ter pelo menos 6 caracteres")
                elif create_user(signup_username, signup_password):
                    st.success("✅ Conta criada com sucesso! Faça login para continuar.")
                else:
                    st.error("❌ Nome de usuário já existe")
        
        with tab3:
            st.markdown("#### Acesso rápido")
            st.info("💡 Experimente sem cadastro! Seus chats não serão salvos permanentemente.")
            
            if st.button("🎯 Entrar como Convidado", key="guest_btn", use_container_width=True):
                st.session_state.user = create_guest_user()
                st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <p style='color: #666; font-size: 0.9rem;'>
                <strong>4 Modos Inteligentes</strong> • <strong>Powered by Groq</strong><br>
                <span style='color: #ff6b35;'>GPT-OSS 120B</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Interface principal
    with st.sidebar:
        st.markdown("### 🤖 PrimeBud 2.0")
        st.markdown(f"**👤 {st.session_state.user['username']}**")
        st.caption(f"Plano: {st.session_state.user['plan'].upper()}")
        st.markdown("---")
        
        if st.button("➕ Novo Chat", use_container_width=True, key="new_chat"):
            if st.session_state.user.get('is_guest'):
                import random
                chat_id = f"guest_chat_{random.randint(10000, 99999)}"
                st.session_state.guest_chats[chat_id] = {
                    'name': f"Chat {len(st.session_state.guest_chats) + 1}",
                    'mode': 'primebud_1_5'
                }
                st.session_state.guest_messages[chat_id] = []
                st.session_state.current_chat_id = chat_id
            else:
                chats = get_user_chats(st.session_state.user['id'])
                chat_name = f"Chat {len(chats) + 1}"
                chat_id = create_chat(st.session_state.user['id'], chat_name)
                st.session_state.current_chat_id = chat_id
            st.rerun()
        
        st.markdown("#### 💬 Seus Chats")
        
        if st.session_state.user.get('is_guest'):
            chats = [(k, v['name'], v['mode'], '') for k, v in st.session_state.guest_chats.items()]
        else:
            chats = get_user_chats(st.session_state.user['id'])
        
        if not chats:
            st.caption("Nenhum chat ainda")
        else:
            for chat in chats:
                chat_id, chat_name, chat_mode, _ = chat
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    is_current = chat_id == st.session_state.current_chat_id
                    button_label = f"{'📌 ' if is_current else ''}{chat_name}"
                    if st.button(button_label, key=f"chat_{chat_id}", use_container_width=True):
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
        st.markdown("<h1 style='text-align: center;'>👋 Bem-vindo ao PrimeBud 2.0</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;'>Escolha um modo e comece a conversar</p>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            for mode_key in ["primebud_1_0_flash", "primebud_1_0"]:
                mode = MODES_CONFIG[mode_key]
                st.markdown(f"""
                <div style='background: #2d3139; 
                            padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; 
                            border: 2px solid #3d4149; box-shadow: 0 2px 8px rgba(0,0,0,0.3);'>
                    <h3>{mode['name']}</h3>
                    <p style='color: #666;'>{mode['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            for mode_key in ["primebud_1_5", "primebud_2_0"]:
                mode = MODES_CONFIG[mode_key]
                st.markdown(f"""
                <div style='background: #2d3139; 
                            padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; 
                            border: 2px solid #3d4149; box-shadow: 0 2px 8px rgba(0,0,0,0.3);'>
                    <h3>{mode['name']}</h3>
                    <p style='color: #666;'>{mode['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.info("💡 Crie um novo chat para começar!")
    
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
            
            # Cabeçalho
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                mode_name = MODES_CONFIG[current_mode]['short_name']
                st.markdown(f"### 💬 {chat_name} <span class='mode-badge'>{mode_name}</span>", unsafe_allow_html=True)
            
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
            
            with col3:
                # Botão de download
                if st.session_state.user.get('is_guest'):
                    messages = st.session_state.guest_messages.get(st.session_state.current_chat_id, [])
                else:
                    messages = get_chat_messages(st.session_state.current_chat_id)
                
                if messages:
                    chat_text = export_chat_to_text(messages, chat_name)
                    st.download_button(
                        label="📥 Exportar",
                        data=chat_text,
                        file_name=f"{chat_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            st.caption(MODES_CONFIG[current_mode]['description'])
            st.markdown("---")
            
            # Container de mensagens
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            
            if not messages:
                st.markdown("""
                <div style='text-align: center; padding: 3rem; color: #666;'>
                    <h2>🤖</h2>
                    <p style='font-size: 1.1rem;'>Olá! Como posso ajudar você hoje?</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                for msg in messages:
                    if st.session_state.user.get('is_guest'):
                        role, content = msg['role'], msg['content']
                    else:
                        role, content, _ = msg
                    
                    if role == "user":
                        st.markdown(f'<div class="chat-message user-message"><div class="message-label">Você</div>{content}</div>', unsafe_allow_html=True)
                    else:
                        formatted_content = format_message_with_code(content)
                        st.markdown(f'<div class="chat-message assistant-message"><div class="message-label">🤖 PrimeBud</div>{formatted_content}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Input
            with st.form(key="message_form", clear_on_submit=True):
                user_input = st.text_area(
                    "Mensagem",
                    key="user_input",
                    placeholder="Digite sua mensagem... (Ctrl+Enter para enviar)",
                    label_visibility="collapsed"
                )
                
                submitted = st.form_submit_button("📤 Enviar", use_container_width=True)
                
                if submitted and user_input.strip():
                    # Salvar mensagem
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
                    with st.spinner("🤔 Processando..."):
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

