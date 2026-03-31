import pandas as pd
import os
from bcb import Expectativas
from datetime import datetime
from settings.settings import load_config


config = load_config()




def atualizar_dados_api(proj_dir, data_inicio, arquivo):
    caminho_arquivo = os.path.join(proj_dir, 'data', arquivo)
    df_existente = pd.DataFrame()

    if os.path.exists(caminho_arquivo):
        df_existente = pd.read_csv(caminho_arquivo)
        if not df_existente.empty:
            df_existente['data_boletim'] = pd.to_datetime(df_existente['data_boletim'], format='mixed')
            data_ultima_atualizacao = df_existente['data_boletim'].max()
            data_max_existente = data_ultima_atualizacao.strftime('%Y-%m-%d')
            
            dias_decorridos = (datetime.now() - data_ultima_atualizacao).days
            
            if dias_decorridos < 7:
                print(f"Último dado é de {data_max_existente} ({dias_decorridos} dias). Atualização da API pulada.")
                return
            
            # Formata estritamente para a query do OData
            data_inicio = data_ultima_atualizacao.strftime('%Y-%m-%d')
            print(f"Atualizando base existente a partir de {data_inicio}.")
    else:
        # Garante a formatação caso venha do argumento default
        data_inicio = pd.to_datetime(data_inicio).strftime('%Y-%m-%d')
        print(f"Criando nova base a partir de {data_inicio}.")

    em = Expectativas()
    ep = em.get_endpoint('ExpectativasMercadoAnuais')
    
    indicadores = ['IPCA', 'PIB Total', 'Câmbio', 'Selic', 'IGP-M']

    print("Coletando dados via python-bcb...")
    
    try:
        df_raw = (ep.query()
                  .filter(ep.Data >= data_inicio)
                  .filter(ep.baseCalculo == 0)
                  .select(ep.Data, ep.Indicador, ep.DataReferencia, ep.Mediana, ep.numeroRespondentes)
                  .collect())
    except json.decoder.JSONDecodeError:
        print("Erro: A API do Banco Central retornou uma resposta inválida (provável instabilidade do servidor ou timeout).")
        return
    except Exception as e:
        print(f"Erro inesperado na conexão com a API: {e}")
        return

    if df_raw.empty:
        print("Nenhum dado novo retornado.")
        return

    df_novos = df_raw[df_raw['Indicador'].isin(indicadores)].copy()
    
    if df_novos.empty:
        print("Nenhum dado novo para os indicadores selecionados.")
        return

    df_novos = df_novos.rename(columns={
        'Data': 'data_boletim',
        'Indicador': 'indicador',
        'DataReferencia': 'periodo_previsao',
        'Mediana': 'previsao',
        'numeroRespondentes': 'respondentes'
    })

    mapa_indicadores = {
        "IPCA": "IPCA (%)",
        "PIB Total": "PIB Total (%)",
        "Câmbio": "Câmbio (R$/US$)",
        "Selic": "Selic (% a.a)",
        "IGP-M": "IGP-M (%)"
    }
    
    df_novos['indicador'] = df_novos['indicador'].map(mapa_indicadores).fillna(df_novos['indicador'])
    df_novos['respondentes'] = df_novos['respondentes'].fillna(0).astype(int)

    if not df_existente.empty:
        df_final = pd.concat([df_existente, df_novos], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=['data_boletim', 'indicador', 'periodo_previsao'], keep='last')
    else:
        df_final = df_novos

    df_final = df_final.sort_values(by=['data_boletim', 'indicador', 'periodo_previsao'])
    df_final.to_csv(caminho_arquivo, index=False)
    
    print(f"Concluído. Tabela salva em: {caminho_arquivo} com {len(df_final)} registros.")