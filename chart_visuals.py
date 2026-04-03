import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
from settings.settings import load_config

config = load_config()

def carregar_dados(proj_dir, arquivo_focus, arquivo_sgs):
    df_focus = pd.read_csv(os.path.join(proj_dir, 'data', arquivo_focus))
    df_focus['data_boletim'] = pd.to_datetime(df_focus['data_boletim'], format='mixed')
    df_focus['data_alvo'] = pd.to_datetime(df_focus['periodo_previsao'].astype(str) + '-12-31')
    
    df_sgs = pd.read_csv(os.path.join(proj_dir, 'data', arquivo_sgs))
    df_sgs['data'] = pd.to_datetime(df_sgs['data'], format='mixed')
    
    return df_focus, df_sgs
    
    return df_focus, df_sgs

def plotar_trajetorias(indicador, df_focus, df_sgs, data_inicio):
    # Filtro para garantir que o gráfico comece exatamente em 2010-01-01
    limite_data = pd.to_datetime(data_inicio)
    df_real = df_sgs[(df_sgs['indicador'] == indicador) & (df_sgs['data'] >= limite_data)].copy()
    if df_real.empty: return

    # Corta previsões cujos boletins são muito antigos ou descolados do início da série real
    df_ind = df_focus[(df_focus['indicador'] == indicador) & (df_focus['data_boletim'] >= limite_data)].copy()
    if df_ind.empty: return

    boletins_selecionados = df_ind['data_boletim'].unique()

    plt.figure(figsize=(14, 7))
    plt.plot(df_real['data'], df_real['valor'], color='#2979FF', linewidth=2.5, zorder=5)

    for dt_bol in boletins_selecionados:
        df_bol = df_ind[df_ind['data_boletim'] == dt_bol].sort_values('data_alvo')
        if df_bol.empty: continue

        real_historico = df_real[df_real['data'] <= dt_bol]
        if not real_historico.empty:
            prev_x, prev_y = dt_bol, real_historico.iloc[-1]['valor']
            for _, row in df_bol.iterrows():
                curr_x, curr_y = row['data_alvo'], row['previsao']
                horizonte = pd.to_datetime(curr_x).year - pd.to_datetime(dt_bol).year
                
                # Definição de cores baseada no horizonte
                cor, alfa = ('#424242', 0.20) if horizonte <= 0 else (('#9E9E9E', 0.10) if horizonte == 1 else ('#E0E0E0', 0.05))
                plt.plot([prev_x, curr_x], [prev_y, curr_y], color=cor, alpha=alfa, linewidth=1.0, zorder=2)
                prev_x, prev_y = curr_x, curr_y

    indicador_formatado = indicador.replace('$', r'\$')
    plt.title(f'Trajetória Focus vs Realizado: {indicador_formatado}', fontsize=14, fontweight='bold', pad=15)
    
    # Lógica de Formatação Dinâmica do Eixo Y
    ax = plt.gca()
    if '%' in indicador:
        plt.ylabel('Percentual (%)', fontsize=11)
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(decimals=1))
    elif 'R$/US$' in indicador:
        plt.ylabel('Valor', fontsize=11)
        # Formata como R$ 5,20
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')))
    else:
        plt.ylabel('Valor', fontsize=11)
    # -----------------------------------------------------

    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.xticks(rotation=45)
    
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # Ajuste de legenda: Superior Direito para o PIB, Esquerdo para os demais
    loc_legenda = 'upper right' if 'PIB' in indicador else 'upper left'
    
    elementos_legenda = [
        Line2D([0], [0], color='#2979FF', lw=2.5, label='Dado Real'),
        Line2D([0], [0], color='#424242', lw=1.5, label='Expectativa (Ano Corrente)'),
        Line2D([0], [0], color='#9E9E9E', lw=1.5, label='Expectativa (1 Ano à Frente)'),
        Line2D([0], [0], color='#E0E0E0', lw=1.5, label='Expectativa (2+ Anos à Frente)')
    ]
    plt.legend(handles=elementos_legenda, frameon=False, loc=loc_legenda)
    
    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.gca().spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    
    pasta_charts = os.path.join(os.getcwd(), 'charts')
    os.makedirs(pasta_charts, exist_ok=True)
    
    # Nome de arquivo limpo (Removendo caracteres especiais de URL)
    nome_fmt = indicador.replace(' ', '_').replace('%', 'pct').replace('(', '').replace(')', '').replace('$', '').replace('/', '')
    plt.savefig(os.path.join(pasta_charts, f"trajetoria_{nome_fmt}.png"), dpi=300)
    plt.close()
    print(f"Gráfico salvo: {os.path.join(pasta_charts, f"trajetoria_{nome_fmt}.png")}")

if __name__ == "__main__":
    df_f, df_s = carregar_dados(proj_dir=os.getcwd())
    
    indicadores = df_s['indicador'].unique()
    for ind in indicadores:
        plotar_trajetorias(ind, df_f, df_s, data_inicio='2010-01-01')