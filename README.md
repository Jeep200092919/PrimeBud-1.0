# PrimeBud 2.0 - Streamlit Edition

Versão Streamlit do PrimeBud 2.0 com todas as funcionalidades modernas.

## 🚀 Características

- ✅ **7 Modos de Resposta** - Flash, Standard, Light, Pro, Ultra, Helper e v1.5
- ✅ **Múltiplos Chats** - Crie e gerencie várias conversas
- ✅ **Autenticação** - Sistema de login e cadastro seguro
- ✅ **Persistência** - Banco de dados SQLite para salvar histórico
- ✅ **Interface Moderna** - Design dark com cores laranja
- ✅ **Integração Groq** - Powered by GPT-OSS 120B (llama-3.3-70b-versatile)

## 📋 Pré-requisitos

- Python 3.8+
- Conta Groq com API Key (gratuita em https://console.groq.com/)

## 🔧 Instalação

1. **Clone ou baixe os arquivos**
```bash
cd primebud_streamlit
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure a API Key do Groq**

**Opção 1: Variável de ambiente (Recomendado)**
```bash
export GROQ_API_KEY="sua_chave_aqui"
```

**Opção 2: Arquivo .streamlit/secrets.toml**
```bash
mkdir .streamlit
echo 'GROQ_API_KEY = "sua_chave_aqui"' > .streamlit/secrets.toml
```

**Opção 3: Diretamente no código**
Edite o arquivo `app.py` e adicione sua chave na linha onde está `os.getenv("GROQ_API_KEY")`

4. **Execute o aplicativo**
```bash
streamlit run app.py
```

O aplicativo abrirá automaticamente no seu navegador em `http://localhost:8501`

## 🎯 Como Usar

### Primeiro Acesso

1. **Crie uma conta**
   - Clique na aba "Cadastro"
   - Escolha um nome de usuário e senha (mínimo 6 caracteres)
   - Clique em "Cadastrar"

2. **Faça login**
   - Use suas credenciais na aba "Login"
   - Clique em "Entrar"

### Usando o Chat

1. **Crie um novo chat**
   - Clique no botão "➕ Novo Chat" na barra lateral
   - Um novo chat será criado automaticamente

2. **Escolha o modo de resposta**
   - Use o seletor no topo da página
   - Experimente diferentes modos para diferentes necessidades:
     - 🚀 **Flash**: Respostas rápidas (500 tokens)
     - ⚡ **Standard**: Balanceado (1500 tokens)
     - 💡 **Light**: Explicações simples (1000 tokens)
     - 🎯 **Pro**: Técnico e detalhado (2500 tokens)
     - 🔥 **Ultra**: Análise profunda (4000 tokens)
     - 🤝 **Helper**: Amigável e empático (2000 tokens)
     - ⭐ **v1.5**: Híbrido recomendado (3000 tokens)

3. **Converse**
   - Digite sua mensagem na caixa de texto
   - Clique em "📤 Enviar"
   - Aguarde a resposta da IA

4. **Gerencie seus chats**
   - Alterne entre chats clicando neles na barra lateral
   - Delete chats com o botão 🗑️
   - Limpe o histórico com "🗑️ Limpar Chat"

## 🗄️ Banco de Dados

O aplicativo usa SQLite para armazenar:
- **Usuários**: Credenciais e informações de conta
- **Chats**: Conversas criadas por cada usuário
- **Mensagens**: Histórico completo de cada conversa

O arquivo `primebud.db` é criado automaticamente na primeira execução.

## 🔒 Segurança

- Senhas são criptografadas com SHA-256
- Cada usuário só acessa seus próprios chats
- Banco de dados local (não compartilhado)

## 🌐 Deploy no Streamlit Cloud

1. **Faça upload do código para GitHub**
```bash
git init
git add .
git commit -m "PrimeBud 2.0 Streamlit"
git remote add origin seu_repositorio
git push -u origin main
```

2. **Configure no Streamlit Cloud**
   - Acesse https://share.streamlit.io/
   - Conecte seu repositório GitHub
   - Adicione a secret `GROQ_API_KEY` nas configurações
   - Deploy!

## 📝 Notas

- A API do Groq tem limite de requisições no plano gratuito
- O banco de dados SQLite é adequado para uso pessoal/pequeno
- Para produção em larga escala, considere PostgreSQL ou MySQL

## 🆘 Solução de Problemas

### Erro: "GROQ_API_KEY não configurada"
- Certifique-se de ter configurado a variável de ambiente
- Verifique se a chave está correta

### Erro: "Cannot connect to database"
- Verifique permissões de escrita no diretório
- Delete o arquivo `primebud.db` e tente novamente

### Interface não carrega corretamente
- Limpe o cache do navegador
- Reinicie o Streamlit com `Ctrl+C` e execute novamente

## 📄 Licença

Este projeto é de código aberto e pode ser usado livremente.

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Enviar pull requests

---

**PrimeBud 2.0** - Desenvolvido com ❤️ usando Streamlit e Groq API

