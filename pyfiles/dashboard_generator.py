import pandas as pd
import plotly.graph_objects as go
import os

# ==========================================
# Funções Auxiliares de Formatação e Estilo
# ==========================================

def formatar_valor(valor, indicador):
    """Aplica a formatação de moeda ou percentual para o tooltip."""
    if '%' in indicador:
        return f"{valor:.2f}%".replace('.', ',')
    elif 'R$/US$' in indicador:
        return f"R$ {valor:.2f}".replace('.', ',')
    return str(valor)

def obter_configuracoes_eixo_y(indicador):
    """Retorna o título e o formato do eixo Y."""
    if '%' in indicador:
        return 'Percentual (%)', ',.1f'
    elif 'R$/US$' in indicador:
        return 'Taxa de Câmbio (R$)', ',.2f'
    return 'Valor', ''

def obter_cor_horizonte(ano_alvo, ano_boletim):
    """Define a cor baseada no horizonte de tempo (Ano Corrente, T+1, T+2+)."""
    horizonte = ano_alvo - ano_boletim
    if horizonte <= 0:
        return 'rgba(66, 66, 66, 0.25)'     # Ano Corrente: Cinza Escuro
    elif horizonte == 1:
        return 'rgba(158, 158, 158, 0.15)'  # 1 Ano à frente: Cinza Médio
    else:
        return 'rgba(200, 200, 200, 0.10)'  # 2 ou mais anos à frente: Cinza Claro

# ==========================================
# Funções de Construção do Gráfico
# ==========================================

def adicionar_linha_real(fig, df_real, indicador):
    """Adiciona a série temporal do dado realizado."""
    textos_hover = [
        f"Dado Real: {d.strftime('%m/%Y')}<br>Valor: {formatar_valor(v, indicador)}" 
        for d, v in zip(df_real['data'], df_real['valor'])
    ]
    
    fig.add_trace(go.Scatter(
        x=df_real['data'], 
        y=df_real['valor'],
        mode='lines', 
        name='Dado Real',
        line=dict(color='#2979FF', width=3),
        hoverinfo='text',
        text=textos_hover,
        zorder=10
    ))

def adicionar_tracos_expectativas(fig, df_ind, df_real, indicador):
    """Plota as trajetórias das previsões para todos os anos disponíveis."""
    boletins = df_ind['data_boletim'].unique()
    linhas_adicionadas = 0

    for dt_bol in boletins:
        # Pega todas as previsões futuras deste boletim (T, T+1, T+2, T+3...)
        df_bol = df_ind[df_ind['data_boletim'] == dt_bol].sort_values('data_alvo')
        real_hist = df_real[df_real['data'] <= dt_bol]
        
        if real_hist.empty or df_bol.empty:
            continue
            
        # Ponto de partida: último dado real conhecido na data do boletim
        prev_x = dt_bol
        prev_y = real_hist.iloc[-1]['valor']
        ano_boletim = pd.to_datetime(dt_bol).year
        
        for _, row in df_bol.iterrows():
            curr_x = row['data_alvo']
            curr_y = row['previsao']
            ano_alvo = curr_x.year
            
            cor = obter_cor_horizonte(ano_alvo, ano_boletim)
            texto_hover = (
                f"Data do Boletim: {pd.to_datetime(dt_bol).strftime('%d/%m/%Y')}<br>"
                f"Previsão para o Ano: {ano_alvo}<br>"
                f"Valor Projetado: {formatar_valor(curr_y, indicador)}"
            )
            
            fig.add_trace(go.Scatter(
                x=[prev_x, curr_x], 
                y=[prev_y, curr_y],
                mode='lines',
                line=dict(color=cor, width=1.5),
                showlegend=False,
                hoverinfo='text',
                text=texto_hover,
                zorder=2
            ))
            
            # O próximo ponto da trajetória parte do ponto atual
            prev_x, prev_y = curr_x, curr_y
            linhas_adicionadas += 1

    return linhas_adicionadas

def configurar_layout_e_legenda(fig, indicador):
    """Define títulos de eixos e legendas customizadas."""
    y_title, y_tickformat = obter_configuracoes_eixo_y(indicador)
    
    legend_map = [
        ('#424242', 'Expectativa (Ano Corrente)'),
        ('#9E9E9E', 'Expectativa (1 Ano à Frente)'),
        ('#C8C8C8', 'Expectativa (2+ Anos à Frente)')
    ]
    for cor, label in legend_map:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='lines',
            line=dict(color=cor, width=2),
            name=label
        ))

    fig.update_layout(
        title=dict(text=f'Trajetória Focus vs Realizado: {indicador}', font=dict(size=20, color='black')),
        template='plotly_white',
        hovermode='closest',
        xaxis=dict(
            title='Ano', # Rótulo do Eixo X adicionado
            showgrid=True, 
            gridcolor='#F0F0F0', 
            zeroline=False
        ),
        yaxis=dict(
            title=y_title, 
            tickformat=y_tickformat, 
            showgrid=True, 
            gridcolor='#F0F0F0', 
            zeroline=False
        ),
        legend=dict(
            orientation="h", 
            yanchor="bottom", y=1.02, 
            xanchor="right", x=1,
            font=dict(size=11)
        ),
        margin=dict(l=60, r=60, t=90, b=60)
    )

# ==========================================
# Função Principal
# ==========================================

def gerar_dashboard_interativo(arquivo_focus, arquivo_sgs, data_inicio='2010-01-01'):
    print("\n[Dashboard Interativo] Iniciando carregamento de arquivos...")
    
    df_focus = pd.read_csv(arquivo_focus)
    df_sgs = pd.read_csv(arquivo_sgs)
    
    df_focus['data_boletim'] = pd.to_datetime(df_focus['data_boletim'], format='mixed')
    df_focus['data_alvo'] = pd.to_datetime(df_focus['periodo_previsao'].astype(str) + '-12-31')
    df_sgs['data'] = pd.to_datetime(df_sgs['data'], format='mixed')

    limite_data = pd.to_datetime(data_inicio)
    indicadores = df_sgs['indicador'].unique()
    
    pasta_destino = 'charts/interativo'
    os.makedirs(pasta_destino, exist_ok=True)

    for ind in indicadores:
        print(f"\n[Dashboard Interativo] Processando: {ind}")
        fig = go.Figure()

        df_real = df_sgs[(df_sgs['indicador'] == ind) & (df_sgs['data'] >= limite_data)].sort_values('data')
        df_ind = df_focus[(df_focus['indicador'] == ind) & (df_focus['data_boletim'] >= limite_data)].copy()
        
        if df_real.empty: 
            print(f"  -> Aviso: Sem dados históricos. Pulando.")
            continue
        
        adicionar_linha_real(fig, df_real, ind)
        linhas_plotadas = adicionar_tracos_expectativas(fig, df_ind, df_real, ind)
        
        print(f"  -> {len(df_ind['data_boletim'].unique())} boletins processados.")
        print(f"  -> {linhas_plotadas} segmentos de previsão adicionados.")
        
        configurar_layout_e_legenda(fig, ind)

        nome_fmt = ind.replace(' ', '_').replace('%', 'pct').replace('(', '').replace(')', '').replace('$', '').replace('/', '')
        caminho_html = os.path.join(pasta_destino, f"trajetoria_{nome_fmt}.html")
        fig.write_html(caminho_html)
        
        print(f"  -> [SUCESSO] Arquivo salvo: {caminho_html}")

    print("\n[Dashboard Interativo] Finalizado.")

if __name__ == "__main__":
    gerar_dashboard_interativo('data/dados_focus.csv', 'data/dados_sgs.csv')