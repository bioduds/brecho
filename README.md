# 🛍️ Brechó Local - Sistema de Gestão

Sistema completo para gestão de brechó desenvolvido com base na conversa sobre as necessidades reais do negócio.

## ✨ Principais Funcionalidades

### 📊 **Dashboard Avançado**

- **KPIs em tempo real**: Estoque atual, vendas do período, taxa de rotação, dias médios para venda
- **Análise ABC**: Identifica categorias que geram mais receita (classes A, B, C)
- **Matriz Categoria × Tamanho**: Heatmap mostrando taxa de venda por combinação
- **Análise de Descontos**: Performance por etapa de desconto
- **Top Performers**: Melhores consignantes e itens de rotação rápida
- **Recomendações Automáticas**: Sugestões baseadas em dados

### 🤖 **Automação Inteligente**

- **Atualização automática de descontos** baseada em tempo:
  - 0-30 dias: Preço cheio
  - 31-60 dias: -10%
  - 61-90 dias: -25%
  - 90+ dias: -40%
- **Identificação de itens parados** (candidatos a bundle/doação)
- **Análise de performance dos consignantes**
- **Sugestões de aquisição** (categorias/tamanhos com alta demanda)
- **Backup automático** do banco de dados

### 📸 **Gestão de Fotos**

- **Upload múltiplo** de fotos por item (até 5 fotos)
- **Redimensionamento automático** para redes sociais (1080px)
- **Galeria organizada** com filtros por categoria/marca
- **Estatísticas de cobertura** - identifica itens sem fotos
- **Listas de prioridade** para fotografia (itens novos, alto valor, etc.)

### 🏷️ **Sistema de Etiquetas Profissional**

- **Múltiplos formatos**: 58x40mm (térmica), 70x50mm, 90x60mm, A4
- **QR Codes automáticos** para cada SKU
- **Layout inteligente**: Preço atual, preço original riscado quando em desconto
- **Impressão em lote**: A4 com múltiplas etiquetas (2x4 ou 3x6)
- **Templates personalizáveis** com informações da loja

### 💾 **Gestão de Dados Robusta**

- **Formulários inteligentes**: Preservam dados quando há erro de validação
- **Base SQLite local**: Sem dependência de internet
- **Backup e restauração** simples
- **Validação de dados** consistente
- **Histórico completo** de todas as operações

## 🔄 **Fluxo de Trabalho Otimizado**

### 📦 **Entrada de Mercadoria**

1. **Cadastrar Consignante** (se novo)
2. **Fotografar itens** (3 ângulos: frontal, lateral, defeito)
3. **Cadastrar Item** com medidas e condição
4. **Gerar etiqueta** com QR code e preço
5. **Posicionar no estoque** por categoria/tamanho

### 🏪 **Operação Diária**

1. **Verificar dashboard** para KPIs do dia
2. **Executar automação** de descontos (1 clique)
3. **Registrar vendas** com leitura de QR
4. **Atualizar fotos** de novos itens
5. **Gerar etiquetas** de reposição conforme necessário

### 📈 **Gestão Estratégica**

1. **Análise ABC semanal** - focar aquisição em categorias A
2. **Review de consignantes** - performance individual
3. **Limpeza de estoque** - bundles para itens >90 dias
4. **Planejamento de compras** baseado em dados de rotação

## 🛠️ **Instalação e Uso**

### Pré-requisitos

- Python 3.8+
- 2GB de espaço em disco

### Instalação

```bash
# Clone o projeto
git clone [repositório]
cd brecho_local_app

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# ou
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run app.py
```

### Acesso

- Local: <http://localhost:8501>
- Rede: http://[IP_DA_MÁQUINA]:8501

## 📋 **Páginas do Sistema**

1. **🏠 Home** - Visão geral e navegação rápida
2. **👥 Consignantes** - Cadastro e gestão de parceiros
3. **📦 Itens** - Inventário completo com política de descontos
4. **💰 Vendas** - Registro de transações
5. **💸 Repasses** - Cálculo automático de comissões
6. **🎯 QR & Recibo** - Geração de documentos
7. **📊 Dashboard** - KPIs e análises avançadas
8. **🤖 Automação** - Rotinas automatizadas
9. **📸 Fotos** - Gestão de imagens
10. **🏷️ Etiquetas** - Sistema de impressão

## 💡 **Diferenciais Competitivos**

### 📊 **Decision Making Baseado em Dados**

- **Matriz de rotatividade**: Identifica exatamente quais categorias/tamanhos comprar
- **Performance de consignantes**: Dados objetivos para negotiations
- **Previsão de demanda**: Baseada em histórico de vendas
- **ROI por categoria**: Maximiza retorno sobre investimento

### ⚡ **Eficiência Operacional**

- **1 clique para atualizações**: Descontos automáticos por tempo
- **QR codes integrados**: Reduz tempo de venda e evita erros
- **Templates de fotos**: Padronização para redes sociais
- **Backup automático**: Segurança dos dados

### 🎯 **Foco no Negócio**

- **Política de descontos clara**: Evita acúmulo de estoque
- **Identificação de slow movers**: Ação proativa em itens parados
- **Análise de consignantes**: Foco nos parceiros mais produtivos
- **Otimização de espaço**: Dados para allocation por categoria

## 🔮 **Roadmap Futuro**

### 🌐 **Integrações**

- [ ] WhatsApp Business API para notificações
- [ ] Instagram Shopping integration
- [ ] Shopee/Enjoei sync automático
- [ ] Sistema de pagamento (PicPay, Pix)

### 🤖 **IA e Automação**

- [ ] Classificação automática de fotos (categoria, cor, defeitos)
- [ ] Precificação inteligente baseada em market data
- [ ] Chatbot para atendimento via WhatsApp
- [ ] Recomendação de combos para clientes

### 📱 **Mobile**

- [ ] App nativo para operação no celular
- [ ] Scanner de código de barras
- [ ] Catálogo mobile para clientes
- [ ] Gestão de consignação via app

## 📞 **Suporte**

Este sistema foi desenvolvido especificamente para brechós brasileiros, com foco em:

- **Simplicidade operacional**
- **Dados acionáveis**
- **Compliance local**
- **Escalabilidade controlada**

Para dúvidas técnicas ou melhorias, consulte a documentação ou entre em contato.

---
*Desenvolvido com ❤️ para o ecossistema de moda circular no Brasil*
