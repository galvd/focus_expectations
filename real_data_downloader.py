import os
import time
import pandas as pd
from bcb import sgs
from settings.settings import load_config

config = load_config()

# Os nomes aqui DEVEM ser idênticos aos definidos no focus_downloader.py
MAPA_SGS = {
    'IPCA (%)': 13522,
    'Selic (% a.a)': 432,
    'Taxa de Câmbio (R$/US$)': 1,
    'PIB Acum. 4tri (%)': 22109
}

def baixar_dados_sgs(proj_dir, data_inicio, arquivo):
    caminho_arquivo = os.path.join(proj_dir, 'data', arquivo)
    
    if os.path.exists(caminho_arquivo):
        df_final = pd.read_csv(caminho_arquivo)
        df_final['data'] = pd.to_datetime(df_final['data'], format='mixed')
    else:
        df_final = pd.DataFrame(columns=['data', 'indicador', 'valor'])

    fim_global = pd.to_datetime('today')

    for nome, codigo in MAPA_SGS.items():
        print(f"\n--- Processando {nome} (Código: {codigo}) ---")
        
        # PIB precisa da base de 2009 para calcular a variação de 2010
        data_busca = '2009-01-01' if nome == 'PIB Acum. 4tri (%)' else data_inicio
        
        atual = pd.to_datetime(data_busca)
        df_ind_all = pd.DataFrame()

        # Restauração da lógica de lotes (Chunking) para evitar timeout em séries diárias
        while atual <= fim_global:
            proximo = atual + pd.DateOffset(years=3)
            str_atual = atual.strftime('%Y-%m-%d')
            str_proximo = min(proximo, fim_global).strftime('%Y-%m-%d')
            
            if str_atual > str_proximo:
                break
            
            try:
                df_lote = sgs.get({codigo: codigo}, start=str_atual, end=str_proximo)
                if not df_lote.empty:
                    df_ind_all = pd.concat([df_ind_all, df_lote])
            except Exception as e:
                print(f"[ERRO] Falha ao baixar o período {str_atual} - {str_proximo} para {nome}: {e}")
                break # Sai do loop deste indicador se a API travar
            
            atual = proximo + pd.Timedelta(days=1)
            time.sleep(0.5)

        if not df_ind_all.empty:
            df_ind_all = df_ind_all[~df_ind_all.index.duplicated(keep='first')]
            
            # --- Lógica Específica do PIB ---
            if nome == 'PIB Acum. 4tri (%)':
                df_ind_all['Year'] = df_ind_all.index.year
                mean_2010 = df_ind_all[df_ind_all['Year'] == 2010][codigo].mean()
                mean_2009_sintetico = mean_2010 / 1.0753
                df_ind_all.loc[df_ind_all['Year'] == 2009, codigo] = mean_2009_sintetico
                
                soma_4_tri = df_ind_all[codigo].rolling(window=4).sum()
                df_ind_all['valor_calculado'] = ((soma_4_tri / soma_4_tri.shift(4)) - 1) * 100
            else:
                df_ind_all['valor_calculado'] = df_ind_all[codigo]

            # --- Tratamento de Frequência e Interpolação ---
            df_ind_all = df_ind_all.resample('ME').last()
            df_ind_all = df_ind_all.interpolate(method='linear').dropna().reset_index()
            
            df_ind_all = df_ind_all.rename(columns={'Date': 'data', 'valor_calculado': 'valor'})
            df_ind_all['indicador'] = nome
            
            # Filtro para remover o ano sintético de 2009 e garantir ponto de partida exato
            df_ind_all = df_ind_all[df_ind_all['data'] >= pd.to_datetime(data_inicio)]
            df_ind_all = df_ind_all[['data', 'indicador', 'valor']]
            
            # --- Atualização do CSV ---
            df_final = df_final[df_final['indicador'] != nome].copy()
            df_final = pd.concat([df_final, df_ind_all], ignore_index=True)
            
            os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
            df_final.to_csv(caminho_arquivo, index=False)
            print(f"Sucesso: {nome} atualizado.")
        else:
            print(f"Aviso: SGS retornou dados vazios para {nome}.")

        time.sleep(2)

if __name__ == "__main__":
    baixar_dados_sgs(proj_dir=os.getcwd(), data_inicio='2010-01-01', arquivo='dados_sgs.csv')