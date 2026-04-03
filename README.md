# Focus: Trajetórias de Expectativas de Mercado vs. Realizado

Este projeto automatiza a coleta, o processamento e a visualização de dados econômicos brasileiros. Ele confronta as expectativas anuais do **Boletim Focus** (Banco Central do Brasil) com os dados reais extraídos do **SGS (Sistema Gerenciador de Séries Temporais)**, gerando gráficos de trajetórias ("fan charts") que permitem visualizar a evolução das previsões ao longo do tempo. 

## Estrutura do Projeto

O projeto é orquestrado pelo arquivo `main.py` e está dividido em módulos de responsabilidade única: 

  * **`main.py`**: O orquestrador central. Define as constantes de diretório, períodos de início e gerencia a sequência de execução (SGS -\> Focus -\> Visualização). 
  * `focus_downloader.py`**: Gerencia a coleta das expectativas anuais via API OData (`python-bcb`). 
      * Implementa uma trava de segurança que verifica a última data disponível; se o dado local tiver menos de 7 dias, a atualização é pulada para otimizar a performance. 
  * `real_data_downloader.py`**: Extrai os dados reais históricos do SGS. 
      * Trabalha com download em lotes de 2 anos para evitar *timeouts* da API e implementa pausas (`sleep`) entre requisições. 
  * `chart_visuals.py`**: Responsável pela lógica de renderização gráfica utilizando `matplotlib`. 

## Requisitos Técnicos

  * **Linguagem**: Python 3.12+
  * **Bibliotecas Principais**:
      * `pandas`: Manipulação e estruturação de dados *Tidy*. 
      * `python-bcb`: Interface de conexão com as APIs do Banco Central. 
      * `matplotlib`: Geração de gráficos. 

## Indicadores Monitorados

O sistema monitora e gera trajetórias para os seguintes indicadores: 

| Indicador | Código SGS (Real) | Unidade |
| :--- | :--- | :--- |
| **IPCA** | 13522 | Variação acumulada em 12 meses (%) |
| **PIB (Acum. 4tri)** | 22109 | Acumulado em 4 trimestres (ajustado no código) |
| **Selic** | 432 | Taxa Meta definida pelo Copom (% a.a.) |
| **Câmbio** | 1 | Taxa de câmbio Livre - Venda (R$/US$) |

## Metodologia do PIB
Para garantir a comparabilidade com as expectativas de mercado, o **PIB Total (%)** é processado a partir da série de índice de volume (SGS 22109). 
* **Cálculo**: Variação acumulada de 4 trimestres.
* **Ancoragem**: Série ancorada em 2009 para refletir o crescimento real de **7,53%** em 2010.
* **Suavização**: Interpolação linear mensal para eliminar o efeito de "escada" dos dados trimestrais.

## Lógica de Visualização

Os gráficos são salvos automaticamente na pasta `/charts`.  A visualização utiliza um sistema de cores dinâmico para representar o horizonte das expectativas: 

  * Linha Azul**: Representa o **Dado Real** extraído do SGS. 
  * Linha Cinza Escuro**: Expectativas feitas para o **Ano Corrente** (horizonte $\leq 0$). 
  * Linha Cinza Médio**: Expectativas feitas para **1 Ano à Frente** (horizonte $= 1$). 
  * Linha Cinza Claro**: Expectativas feitas para **2 ou mais anos à Frente** (horizonte $\geq 2$). 


## Configuração

O projeto depende de um arquivo `config.json` na raiz, que deve apontar para o caminho de rede ou diretório de trabalho conforme configurado no sistema local. 

```json
{
    "caminho_rede": "C:/Caminho/Para/Seu/Projeto" # ou caminho similar 
}
```

## Como Executar

Basta rodar o comando principal no terminal:

```bash
python main.py
```

O orquestrador cuidará de verificar atualizações pendentes, baixar novos dados se necessário e atualizar todos os arquivos de imagem na pasta `/charts`. 