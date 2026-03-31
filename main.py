import os
from real_data_downloader import baixar_dados_sgs
from focus_downloader import atualizar_dados_api
from chart_visuals import carregar_dados, plotar_trajetorias
from settings.settings import load_config



config = load_config()



PROJ_DIR = config['caminho_rede']
DATA_INICIO = '2010-01-01'
ARQUIVO_FOCUS = "dados_focus.csv"
ARQUIVO_SGS = "dados_sgs.csv"


if __name__ == "__main__":
    print("Iniciando download dos dados do SGS...")
    baixar_dados_sgs(proj_dir = PROJ_DIR, data_inicio=DATA_INICIO, arquivo=ARQUIVO_SGS)
    
    print("\nIniciando download dos dados do Focus...")
    atualizar_dados_api(proj_dir = PROJ_DIR, data_inicio=DATA_INICIO, arquivo=ARQUIVO_FOCUS)

    print("\nCarregando dados para visualização...")
    df_f, df_s = carregar_dados(proj_dir = PROJ_DIR, arquivo_focus=ARQUIVO_FOCUS, arquivo_sgs=ARQUIVO_SGS)

    print("\nGerando gráficos de trajetórias...")
    indicadores = df_s['indicador'].unique()
    for ind in indicadores:
        plotar_trajetorias(ind, df_f, df_s, data_inicio=DATA_INICIO)


