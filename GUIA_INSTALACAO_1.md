# Como rodar o "Onde é o Rolê?" na sua máquina

Guia passo a passo para clonar e executar o projeto a partir do GitHub.

## 1. Pré-requisitos

Antes de começar, instale:

- **Python 3.10 ou mais recente** — baixe em [python.org/downloads](https://www.python.org/downloads/). Durante a instalação no Windows, marque a opção "Add Python to PATH".
- **Git** — baixe em [git-scm.com](https://git-scm.com/downloads).
- Um editor de código (opcional, mas recomendado): [VS Code](https://code.visualstudio.com/).

Pra confirmar que tudo foi instalado certo, abra um terminal (PowerShell, Git Bash, ou o terminal do VS Code) e rode:

```bash
python --version
git --version
```

Ambos devem mostrar um número de versão, sem erro.

## 2. Clonar o repositório

No terminal, navegue até a pasta onde você quer salvar o projeto e rode:

```bash
git clone https://github.com/qnada0/urban-intelligence-recife-Onde-o-Rol-.git
cd urban-intelligence-recife-Onde-o-Rol-
```

(Se o nome da pasta vier diferente, ajuste o `cd` de acordo.)

## 3. Criar um ambiente virtual (recomendado)

Isso evita conflito entre as bibliotecas desse projeto e outras que você já tenha instaladas.

```bash
python -m venv venv
```

Ativar o ambiente:

- **Windows (PowerShell):** `venv\Scripts\Activate.ps1`
- **Windows (Git Bash):** `source venv/Scripts/activate`
- **Mac/Linux:** `source venv/bin/activate`

Você vai saber que funcionou porque o prompt do terminal passa a mostrar `(venv)` no início da linha. Repita esse passo de ativação toda vez que abrir um terminal novo pra trabalhar no projeto.

## 4. Instalar as dependências

Com o ambiente virtual ativado:

```bash
pip install -r requirements.txt
```

Isso instala Streamlit, FastAPI, Pandas, Plotly, scikit-learn e todo o resto que o projeto precisa. Pode demorar alguns minutos.

## 5. Configurar as variáveis de ambiente

O projeto precisa de algumas chaves e credenciais que **não estão no GitHub** por segurança (banco de dados e APIs).

1. Copie o arquivo `.env.example` e renomeie a cópia para `.env` (sem o ".example" no final).
2. Peça pro Rafael te mandar os valores reais de `DATABASE_URL`, `GOOGLE_MAPS_API_KEY` e `WEATHER_API_KEY` **por uma via segura** (WhatsApp, e-mail — nunca pelo GitHub).
3. Cole esses valores no `.env`, ficando assim (com os valores reais no lugar):

```
DATABASE_URL=postgresql://usuario:senha@host:5432/postgres
GOOGLE_MAPS_API_KEY=AIzaSy...
WEATHER_API_KEY=abc123...
```

## 6. Rodar o projeto

O projeto tem duas partes que precisam rodar **ao mesmo tempo**, cada uma no seu próprio terminal (com o ambiente virtual ativado nos dois).

**Terminal 1 — Backend (API de recomendações):**

```bash
uvicorn app.main:app --reload
```

Deve aparecer `Uvicorn running on http://127.0.0.1:8000` sem erros.

**Terminal 2 — Frontend (dashboard):**

```bash
streamlit run dashboard_app.py
```

Isso deve abrir automaticamente uma aba no navegador em `http://localhost:8501` com o dashboard funcionando. Se não abrir sozinho, copie esse endereço e cole no navegador manualmente.

## Problemas comuns

**"Could not import module main"** — você está rodando o comando da pasta errada, ou esqueceu o caminho completo. Use sempre `uvicorn app.main:app --reload` (com o `app.` na frente) a partir da pasta raiz do projeto, nunca de dentro da pasta `app/`.

**"FastAPI offline" na página de Recomendações** — o backend (Terminal 1) não está rodando. Confirme que os dois terminais estão abertos ao mesmo tempo.

**Erro ao instalar `psycopg2`** — isso não deve acontecer já que o `requirements.txt` usa `psycopg2-binary`, que já vem pré-compilado. Se mesmo assim der erro, confirme que está com Python 3.10+ instalado.

**Porta já em uso** — se aparecer erro de porta ocupada (8501 ou 8000), feche outros terminais que possam estar rodando o projeto, ou reinicie o computador.

**"ModuleNotFoundError"** — alguma biblioteca não foi instalada. Confirme que o ambiente virtual está ativado (deve aparecer `(venv)` no terminal) e rode `pip install -r requirements.txt` de novo.
