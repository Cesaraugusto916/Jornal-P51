# -*- coding: latin-1 -*-
import requests
import feedparser
import random
from datetime import datetime
from pathlib import Path

# --- CONFIGURAÇÕES ---
FILE_ENCODING = "iso-8859-1"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- URLs DAS APIs E FEEDS ---
URL_CLIMA = "https://wttr.in/Sao+Paulo?format=j1&lang=pt"
URL_G1_RSS = "http://g1.globo.com/dynamo/rss2.xml"
URL_TABNEWS_RSS = "https://www.tabnews.com.br/recentes/rss"
# CORREÇÃO 1: A URL da API foi corrigida para o subdomínio 'economia'.
URL_FINANCEIRO = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL"
URL_METAR = "https://tgftp.nws.noaa.gov/data/observations/metar/stations/SBSP.TXT"
URL_VERSICULO = "https://bible-api.com/?random=verse&translation=almeida"

# --- FALLBACKS E TRADUÇÕES ---
VERSICULOS_FALLBACK = [
    ("João 3:16", "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna."),
    ("Filipenses 4:13", "Tudo posso naquele que me fortalece."),
    ("Salmos 23:1", "O Senhor é o meu pastor; nada me faltará."),
]
MESES_PT_BR = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def get_desktop_path():
    """Encontra a pasta 'Área de Trabalho' ou 'Desktop' do usuário."""
    home = Path.home()
    desktop_path = home / 'Área de Trabalho'
    if desktop_path.exists():
        return desktop_path
    desktop_path = home / 'Desktop'
    if desktop_path.exists():
        return desktop_path
    return home

def get_data_pt_br():
    """Retorna a data atual formatada com o mês em português."""
    now = datetime.now()
    return f"{now.day} de {MESES_PT_BR[now.month]} de {now.year}"

def normalizar_texto(texto):
    """Garante que o texto seja compatível com a codificação ISO-8859-1."""
    if not texto: return ""
    return texto.encode(FILE_ENCODING, 'ignore').decode(FILE_ENCODING)

# ==============================================================================
# A. ETAPA DE EXTRAÇÃO (DATA FETCHING)
# ==============================================================================

def get_clima():
    try:
        response = requests.get(URL_CLIMA, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        condicao_atual = data.get('current_condition', [{}])[0]
        previsao_hoje = data.get('weather', [{}])[0]
        return {
            "temp_atual": condicao_atual.get('temp_C', 'N/A'),
            "sensacao": condicao_atual.get('FeelsLikeC', 'N/A'),
            "descricao": condicao_atual.get('lang_pt', [{'value': 'N/A'}])[0].get('value', 'N/A'),
            "max_hoje": previsao_hoje.get('maxtempC', 'N/A'),
            "min_hoje": previsao_hoje.get('mintempC', 'N/A')
        }
    except Exception as e:
        print(f"ERRO ao buscar clima: {e}")
        return None

def get_versiculo_biblico():
    try:
        response = requests.get(URL_VERSICULO, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return (normalizar_texto(data['reference']), normalizar_texto(data['text']))
    except Exception as e:
        print(f"ERRO ao buscar versículo (usando fallback): {e}")
        return random.choice(VERSICULOS_FALLBACK)

def get_noticias_rss(url, quantidade):
    try:
        feed = feedparser.parse(url)
        return [normalizar_texto(entry.title) for entry in feed.entries[:quantidade]]
    except Exception as e:
        print(f"ERRO ao buscar notícias de '{url}': {e}")
        return ["N/A"] * quantidade

def get_financeiro():
    """Busca cotações usando a URL corrigida."""
    try:
        response = requests.get(URL_FINANCEIRO, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "dolar": f"R$ {float(data['USDBRL']['bid']):.2f}",
            "euro": f"R$ {float(data['EURBRL']['bid']):.2f}",
            "btc": f"R$ {float(data['BTCBRL']['bid']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        }
    except Exception as e:
        print(f"ERRO ao buscar dados financeiros: {e}")
        return None

def get_metar():
    try:
        response = requests.get(URL_METAR, headers=HEADERS, timeout=15)
        response.raise_for_status()
        linhas = response.text.strip().splitlines()
        if len(linhas) >= 2: return linhas[1]
        return "Formato de METAR inesperado."
    except Exception as e:
        print(f"ERRO ao buscar METAR: {e}")
        return "METAR N/A"

# ==============================================================================
# B. ETAPA DE TRANSFORMAÇÃO (FILE BUILDING)
# ==============================================================================

def build_html(clima, versiculo, noticias_g1, noticias_tech, financeiro, metar):
    """Constrói a string HTML com todos os dados coletados."""
    data_hoje = get_data_pt_br()
    
    html = f"<html><head><title>Diario P51</title></head>"
    html += f"<body style='font-family: sans-serif; font-size: 22px;'>"
    html += f"<h2 align='center' style='font-size: 28px;'>Diario P51</h2>"
    html += f"<p align='center'><i>{data_hoje}</i></p><hr>"

    html += "<h3 style='font-size: 24px;'>-- Devocional --</h3>"
    if versiculo:
        html += f"<p><b>{versiculo[0]}</b><br>{versiculo[1]}</p><hr>"
    
    html += "<h3 style='font-size: 24px;'>-- Clima em SP --</h3>"
    if clima:
        html += f"<p><b>Agora:</b> {clima['temp_atual']}C (Sensacao: {clima['sensacao']}C)<br>"
        html += f"<b>Previsao:</b> Min {clima['min_hoje']}C / Max {clima['max_hoje']}C<br>"
        html += f"<i>{normalizar_texto(clima['descricao'])}</i></p><hr>"

    html += "<h3 style='font-size: 24px;'>-- Noticias (G1) --</h3><ul>"
    for manchete in noticias_g1: html += f"<li>{manchete}</li>"
    html += "</ul><hr>"

    html += "<h3 style='font-size: 24px;'>-- Tech & IA (TabNews) --</h3><ul>"
    for manchete in noticias_tech: html += f"<li>{manchete}</li>"
    html += "</ul><hr>"

    html += "<h3 style='font-size: 24px;'>-- Financeiro --</h3>"
    if financeiro:
        html += f"<p><b>Dolar:</b> {financeiro['dolar']}<br><b>Euro:</b> {financeiro['euro']}<br><b>Bitcoin:</b> {financeiro['btc']}</p><hr>"
    else:
        # CORREÇÃO 1: Mensagem de erro sem acentos.
        html += "<p>Cotacao Indisponivel</p><hr>"
    
    html += f"<p align='center' style='font-size:10px;'><b>METAR SBSP:</b> {normalizar_texto(metar)}</p>"
    html += "</body></html>"
    return html

# ==============================================================================
# C. ETAPA DE CARGA (LOCAL SAVE)
# ==============================================================================

def save_file_locally(html_content, path, filename):
    """Salva o conteúdo em um arquivo local com o cabeçalho binário."""
    full_path = path / filename
    
    binary_header = b'\xB3\x00\x00\x00\x01\x00\x00\x00\x15\x00\x00\x00\x5A\x00\x00\x00\x30\x00\x00\x00'
    charset_header = b' charset=ISO-8859-1\n'

    try:
        print(f"Gerando arquivo em '{full_path}'...")
        with open(full_path, 'wb') as f:
            f.write(binary_header)
            f.write(charset_header)
            f.write(html_content.encode(FILE_ENCODING, 'ignore'))
        
        print(f"\nSucesso! Jornal gerado em: {full_path}")

    except PermissionError:
        print(f"ERRO: Sem permissão para escrever em '{path}'.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao salvar o arquivo: {e}")

def main():
    """Função principal que orquestra o pipeline ETL."""
    print("Iniciando pipeline do Diário P51...")

    # CORREÇÃO 3: Gerar nome do arquivo dinamicamente com a data.
    output_filename = datetime.now().strftime("Jornal_P51_%Y-%m-%d.html")
    desktop = get_desktop_path()
    
    # 1. Extração
    clima = get_clima()
    versiculo = get_versiculo_biblico()
    noticias_g1 = get_noticias_rss(URL_G1_RSS, 3)
    # CORREÇÃO 2: Buscar 5 notícias de tecnologia.
    noticias_tech = get_noticias_rss(URL_TABNEWS_RSS, 5)
    financeiro = get_financeiro()
    metar = get_metar()
    
    # 2. Transformação
    html_content = build_html(clima, versiculo, noticias_g1, noticias_tech, financeiro, metar)
    
    # 3. Carga (passando o nome dinâmico do arquivo)
    save_file_locally(html_content, desktop, output_filename)
    
    print("\nPipeline finalizado.")

if __name__ == "__main__":
    main()
