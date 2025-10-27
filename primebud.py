import streamlit as st
import sqlite3
import hashlib  # <-- Revertido para hashlib
import re
import os
import random
from datetime import datetime
from groq import Groq
from contextlib import contextmanager
import google.generativeai as genai # <-- NOVO IMPORT

# 1. Configuração da Página
st.set_page_config(
    page_title="PrimeBud 2.0",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Configuração dos Modos (ATUALIZADO PARA LLAMA 3)
MODES_CONFIG = {
    "primebud_1_0_flash": {
        "name": "⚡ PrimeBud 1.0 Flash (Groq)",
        "short_name": "Flash",
        "description": "Respostas ultrarrápidas (GPT-OSS 120B)", # <-- ATUALIZADO
        "system_prompt": "Você é o PrimeBud 1.0 Flash. Forneça respostas extremamente rápidas, diretas e concisas. Vá direto ao ponto sem rodeios.",
        "temperature": 0.3,
        "max_tokens": 500,
        "api_provider": "groq", # <-- Define o provedor
        "model": "openai/gpt-oss-120b" # <-- ATUALIZADO CONFORME O SEU PEDIDO
    },
    "primebud_1_0": {
        "name": "🔵 PrimeBud 1.0 (Groq)",
        "short_name": "1.0",
        "description": "Versão clássica balanceada (GPT-OSS 120B)", # <-- ATUALIZADO
        "system_prompt": "Você é o PrimeBud 1.0, a versão clássica. Forneça respostas equilibradas, completas e bem estruturadas, mantendo clareza e objetividade.",
        "temperature": 0.7,
        "max_tokens": 2000,
        "api_provider": "groq",
        "model": "openai/gpt-oss-120b" # <-- ATUALIZADO CONFORME O SEU PEDIDO
    },
    "primebud_1_5": {
        "name": "⭐ PrimeBud 1.5 (Groq)",
        "short_name": "1.5",
        "description": "Híbrido inteligente (GPT-OSS 120B)", # <-- ATUALIZADO
        "system_prompt": "Você é o PrimeBud 1.5, a versão híbrida premium. Combine clareza com profundidade, sendo detalhado quando necessário mas sempre mantendo objetividade e estrutura clara. Quando fornecer código, use blocos de código markdown com ```linguagem para melhor formatação.",
        "temperature": 0.75,
        "max_tokens": 3000,
        "api_provider": "groq",
        "model": "openai/gpt-oss-120b" # <-- ATUALIZADO CONFORME O SEU PEDIDO
    },
    "primebud_2_0": {
        "name": "🚀 PrimeBud 2.0 (Gemini)", # <-- MUDOU
        "short_name": "2.0 Gemini",
        "description": "Versão avançada com máxima capacidade (Gemini)",
        "system_prompt": "Você é o PrimeBud 2.0, rodando no Gemini 2.5. Você é a versão mais avançada. Forneça análises profundas, respostas extremamente detalhadas e completas, explorando múltiplas perspectivas e nuances. Seja o mais abrangente possível. Quando fornecer código, sempre use blocos de código markdown com ```linguagem.",
        "temperature": 0.85,
        "max_tokens": 4000,
        "api_provider": "gemini", # <-- MUDOU
        "model": "gemini-2.5-flash-preview-09-2025" # <-- MUDOU (Conforme solicitado)
    },
}

# 3. Estilos CSS
# (O seu CSS completo está aqui)
st.markdown("""
<style>
    /* ... Seu CSS completo vai aqui ... */
    /* Tema escuro elegante */
    .main {
        background-color: #1a1d23;
    }
    
    .block-container {
        padding-top: 3rem; /* <-- CORREÇÃO DO CSS APLICADA AQUI */
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


# 4. Funções Utilitárias (Helpers)
def format_message_with_code(content):
    """Detecta blocos de código e adiciona syntax highlighting e botão de copiar."""
    code_pattern = r'```(\w+)?\n(.*?)```'
    
    def replace_code(match):
        language = match.group(1) or 'text'
        code = match.group(2)
        # Escapar HTML e backticks para o JS
        code_html_escaped = code.replace('<', '&lt;').replace('>', '&gt;')
        code_js_escaped = code.replace('`', '\\`').replace('\\', '\\\\')
        
        return f'''
        <div style="position: relative; margin: 1rem 0;">
            <pre><code class="language-{language}">{code_html_escaped}</code></pre>
            <button class="copy-button" onclick="navigator.clipboard.writeText(`{code_js_escaped}`)">📋 Copiar Código</button>
        </div>
        '''
    
    formatted = re.sub(code_pattern, replace_code, content, flags=re.DOTALL)
    inline_pattern = r'`([^`]+)`'
    formatted = re.sub(inline_pattern, r'<code>\1</code>', formatted)
    
    return formatted

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
            # Lidar com 'assistant' (Groq) e 'model' (Gemini)
            text += f"🤖 PRIMEBUD:\n{content}\n\n"
        
        text += "-"*50 + "\n\n"
    
    return text

# 5. Funções de Banco de Dados (SQLite)
DB_NAME = 'primebud.db'

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        st.error(f"Erro no banco de dados: {e}")
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
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

# --- Funções de Autenticação (DB) ---
def hash_password(password):
    # Revertido para hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    # Revertido para hashlib
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                          (username, hash_password(password)))
            conn.commit()
        return True, "Conta criada com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Nome de usuário já existe."
    except Exception as e:
        return False, f"Erro inesperado: {e}"

def verify_user(username, password):
    # Revertido para hashlib
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT id, username, plan FROM users WHERE username = ? AND password_hash = ?',
                    (username, hash_password(password)))
        return c.fetchone()

# --- Funções de Chat (DB) ---
def create_chat(user_id, name, mode='primebud_1_5'):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO chats (user_id, name, mode) VALUES (?, ?, ?)',
                    (user_id, name, mode))
        chat_id = c.lastrowid
        conn.commit()
        return chat_id

def get_user_chats(user_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT id, name, mode, created_at FROM chats WHERE user_id = ? ORDER BY updated_at DESC',
                    (user_id,))
        return c.fetchall()

def get_chat_messages(chat_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY created_at',
                    (chat_id,))
        return c.fetchall()

def get_chat_info(chat_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT name, mode FROM chats WHERE id = ?', (chat_id,))
        return c.fetchone()

def save_message(chat_id, role, content):
    # Garante que o role do Gemini ('model') seja salvo como 'assistant'
    db_role = "assistant" if role == "model" else role
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)',
                    (chat_id, db_role, content))
        c.execute('UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (chat_id,))
        conn.commit()

def update_chat_mode(chat_id, mode):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('UPDATE chats SET mode = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (mode, chat_id))
        conn.commit()

def delete_chat(chat_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
        c.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
        conn.commit()

# 6. Funções de Cliente de API (ATUALIZADO)

def get_groq_response(messages, config):
    """Chama a API Groq (Llama 3).""" # <-- ATUALIZADO
    try:
        api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
        if not api_key:
            return "❌ Erro: GROQ_API_KEY não configurada."
        
        client = Groq(api_key=api_key)
        
        # Groq precisa de 'system' no início
        full_messages = [
            {"role": "system", "content": config["system_prompt"]}
        ] + messages
        
        response = client.chat.completions.create(
            model=config["model"],
            messages=full_messages,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
        )
        
        return response.choices[0].message.content, "assistant" # Retorna role
    except Exception as e:
        st.error(f"Erro ao contatar a API Groq: {e}")
        return f"❌ Erro ao processar: {str(e)}", "assistant"

def get_gemini_response(messages, config):
    """Chama a API Gemini (NOVA FUNÇÃO)."""
    try:
        api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            return "❌ Erro: GEMINI_API_KEY não configurada."
        
        genai.configure(api_key=api_key)
        
        # Formatar mensagens para o Gemini: 'assistant' -> 'model'
        gemini_messages_formatted = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            gemini_messages_formatted.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        model = genai.GenerativeModel(
            model_name=config["model"],
            system_instruction=config["system_prompt"],
            generation_config=genai.GenerationConfig(
                temperature=config["temperature"],
                max_output_tokens=config["max_tokens"]
            )
        )
        
        # Otimização: remove mensagens consecutivas da mesma role
        cleaned_messages = []
        if gemini_messages_formatted:
            cleaned_messages.append(gemini_messages_formatted[0])
            for i in range(1, len(gemini_messages_formatted)):
                if gemini_messages_formatted[i]["role"] != cleaned_messages[-1]["role"]:
                    cleaned_messages.append(gemini_messages_formatted[i])
                else:
                    # Se for a mesma role, concatena o conteúdo (caso raro)
                    cleaned_messages[-1]["parts"][0]["text"] += "\n" + gemini_messages_formatted[i]["parts"][0]["text"]


        response = model.generate_content(cleaned_messages)
        
        return response.text, "model" # Retorna role
    except Exception as e:
        st.error(f"Erro ao contatar a API Gemini: {e}")
        # Tenta extrair uma mensagem de erro mais clara da resposta da API
        try:
            error_details = str(e)
            if "API key not valid" in error_details:
                return "❌ Erro: A chave da API Gemini não é válida. Verifique seus secrets.", "model"
            if "quota" in error_details:
                return "❌ Erro: Você excedeu sua cota na API Gemini.", "model"
        except:
            pass
        return f"❌ Erro ao processar com Gemini: {str(e)}", "model"


def generate_chat_response(messages, mode):
    """Roteador: Chama a API correta com base no modo (NOVA FUNÇÃO)."""
    config = MODES_CONFIG[mode]
    provider = config.get("api_provider", "groq") # Padrão é Groq
    
    if provider == "gemini":
        return get_gemini_response(messages, config)
    else: # 'groq'
        return get_groq_response(messages, config)


# 7. Função de Usuário Convidado
def create_guest_user():
    import random
    guest_id = f"guest_{random.randint(10000, 99999)}"
    return {
        'id': guest_id,
        'username': f'Convidado #{guest_id.split("_")[1]}',
        'plan': 'free',
        'is_guest': True
    }

# 8. Inicialização da Aplicação
init_db()  # Garante que as tabelas existem

if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'guest_chats' not in st.session_state:
    st.session_state.guest_chats = {}
if 'guest_messages' not in st.session_state:
    st.session_state.guest_messages = {}

# 9. Lógica Principal da UI

# --- TELA DE AUTENTICAÇÃO ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🤖 PrimeBud 2.0</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.1rem; color: #aaa;'>Assistente de IA de Nova Geração</p>", unsafe_allow_html=True)
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
                else:
                    success, message = create_user(signup_username, signup_password)
                    if success:
                        st.success(f"✅ {message} Faça login para continuar.")
                    else:
                        st.error(f"❌ {message}")
        
        with tab3:
            st.markdown("#### Acesso rápido")
            st.info("💡 Experimente sem cadastro! Seus chats são temporários.")
            
            if st.button("🎯 Entrar como Convidado", key="guest_btn", use_container_width=True):
                st.session_state.user = create_guest_user()
                st.rerun()
        
        st.markdown("---")
        # ATUALIZADO para refletir os modelos corretos
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <p style='color: #aaa; font-size: 0.9rem;'>
                <strong>Multi-API</strong> • <strong>Powered by Groq & Gemini</strong><br>
                <span style='color: #ff6b35;'>GPT-OSS 120B (Groq) & Gemini 2.5</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

# --- TELA PRINCIPAL (APP) ---
else:
    # --- SIDEBAR (Barra Lateral) ---
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
            chats.reverse()
        else:
            chats = get_user_chats(st.session_state.user['id'])
        
        if not chats:
            st.caption("Nenhum chat ainda")
        else:
            for chat in chats:
                chat_id, chat_name, chat_mode, _ = chat
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    is_current = (chat_id == st.session_state.current_chat_id)
                    button_label = f"{'📌 ' if is_current else ''}{chat_name}"
                    if st.button(button_label, key=f"chat_{chat_id}", use_container_width=True):
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{chat_id}", help="Excluir chat"):
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

    # --- ÁREA PRINCIPAL ---
    if st.session_state.current_chat_id is None:
        # Tela de Boas-Vindas (com exemplos)
        st.markdown("<h1 style='text-align: center;'>👋 Bem-vindo ao PrimeBud 2.0</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #aaa; margin-bottom: 2rem;'>Sua assistente Multi-API. Escolha um modo e comece a conversar.</p>", unsafe_allow_html=True)
        
        st.markdown("### 🚀 Nossos Modos de IA")
        col1, col2 = st.columns(2)
        
        with col1:
            for mode_key in ["primebud_1_0_flash", "primebud_1_5"]:
                mode = MODES_CONFIG[mode_key]
                st.markdown(f"""
                <div style='background: #2d3139; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; border: 2px solid #3d4149; box-shadow: 0 2px 8px rgba(0,0,0,0.3);'>
                    <h3>{mode['name']}</h3>
                    <p style='color: #aaa;'>{mode['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            for mode_key in ["primebud_1_0", "primebud_2_0"]:
                mode = MODES_CONFIG[mode_key]
                st.markdown(f"""
                <div style='background: #2d3139; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; border: 2px solid #3d4149; box-shadow: 0 2px 8px rgba(0,0,0,0.3);'>
                    <h3>{mode['name']}</h3>
                    <p style='color: #aaa;'>{mode['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🤔 Experimente perguntar")

        ex_col1, ex_col2, ex_col3 = st.columns(3)
        with ex_col1:
            st.info("Me explique o que é computação quântica em termos simples.")
        with ex_col2:
            st.info("Escreva um código em Python para um jogo da cobrinha (snake).")
        with ex_col3:
            st.info("Quais são os prós e contras de usar React vs. Vue?")

        st.info("💡 **Para começar, clique em '➕ Novo Chat' na barra lateral!**")
    
    else:
        # --- TELA DE CHAT ATIVO ---
        if st.session_state.user.get('is_guest'):
            chat = st.session_state.guest_chats[st.session_state.current_chat_id]
            chat_info = (chat['name'], chat['mode'])
        else:
            chat_info = get_chat_info(st.session_state.current_chat_id)
        
        if chat_info:
            chat_name, current_mode = chat_info
            
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
            
            # Obter mensagens formatadas para a API
            messages_for_api = []
            if st.session_state.user.get('is_guest'):
                messages_for_api = st.session_state.guest_messages.get(st.session_state.current_chat_id, [])
            else:
                db_messages = get_chat_messages(st.session_state.current_chat_id)
                # Formato para API: [{'role': ..., 'content': ...}]
                messages_for_api = [{"role": m[0], "content": m[1]} for m in db_messages]

            with col3:
                if messages_for_api:
                    chat_text = export_chat_to_text(messages_for_api, chat_name)
                    st.download_button(
                        label="📥 Exportar",
                        data=chat_text,
                        file_name=f"{chat_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            st.caption(MODES_CONFIG[current_mode]['description'])
            st.markdown("---")
            
            # Container de Mensagens
            if not messages_for_api:
                st.markdown("""
                <div style='text-align: center; padding: 3rem; color: #aaa;'>
                    <h2>🤖</h2>
                    <p style='font-size: 1.1rem;'>Olá! Como posso ajudar você hoje?</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                for msg in messages_for_api:
                    role, content = msg['role'], msg['content']
                    
                    if role == "user":
                        st.markdown(f'<div class="chat-message user-message"><div class="message-label">Você</div>{content}</div>', unsafe_allow_html=True)
                    else:
                        # role == 'assistant' ou 'model'
                        formatted_content = format_message_with_code(content)
                        st.markdown(f'<div class="chat-message assistant-message"><div class="message-label">🤖 PrimeBud</div>{formatted_content}</div>', unsafe_allow_html=True)
            
            # Input de Mensagem
            with st.form(key="message_form", clear_on_submit=True):
                user_input = st.text_area(
                    "Mensagem",
                    key="user_input",
                    placeholder="Digite sua mensagem... (Ctrl+Enter para enviar)",
                    label_visibility="collapsed"
                )
                
                submitted = st.form_submit_button("📤 Enviar", use_container_width=True)
                
                if submitted and user_input.strip():
                    # Salva a mensagem do usuário
                    if st.session_state.user.get('is_guest'):
                        if st.session_state.current_chat_id not in st.session_state.guest_messages:
                            st.session_state.guest_messages[st.session_state.current_chat_id] = []
                        st.session_state.guest_messages[st.session_state.current_chat_id].append({
                            'role': 'user', 'content': user_input
                        })
                        messages_for_api = st.session_state.guest_messages[st.session_state.current_chat_id]
                    else:
                        save_message(st.session_state.current_chat_id, "user", user_input)
                        db_messages = get_chat_messages(st.session_state.current_chat_id)
                        messages_for_api = [{"role": m[0], "content": m[1]} for m in db_messages]

                    # Chama o roteador de API (ATUALIZADO)
                    with st.spinner("🤔 Processando..."):
                        response_text, response_role = generate_chat_response(messages_for_api, current_mode)
                    
                    # Salva a resposta (convidado ou usuário)
                    if st.session_state.user.get('is_guest'):
                        st.session_state.guest_messages[st.session_state.current_chat_id].append({
                            'role': response_role, 'content': response_text
                        })
                    else:
                        save_message(st.session_state.current_chat_id, response_role, response_text)
                    
                    st.rerun()
