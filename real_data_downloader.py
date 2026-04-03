import os
import time
import pandas as pd
from bcb import sgs
from settings.settings import load_config



config = load_config()

MAPA_SGS = {
    'IPCA (%)': 13522,
    'Selic (% a.a)': 432,
    'Câmbio (R$/US$)': 1,
    'PIB Total (%)': 7328  # PIB - Taxa de variação acumulada em 4 trimestres (IBGE)
}

def baixar_dados_sgs(proj_dir, data_inicio, arquivo):
    caminho_arquivo = os.path.join(proj_dir, arquivo)
    
    # Carrega dados existentes para continuar de onde parou
    if os.path.exists(caminho_arquivo):
        df_final = pd.read_csv(caminho_arquivo)
        df_final['data'] = pd.to_datetime(df_final['data'])
        print(f"Arquivo existente encontrado. Registros atuais: {len(df_final)}")
    else:
        df_final = pd.DataFrame(columns=['data', 'indicador', 'valor'])
        print("Criando novo arquivo de base de dados.")

    fim_global = pd.to_datetime('today')

    for nome, codigo in MAPA_SGS.items():
        print(f"\n--- Processando {nome} (Código: {codigo}) ---")
        
        # Para evitar saltos (degraus) entre as fronteiras dos lotes,
        # a série é baixada inteira e interpolada como um único bloco.
        atual = pd.to_datetime(data_inicio)
        df_ind_all = pd.DataFrame()

        while atual <= fim_global:
            proximo = atual + pd.DateOffset(years=3)
            str_atual = atual.strftime('%Y-%m-%d')
            str_proximo = min(proximo, fim_global).strftime('%Y-%m-%d')
            
            if str_atual > str_proximo:
                break

            print(f"Baixando período: {str_atual} a {str_proximo}...", end=" ")
            
            try:
                # Requisição à API
                df_lote = sgs.get({codigo: codigo}, start=str_atual, end=str_proximo)
                if not df_lote.empty:
                    df_ind_all = pd.concat([df_ind_all, df_lote])
                    print("OK.")
                else:
                    print("Vazio.")

            except Exception as e:
                print(f"\n[ERRO] Falha ao baixar o período {str_atual} - {str_proximo}: {e}")
                break

            atual = proximo + pd.Timedelta(days=1)
            time.sleep(1)
            
        if not df_ind_all.empty:
            df_ind_all = df_ind_all[~df_ind_all.index.duplicated(keep='first')]
            
            # Reduz a frequência para o último dia do mês
            df_ind_all = df_ind_all.resample('ME').last()
            
            # Interpolação linear transforma os dados trimestrais do PIB em curvas contínuas
            df_ind_all = df_ind_all.interpolate(method='linear').dropna().reset_index()
            
            df_ind_all = df_ind_all.rename(columns={'Date': 'data', codigo: 'valor'})
            df_ind_all['indicador'] = nome
            
            # Atualiza o arquivo final de forma limpa, substituindo todo o indicador
            df_final = df_final[df_final['indicador'] != nome]
            df_final = pd.concat([df_final, df_ind_all], ignore_index=True)
            
            df_final.to_csv(caminho_arquivo, index=False)

if __name__ == "__main__":
    baixar_dados_sgs(proj_dir=os.getcwd(), data_inicio='2010-01-01', arquivo='dados_sgs.csv')