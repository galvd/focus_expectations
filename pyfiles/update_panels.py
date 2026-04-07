import pandas as pd
from datetime import datetime
import re
import os

def formatar(valor, ind):
    if pd.isna(valor): return "N/D"
    if '%' in ind or 'Selic' in ind:
        return f"{valor:.2f}%".replace('.', ',')
    return f"R$ {valor:.2f}".replace('.', ',')

def atualizar_paineis():
    print("\n[Atualizador] Injetando dados nos painéis...")
    df_sgs = pd.read_csv('data/dados_sgs.csv')
    df_focus = pd.read_csv('data/dados_focus.csv')
    
    ano_atual = datetime.now().year
    valores = {}
    
    indicadores = {
        'PIB': 'PIB Acum. 4tri (%)',
        'IPCA': 'IPCA (%)',
        'SELIC': 'Selic (% a.a)',
        'CAMBIO': 'Taxa de Câmbio (R$/US$)'
    }

    for prefixo, nome_col in indicadores.items():
        # Dado Real
        df_real_ind = df_sgs[df_sgs['indicador'] == nome_col]
        val_real = df_real_ind.iloc[-1]['valor'] if not df_real_ind.empty else float('nan')
        
        # Expectativa Focus
        df_focus_ind = df_focus[(df_focus['indicador'] == nome_col) & (pd.to_datetime(df_focus['periodo_previsao'].astype(str) + '-12-31').dt.year == ano_atual)]
        val_focus = df_focus_ind.iloc[-1]['previsao'] if not df_focus_ind.empty else float('nan')
        
        valores[f"REAL_{prefixo}"] = formatar(val_real, nome_col)
        valores[f"FOCUS_{prefixo}"] = formatar(val_focus, nome_col)

    def injetar_dados(caminho_arquivo):
        if not os.path.exists(caminho_arquivo):
            print(f" -> Arquivo não encontrado: {caminho_arquivo}")
            return

        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        for chave, novo_valor in valores.items():
            padrao = rf'().*?()'
            substituicao = rf'\g<1>{novo_valor}\g<2>'
            conteudo = re.sub(padrao, substituicao, conteudo, flags=re.DOTALL)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f" -> Atualizado: {caminho_arquivo}")

    injetar_dados('index.html')
    injetar_dados('charts/index.md')
    print("[Atualizador] Concluído.")

if __name__ == "__main__":
    atualizar_paineis()