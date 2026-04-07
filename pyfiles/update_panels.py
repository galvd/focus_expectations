import pandas as pd
from datetime import datetime
import os

# ==========================================
# TEMPLATES ESTÁTICOS
# ==========================================

TEMPLATE_MD = """# 📈 Dashboard: Expectativas de Mercado (Focus/BCB)

**[Acesse o Dashboard Interativo clicando aqui](https://galvd.github.io/focus_expectations/)**

**Última atualização:** __DATA_ATUALIZACAO__

Este painel estático apresenta as trajetórias das expectativas de mercado coletadas semanalmente pelo Banco Central do Brasil e expressadas pela medianda das expectativas das instituições financeiras consultadas.

## Painel Resumo: Últimos Valores e Tendências
*(Comparações referentes à semana anterior: ▲ Subiu, ▼ Desceu, = Manteve)*

| 🔹 PIB (série real suavizada) | 🔹 IPCA | 🔹 Taxa Selic | 🔹 Câmbio |
| :--- | :--- | :--- | :--- |
| **Dado Realizado:**<br>**__REAL_PIB__**<br><br>**__ANO_0__:** __F0_PIB__ __T0_PIB__<br>**__ANO_1__:** __F1_PIB__ __T1_PIB__<br>**__ANO_2__:** __F2_PIB__ __T2_PIB__ | **Dado Realizado:**<br>**__REAL_IPCA__**<br><br>**__ANO_0__:** __F0_IPCA__ __T0_IPCA__<br>**__ANO_1__:** __F1_IPCA__ __T1_IPCA__<br>**__ANO_2__:** __F2_IPCA__ __T2_IPCA__ | **Dado Realizado:**<br>**__REAL_SELIC__**<br><br>**__ANO_0__:** __F0_SELIC__ __T0_SELIC__<br>**__ANO_1__:** __F1_SELIC__ __T1_SELIC__<br>**__ANO_2__:** __F2_SELIC__ __T2_SELIC__ | **Dado Realizado:**<br>**__REAL_CAMBIO__**<br><br>**__ANO_0__:** __F0_CAMBIO__ __T0_CAMBIO__<br>**__ANO_1__:** __F1_CAMBIO__ __T1_CAMBIO__<br>**__ANO_2__:** __F2_CAMBIO__ __T2_CAMBIO__ |

---

## Expectativas sobre o PIB Anual (Série Suavizada)
Expectativas de crescimento do Produto Interno Bruto.
<img src="./trajetoria_PIB_Acum._4tri_pct.png" width="100%">

---

## Expectativas sobre a Inflação (IPCA)
Expectativas de inflação oficial (IPCA).
<img src="./trajetoria_IPCA_pct.png" width="100%">

---

## Expectativas sobre a Taxa Selic
Projeções para a taxa básica de juros da economia.
<img src="./trajetoria_Selic_pct_a.a.png" width="100%">

---

## Expectativas sobre a Taxa de Câmbio
Acompanhamento da trajetória esperada para a taxa de câmbio.
<img src="./trajetoria_Taxa_de_Câmbio_RUS.png" width="100%">

---

[← Voltar para o Perfil](https://github.com/galvd)
"""

TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor de Expectativas: Realizado vs Boletim Focus</title>
    <style>
        :root { --primary: #2c3e50; --accent: #3498db; --bg: #f8f9fa; --text: #333; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: auto; }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #eee; padding-bottom: 20px; }
        .disclaimer { background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; font-size: 0.9rem; margin-bottom: 20px; border: 1px solid #ffeeba; }
        
        .summary-panel { margin-bottom: 30px; }
        .summary-header { margin-bottom: 20px; }
        .summary-header h2 { margin: 0 0 5px 0; color: var(--primary); font-size: 1.5rem; }
        .summary-header p { margin: 0; color: #666; font-style: italic; font-size: 0.95rem; }
        
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; }
        .summary-card { background: white; padding: 20px; border-radius: 8px; border-top: 4px solid var(--accent); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .summary-card h3 { margin: 0 0 15px 0; font-size: 1.2rem; color: var(--primary); border-bottom: 1px solid #eee; padding-bottom: 10px; }
        .val-real { color: #2979FF; font-weight: bold; font-size: 1.1rem;}
        
        .focus-box { margin-top: 15px; padding-top: 10px; font-size: 0.95rem; }
        .focus-row { display: flex; justify-content: space-between; margin-bottom: 8px; align-items: center; }
        .focus-row span:first-child { color: #666; font-weight: 600; }
        .trend { font-weight: bold; margin-left: 5px; font-size: 0.9rem; color: #555; }

        details { background: white; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; border: 1px solid #ddd; }
        summary { padding: 15px 20px; font-size: 1.2rem; font-weight: bold; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; transition: background 0.3s; }
        summary:hover { background: #f1f1f1; }
        summary::after { content: "▶"; font-size: 0.8rem; transition: transform 0.3s; }
        details[open] summary::after { transform: rotate(90deg); }
        details[open] summary { border-bottom: 1px solid #eee; background: #fafafa; }
        .content { padding: 20px; }
        iframe { width: 100%; height: 700px; border: none; }
        .links-topo { margin: 15px 0; line-height: 1.6; }
        .links-topo a { color: var(--accent); text-decoration: none; font-weight: bold; }
        .links-topo a:hover { text-decoration: underline; }
        .footer { text-align: center; margin-top: 50px; padding: 20px; font-size: 0.9rem; border-top: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>Monitor de Expectativas: Realizado vs Expectativas Boletim Focus</h1>
            <p>Última atualização: __DATA_ATUALIZACAO__</p>
            <div class="links-topo">
                <p>Construído e mantido por <strong>Daniel Galvêas</strong> - <a href="https://github.com/galvd" target="_blank">github.com/galvd</a></p>
                <p>Para visualizar a versão estática dos gráficos, <a href="https://github.com/galvd/focus_expectations/blob/main/charts/index.md" target="_blank">clique aqui</a>.</p>
                <p>Para visualizar o repositório do projeto no Github, <a href="https://github.com/galvd/focus_expectations" target="_blank">clique aqui</a>.</p>
            </div>
            <div class="disclaimer">
                ⚠️ <strong>Nota:</strong> O carregamento dos gráficos pode ser lento devido ao elevado volume de dados processados em cada série histórica.
            </div>
        </header>
        
        <div class="summary-panel">
            <div class="summary-header">
                <h2>Painel Resumo: Últimos Valores e Tendências</h2>
                <p>(Comparações referentes à semana anterior: ▲ Subiu, ▼ Desceu, = Manteve)</p>
            </div>
            
            <div class="summary-grid">
                
                <div class="summary-card">
                    <h3>PIB (série real suavizada)</h3>
                    <p style="margin: 0; color: #555;">Dado Realizado: <span class="val-real">__REAL_PIB__</span></p>
                    <div class="focus-box">
                        <div class="focus-row"><span>__ANO_0__:</span> <span><strong>__F0_PIB__</strong> <span class="trend">__T0_PIB__</span></span></div>
                        <div class="focus-row"><span>__ANO_1__:</span> <span><strong>__F1_PIB__</strong> <span class="trend">__T1_PIB__</span></span></div>
                        <div class="focus-row"><span>__ANO_2__:</span> <span><strong>__F2_PIB__</strong> <span class="trend">__T2_PIB__</span></span></div>
                    </div>
                </div>

                <div class="summary-card">
                    <h3>IPCA</h3>
                    <p style="margin: 0; color: #555;">Dado Realizado: <span class="val-real">__REAL_IPCA__</span></p>
                    <div class="focus-box">
                        <div class="focus-row"><span>__ANO_0__:</span> <span><strong>__F0_IPCA__</strong> <span class="trend">__T0_IPCA__</span></span></div>
                        <div class="focus-row"><span>__ANO_1__:</span> <span><strong>__F1_IPCA__</strong> <span class="trend">__T1_IPCA__</span></span></div>
                        <div class="focus-row"><span>__ANO_2__:</span> <span><strong>__F2_IPCA__</strong> <span class="trend">__T2_IPCA__</span></span></div>
                    </div>
                </div>

                <div class="summary-card">
                    <h3>Taxa Selic</h3>
                    <p style="margin: 0; color: #555;">Dado Realizado: <span class="val-real">__REAL_SELIC__</span></p>
                    <div class="focus-box">
                        <div class="focus-row"><span>__ANO_0__:</span> <span><strong>__F0_SELIC__</strong> <span class="trend">__T0_SELIC__</span></span></div>
                        <div class="focus-row"><span>__ANO_1__:</span> <span><strong>__F1_SELIC__</strong> <span class="trend">__T1_SELIC__</span></span></div>
                        <div class="focus-row"><span>__ANO_2__:</span> <span><strong>__F2_SELIC__</strong> <span class="trend">__T2_SELIC__</span></span></div>
                    </div>
                </div>

                <div class="summary-card">
                    <h3>Câmbio</h3>
                    <p style="margin: 0; color: #555;">Dado Realizado: <span class="val-real">__REAL_CAMBIO__</span></p>
                    <div class="focus-box">
                        <div class="focus-row"><span>__ANO_0__:</span> <span><strong>__F0_CAMBIO__</strong> <span class="trend">__T0_CAMBIO__</span></span></div>
                        <div class="focus-row"><span>__ANO_1__:</span> <span><strong>__F1_CAMBIO__</strong> <span class="trend">__T1_CAMBIO__</span></span></div>
                        <div class="focus-row"><span>__ANO_2__:</span> <span><strong>__F2_CAMBIO__</strong> <span class="trend">__T2_CAMBIO__</span></span></div>
                    </div>
                </div>

            </div>
        </div>

        <details>
            <summary>Expectativas sobre o PIB Anual (Série Suavizada)</summary>
            <div class="content"><iframe src="charts/interativo/trajetoria_PIB_Acum._4tri_pct.html" loading="lazy"></iframe></div>
        </details>
        <details>
            <summary>Expectativas sobre a Inflação (IPCA)</summary>
            <div class="content"><iframe src="charts/interativo/trajetoria_IPCA_pct.html" loading="lazy"></iframe></div>
        </details>
        <details>
            <summary>Expectativas sobre a Taxa Selic</summary>
            <div class="content"><iframe src="charts/interativo/trajetoria_Selic_pct_a.a.html" loading="lazy"></iframe></div>
        </details>
        <details>
            <summary>Expectativas sobre a Taxa de Câmbio</summary>
            <div class="content"><iframe src="charts/interativo/trajetoria_Taxa_de_Câmbio_RUS.html" loading="lazy"></iframe></div>
        </details>
        <footer class="footer">© 2026 Monitor de Expectativas Econômicas</footer>
    </div>
</body>
</html>
"""

# ==========================================
# MOTOR DE INJEÇÃO
# ==========================================

def formatar(valor, ind):
    if pd.isna(valor): return "-"
    if '%' in ind or 'Selic' in ind: return f"{valor:.2f}%".replace('.', ',')
    return f"R$ {valor:.2f}".replace('.', ',')

def get_trend(atual, anterior):
    if pd.isna(atual) or pd.isna(anterior): 
        return ""
    if abs(atual - anterior) < 0.0001: 
        return "(=)"
    return "(▲)" if atual > anterior else "(▼)"

def atualizar_paineis():
    print("[SSG] Carregando dados base...")
    pasta_raiz = os.getcwd()
    
    caminho_sgs = os.path.join(pasta_raiz, 'data', 'dados_sgs.csv')
    caminho_focus = os.path.join(pasta_raiz, 'data', 'dados_focus.csv')

    df_sgs = pd.read_csv(caminho_sgs)
    df_focus = pd.read_csv(caminho_focus)
    
    datas_boletins = sorted(df_focus['data_boletim'].unique())
    bol_atual = datas_boletins[-1] if len(datas_boletins) > 0 else None
    bol_anterior = datas_boletins[-2] if len(datas_boletins) > 1 else bol_atual

    data_hoje = datetime.now()
    ano_atual = data_hoje.year
    data_formatada = data_hoje.strftime('%d/%m/%Y')
    anos_alvo = [ano_atual, ano_atual + 1, ano_atual + 2]
    
    indicadores = {
        'PIB': 'PIB Acum. 4tri (%)', 'IPCA': 'IPCA (%)',
        'SELIC': 'Selic (% a.a)', 'CAMBIO': 'Taxa de Câmbio (R$/US$)'
    }

    html_final = TEMPLATE_HTML
    md_final = TEMPLATE_MD
    
    # Injeta a data de atualização
    html_final = html_final.replace("__DATA_ATUALIZACAO__", data_formatada)
    md_final = md_final.replace("__DATA_ATUALIZACAO__", data_formatada)
    
    for i, ano in enumerate(anos_alvo):
        html_final = html_final.replace(f"__ANO_{i}__", str(ano))
        md_final = md_final.replace(f"__ANO_{i}__", str(ano))

    for prefixo, nome_col in indicadores.items():
        df_real_ind = df_sgs[df_sgs['indicador'] == nome_col]
        val_real = df_real_ind.iloc[-1]['valor'] if not df_real_ind.empty else float('nan')
        
        str_real = formatar(val_real, nome_col)
        html_final = html_final.replace(f"__REAL_{prefixo}__", str_real)
        md_final = md_final.replace(f"__REAL_{prefixo}__", str_real)

        for i, ano in enumerate(anos_alvo):
            filtro_base = (df_focus['indicador'] == nome_col) & (df_focus['periodo_previsao'].astype(str).str[:4] == str(ano))
            
            val_foco_atual = df_focus[filtro_base & (df_focus['data_boletim'] == bol_atual)]['previsao'].mean()
            val_foco_ant = df_focus[filtro_base & (df_focus['data_boletim'] == bol_anterior)]['previsao'].mean()
            
            str_focus = formatar(val_foco_atual, nome_col)
            trend_symbol = get_trend(val_foco_atual, val_foco_ant)
            
            html_final = html_final.replace(f"__F{i}_{prefixo}__", str_focus)
            html_final = html_final.replace(f"__T{i}_{prefixo}__", trend_symbol)
            
            md_final = md_final.replace(f"__F{i}_{prefixo}__", str_focus)
            md_final = md_final.replace(f"__T{i}_{prefixo}__", trend_symbol)

    caminho_html = os.path.join(pasta_raiz, 'index.html')
    with open(caminho_html, 'w', encoding='utf-8') as f:
        f.write(html_final)
    print(f"[SSG] HTML sobrescrito com sucesso.")

    caminho_md = os.path.join(pasta_raiz, 'charts', 'index.md')
    os.makedirs(os.path.dirname(caminho_md), exist_ok=True)
    with open(caminho_md, 'w', encoding='utf-8') as f:
        f.write(md_final)
    print(f"[SSG] Markdown sobrescrito com layout de tabela.")

if __name__ == "__main__":
    atualizar_paineis()