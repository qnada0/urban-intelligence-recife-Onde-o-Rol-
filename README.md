# 📊 Urban Intelligence – Análise de Restaurantes em Recife
![Python](https://img.shields.io/badge/Python-3.10-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![Status](https://img.shields.io/badge/status-ativo-success)

Projeto de análise de dados urbanos com foco na identificação de padrões entre preço, localização e avaliação de restaurantes na cidade do Recife.

---

## 🎯 Problema

A escolha de restaurantes em grandes centros urbanos é frequentemente baseada em tentativa e erro ou recomendações informais.  
Com múltiplas opções disponíveis, usuários enfrentam dificuldade em identificar locais com boa relação custo-benefício.

---

## 💡 Objetivo

Desenvolver uma análise de dados capaz de identificar padrões entre:

- 💰 Preço  
- 📍 Localização  
- ⭐ Avaliação  

Apoiando decisões mais inteligentes na escolha de restaurantes.

---

## 🧠 Metodologia – CRISP-DM

O projeto segue a metodologia CRISP-DM:

1. **Business Understanding**  
   Definição do problema

2. **Data Understanding**  
   Coleta via Google Places API

3. **Data Preparation**  
   Limpeza com Pandas

4. **Modeling**  
   Criação de métricas (custo-benefício)

5. **Evaluation**  
   Análise exploratória

6. **Deployment**  
   Dashboard com Streamlit

---

## 🏗️ Arquitetura do Projeto
Google Places API → Python → Pandas → CSV → Streamlit Dashboard


---

## 🛠️ Tecnologias Utilizadas

- Python  
- Pandas  
- Streamlit  
- Google Places API  
- Requests  
- Python-dotenv  

---

## ⚙️ Funcionalidades

- Dashboard interativo  
- Filtros por preço e avaliação  
- Mapa geográfico  
- Análise de distribuição  
- Score de custo-benefício
  
📷 Veja o funcionamento do sistema abaixo:
[Urban Intelligence Dashboard.pdf](https://github.com/user-attachments/files/26761126/Urban.Intelligence.Dashboard.pdf)
### 📊 Dashboard

![Dashboard](./assets/dashboard.png)

### 🗺️ Mapa Interativo

![Mapa](./assets/mapa.png)


---

## 📂 Estrutura do Projeto
```bash
urban-intelligence/
│
├── app/
├── data/
│ └── places_recife_real.csv
├── assets/ 
├── dashboard_app.py
├── fetch_places_new.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
...
```


---

## 🔑 Configuração da API

Crie um arquivo `.env`:

```env
GOOGLE_MAPS_API_KEY=SUA_CHAVE_AQUI
```

## ▶️ Como Executar o Projeto
```bash
# Clonar repositório
git clone https://github.com/seuusuario/seurepo.git

# Entrar na pasta
cd urban-intelligence

# Instalar dependências
pip install -r requirements.txt

# Rodar aplicação
streamlit run dashboard_app.py

1. Instalar dependências
```bash
pip install -r requirements.txt
```
```markdown
## 🧪 Exemplo de Uso

O usuário pode:

- Filtrar restaurantes por preço e avaliação
- Visualizar distribuição geográfica
- Identificar melhor custo-benefício
---
## 📚 Aprendizados

- Integração com APIs reais
- Limpeza e tratamento de dados
- Visualização com Streamlit
- Aplicação de CRISP-D
---

## 📊 Fluxo do Sistema
Coleta via API
Tratamento com Pandas
Geração do dataset
Visualização no dashboard
---
## ⚠️ Limitações
Dependência da API do Google
Avaliações subjetivas
Dados dinâmicos
Recorte geográfico limitado
---
## 📌 Principais Insights
Preço alto ≠ melhor avaliação
Melhor custo-benefício em preços intermediários
Localização não garante qualidade
Dados ajudam decisões mais eficientes
---

## 📈 Conclusão

O projeto demonstra como dados urbanos podem ser transformados em inteligência aplicada, auxiliando na tomada de decisão e melhorando a experiência do usuário.
