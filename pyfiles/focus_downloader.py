import pandas as pd
import os
import json
from bcb import Expectativas
from datetime import datetime
from settings.settings import load_config

config = load_config()

def atualizar_dados_api(proj_dir, data_inicio, arquivo):
    caminho_arquivo = os.path.join(proj_dir, 'data', arquivo)
    df_existente = pd.DataFrame()

    # 1. Verificação de base existente e trava de 7 dias
    if os.path.exists(caminho_arquivo):
        df_existente = pd.read_csv(caminho_arquivo)
        if not df_existente.empty:
            # Garante conversão cronológica antes de buscar o máximo
            df_existente['data_boletim'] = pd.to_datetime(df_existente['data_boletim'], format='mixed')
            data_ultima_atualizacao = df_existente['data_boletim'].max()
            
            dias_decorridos = (datetime.now() - data_ultima_atualizacao).days
            
            if dias_decorridos < 7:
                print(f"Último dado é de {data_ultima_atualizacao.strftime('%Y-%m-%d')} ({dias_decorridos} dias). Atualização pulada.")
                return
            
            # Define data de início para a API (YYYY-MM-DD)
            data_inicio = data_ultima_atualizacao.strftime('%Y-%m-%d')
            print(f"Atualizando base existente a partir de {data_inicio}.")
    else:
        data_inicio = pd.to_datetime(data_inicio).strftime('%Y-%m-%d')
        print(f"Criando nova base a partir de {data_inicio}.")

    # 2. Conexão com a API do BCB
    em = Expectativas()
    ep = em.get_endpoint('ExpectativasMercadoAnuais')
    
    indicadores_alvo = ['IPCA', 'PIB Total', 'Câmbio', 'Selic', 'IGP-M']

    print("Coletando dados via python-bcb...")
    
    try:
        # Query OData
        df_raw = (ep.query()
                  .filter(ep.Data >= data_inicio)
                  .filter(ep.baseCalculo == 0)
                  .select(ep.Data, ep.Indicador, ep.DataReferencia, ep.Mediana, ep.numeroRespondentes)
                  .collect())
    except Exception as e:
        # Captura JSONDecodeError (instabilidade BCB) ou erros de rede
        print(f"Erro na conexão com a API do Banco Central: {e}")
        return

    if df_raw.empty:
        print("Nenhum dado novo retornado pela API.")
        return

    # 3. Filtragem e Renomeação (Tidy Data)
    df_novos = df_raw[df_raw['Indicador'].isin(indicadores_alvo)].copy()
    
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

    # 4. Padronização de Nomes e Tipos
    mapa_indicadores = {
        "IPCA": "IPCA (%)",
        "PIB Total": "PIB Acum. 4tri (%)",  
        "Câmbio": "Taxa de Câmbio (R$/US$)",
        "Selic": "Selic (% a.a)",
        "IGP-M": "IGP-M (%)"
    }
    
    df_novos['indicador'] = df_novos['indicador'].map(mapa_indicadores).fillna(df_novos['indicador'])
    df_novos['respondentes'] = df_novos['respondentes'].fillna(0).astype(int)
    # Garante que a data do boletim seja salva como string simples YYYY-MM-DD
    df_novos['data_boletim'] = pd.to_datetime(df_novos['data_boletim']).dt.strftime('%Y-%m-%d')

    # 5. Consolidação e Exportação
    if not df_existente.empty:
        df_existente['data_boletim'] = df_existente['data_boletim'].dt.strftime('%Y-%m-%d')
        
        df_final = pd.concat([df_existente, df_novos], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=['data_boletim', 'indicador', 'periodo_previsao'], keep='last')
    else:
        df_final = df_novos

    df_final['data_boletim'] = pd.to_datetime(df_final['data_boletim'])
    df_final = df_final.sort_values(by=['data_boletim', 'indicador', 'periodo_previsao'])
    
    # Cria uma chave de Ano-Semana ISO
    df_final['ano_semana'] = df_final['data_boletim'].dt.isocalendar().year.astype(str) + '-' + df_final['data_boletim'].dt.isocalendar().week.astype(str)
    
    # Mantém apenas o último registro de cada semana (Sexta-feira ou véspera útil)
    df_final = df_final.drop_duplicates(subset=['ano_semana', 'indicador', 'periodo_previsao'], keep='last')
    
    # Limpeza da coluna auxiliar
    df_final = df_final.drop(columns=['ano_semana'])

    # Remove previsões sobre o passado LOL
    df_final = df_final[df_final['periodo_previsao'].astype(int) >= df_final['data_boletim'].dt.year]


    # Ordenação final e retorno para o formato de string
    df_final = df_final.sort_values(by=['data_boletim', 'indicador', 'periodo_previsao'])
    df_final['data_boletim'] = df_final['data_boletim'].dt.strftime('%Y-%m-%d')
    
    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    df_final.to_csv(caminho_arquivo, index=False)
    
    print(f"Concluído. Tabela salva em: {caminho_arquivo} ({len(df_final)} registros semanais filtrados).")