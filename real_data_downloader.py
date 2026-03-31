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
    caminho_arquivo = os.path.join(proj_dir, 'data', arquivo)
    
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
        
        # Identifica a última data baixada para este indicador específico
        df_ind = df_final[df_final['indicador'] == nome]
        if not df_ind.empty:
            # Continua a partir do dia seguinte ao último salvo
            data_inicio = df_ind['data'].max() + pd.Timedelta(days=1)
        else:
            data_inicio = pd.to_datetime(data_inicio)

        atual = pd.to_datetime(data_inicio)

        while atual <= fim_global:
            # Lotes de 2 anos para evitar o ReadTimeout
            proximo = atual + pd.DateOffset(years=2)
            
            str_atual = atual.strftime('%Y-%m-%d')
            str_proximo = min(proximo, fim_global).strftime('%Y-%m-%d')
            
            if str_atual > str_proximo:
                break

            print(f"Baixando período: {str_atual} a {str_proximo}...", end=" ")
            
            try:
                # Requisição à API
                df_lote = sgs.get({codigo: codigo}, start=str_atual, end=str_proximo)
                
                if not df_lote.empty:
                    # Padroniza para o último dia do mês para bater com o Focus
                    df_lote = df_lote.resample('ME').last().ffill().dropna().reset_index()
                    df_lote = df_lote.rename(columns={'Date': 'data', codigo: 'valor'})
                    df_lote['indicador'] = nome
                    
                    # Adiciona ao dataframe principal e remove duplicatas residuais
                    df_final = pd.concat([df_final, df_lote], ignore_index=True)
                    df_final = df_final.drop_duplicates(subset=['data', 'indicador'], keep='last')
                    
                    # Salva no disco IMEDIATAMENTE após o sucesso do lote
                    df_final.to_csv(caminho_arquivo, index=False)
                    print(f"OK. Salvo no CSV.")
                else:
                    print("Vazio.")

            except Exception as e:
                print(f"\n[ERRO] Falha ao baixar o período {str_atual} - {str_proximo}: {e}")
                print("Interrompendo este indicador para evitar loop de erros. Tente rodar novamente mais tarde.")
                break # Pula para o próximo indicador se o servidor recusar a conexão

            atual = proximo + pd.Timedelta(days=1)
            
            # Pausa de 3 segundos entre as requisições para evitar rate limit / timeout
            time.sleep(3)

if __name__ == "__main__":
    baixar_dados_sgs(proj_dir = os.getcwd(), data_inicio='2010-01-01')