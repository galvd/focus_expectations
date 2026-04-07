import os
import time
import pandas as pd
from bcb import sgs
from settings.settings import load_config

config = load_config()

MAPA_SGS = {
    'IPCA (%)': 13522,
    'Selic (% a.a)': 432,
    'Taxa de Câmbio (R$/US$)': 1,
    'PIB Acum. 4tri (%)': 22109
}

def baixar_dados_sgs(proj_dir, data_inicio, arquivo):
    caminho_arquivo = os.path.join(proj_dir, 'data', arquivo)
    
    # 1. Carrega base existente se houver
    df_existente = pd.DataFrame()
    if os.path.exists(caminho_arquivo):
        df_existente = pd.read_csv(caminho_arquivo)
        df_existente['data'] = pd.to_datetime(df_existente['data'], format='mixed')
        df_final = df_existente.copy()
    else:
        df_final = pd.DataFrame(columns=['data', 'indicador', 'valor'])

    fim_global = pd.to_datetime('today')

    for nome, codigo in MAPA_SGS.items():
        print(f"\n--- Processando {nome} (Código: {codigo}) ---")
        
        # 2. Definição Dinâmica da Data de Busca (Otimização)
        data_busca = data_inicio
        
        if nome == 'PIB Acum. 4tri (%)':
            # PIB precisa baixar desde 2009 para garantir o cálculo da janela móvel (rolling window)
            data_busca = '2009-01-01'
        elif not df_existente.empty and nome in df_existente['indicador'].values:
            # Encontra a última data registrada no CSV para este indicador
            ultima_data = df_existente[df_existente['indicador'] == nome]['data'].max()
            
            # Volta 2 meses para ter uma margem de segurança na interpolação e resample
            data_otimizada = ultima_data - pd.DateOffset(months=2)
            data_busca = data_otimizada.strftime('%Y-%m-%d')
            print(f"  -> Histórico identificado. Baixando apenas a atualização a partir de {data_busca}")
        else:
            print(f"  -> Primeira execução para o indicador. Baixando desde {data_busca}")

        atual = pd.to_datetime(data_busca)
        df_ind_all = pd.DataFrame()

        # 3. Lógica de Lotes com Sistema de "Retries"
        while atual <= fim_global:
            proximo = atual + pd.DateOffset(years=3)
            str_atual = atual.strftime('%Y-%m-%d')
            str_proximo = min(proximo, fim_global).strftime('%Y-%m-%d')
            
            if str_atual > str_proximo:
                break
                
            sucesso_lote = False
            
            # Tenta baixar o mesmo lote 3 vezes antes de pular
            for tentativa in range(1, 4):
                try:
                    df_lote = sgs.get({codigo: codigo}, start=str_atual, end=str_proximo)
                    if not df_lote.empty:
                        df_ind_all = pd.concat([df_ind_all, df_lote])
                    sucesso_lote = True
                    break  # Se deu certo, sai do loop de tentativas
                except Exception as e:
                    print(f"  [Aviso] Falha na tentativa {tentativa}/3 para {str_atual}-{str_proximo}. Aguardando 3s...")
                    time.sleep(3) 
            
            if not sucesso_lote:
                print(f"  [ERRO FATAL] API do BCB bloqueou o download de {str_atual} a {str_proximo}.")
                break 
            
            atual = proximo + pd.Timedelta(days=1)
            time.sleep(1)

        # 4. Processamento dos Dados
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
            
            # Garante filtro a partir de 2010-01-01 global
            df_ind_all = df_ind_all[df_ind_all['data'] >= pd.to_datetime(data_inicio)]
            df_ind_all = df_ind_all[['data', 'indicador', 'valor']]
            
            # --- Substituição e Merge Seguro na Base ---
            if not df_final.empty:
                # Remove os dados antigos deste indicador APENAS no trecho de tempo recém-baixado
                # Isso impede duplicações e preserva os dados históricos intocados
                condicao_remover = (df_final['indicador'] == nome) & (df_final['data'] >= pd.to_datetime(data_busca))
                df_final = df_final[~condicao_remover]
            
            # Anexa o trecho novo/atualizado ao histórico
            df_final = pd.concat([df_final, df_ind_all], ignore_index=True)
            print(f"  -> Sucesso: {nome} atualizado e integrado ao histórico.")
            
        else:
            print(f"  -> Aviso: SGS retornou dados totalmente vazios para {nome}.")

    # 5. Salva o CSV Consolidado
    if not df_final.empty:
        df_final = df_final.sort_values(by=['indicador', 'data'])
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        df_final.to_csv(caminho_arquivo, index=False)
        print(f"\n[SGS Downloader] Concluído. Tabela atualizada e salva em: {caminho_arquivo}")

if __name__ == "__main__":
    baixar_dados_sgs(proj_dir=os.getcwd(), data_inicio='2010-01-01', arquivo='dados_sgs.csv')