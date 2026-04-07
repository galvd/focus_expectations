import os
from pyfiles.real_data_downloader import baixar_dados_sgs
from pyfiles.focus_downloader import atualizar_dados_api
from pyfiles.chart_visuals import carregar_dados, plotar_trajetorias
from pyfiles.dashboard_generator import gerar_dashboard_interativo
from settings.settings import load_config
from pyfiles.update_panels import atualizar_paineis

# Carregamento de configurações
config = load_config()

# Definições de caminhos e parâmetros
PROJ_DIR = config['caminho_rede']
DATA_INICIO = '2010-01-01'
ARQUIVO_FOCUS = "dados_focus.csv"
ARQUIVO_SGS = "dados_sgs.csv"

if __name__ == "__main__":
    # Resolução de caminhos completos para os arquivos de dados
    caminho_focus = os.path.join(PROJ_DIR, 'data', ARQUIVO_FOCUS)
    caminho_sgs = os.path.join(PROJ_DIR, 'data', ARQUIVO_SGS)

    print("--- ETAPA 1: Download de Dados Reais (SGS) ---")
    baixar_dados_sgs(proj_dir=PROJ_DIR, data_inicio=DATA_INICIO, arquivo=ARQUIVO_SGS)
    
    print("\n--- ETAPA 2: Download de Expectativas (Focus) ---")
    atualizar_dados_api(proj_dir=PROJ_DIR, data_inicio=DATA_INICIO, arquivo=ARQUIVO_FOCUS)

    print("\n--- ETAPA 3: Processamento e Carga ---")
    df_f, df_s = carregar_dados(proj_dir=PROJ_DIR, arquivo_focus=ARQUIVO_FOCUS, arquivo_sgs=ARQUIVO_SGS)

    print("\n--- ETAPA 4: Geração de Gráficos Estáticos (PNG) ---")
    indicadores = df_s['indicador'].unique()
    for ind in indicadores:
        plotar_trajetorias(ind, df_f, df_s, data_inicio=DATA_INICIO)

    print("\n--- ETAPA 5: Geração de Dashboard Interativo (HTML) ---")
    # Chama o gerador Plotly garantindo que os caminhos dos CSVs existam
    if os.path.exists(caminho_focus) and os.path.exists(caminho_sgs):
        gerar_dashboard_interativo(
            arquivo_focus=caminho_focus,
            arquivo_sgs=caminho_sgs,
            data_inicio=DATA_INICIO
        )
    else:
        print("Erro: Arquivos de dados não encontrados para a geração do dashboard.")

    print("\n--- ETAPA 6: Atualização dos Painéis HTML/MD ---")
    atualizar_paineis()
    
    print("\nPipeline finalizado com sucesso.")