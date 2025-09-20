# bot_inteligente.py

import time
import random
import sqlite3
import json
from datetime import date, datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from faker import Faker
from unidecode import unidecode

# --- 1. CONFIGURAÇÕES PRINCIPAIS (VOCÊ PODE AJUSTAR AQUI) ---
URL_DA_PAGINA = "https://leidosilencio.paginas.digital/leidosilencio"
ENVIOS_POR_DIA = 250
ARQUIVO_BD = "contatos_usados.db"  # Banco de dados com a "memória" de contatos
ARQUIVO_ESTADO_JSON = "estado_bot.json"  # Arquivo que guarda o progresso diário

# Defina o horário de "trabalho" do bot (formato 24h)
HORA_INICIO = 8  # 8 da manhã
HORA_FIM = 22  # 10 da noite

# --- 2. SETUP E FUNÇÕES DE BANCO DE DADOS (MEMÓRIA) ---
# (Estas funções são as mesmas da versão anterior, garantindo a unicidade)
fake = Faker("pt_BR")


def setup_database():
    conn = sqlite3.connect(ARQUIVO_BD)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY, nome TEXT UNIQUE, telefone TEXT UNIQUE, email TEXT UNIQUE
        )
    """
    )
    conn.commit()
    conn.close()


def gerar_contato_unico():
    conn = sqlite3.connect(ARQUIVO_BD)
    cursor = conn.cursor()
    while True:
        primeiro_nome, sobrenome = fake.first_name(), fake.last_name()
        nome_completo = f"{primeiro_nome} {sobrenome}"
        nome_email = unidecode(f"{primeiro_nome}.{sobrenome}").lower()
        email = f"{nome_email}{random.randint(100, 999)}@{fake.free_email_domain()}"
        telefone = f"119{random.randint(10000000, 99999999)}"
        cursor.execute(
            "SELECT id FROM contatos WHERE nome = ? OR telefone = ? OR email = ?",
            (nome_completo, telefone, email),
        )
        if cursor.fetchone() is None:
            break
    conn.close()
    return {"nome": nome_completo, "email": email, "telefone": telefone}


def salvar_contato_usado(dados):
    conn = sqlite3.connect(ARQUIVO_BD)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contatos (nome, telefone, email) VALUES (?, ?, ?)",
        (dados["nome"], dados["telefone"], dados["email"]),
    )
    conn.commit()
    conn.close()


# --- 3. FUNÇÕES DE ESTADO E AGENDAMENTO (O NOVO "CÉREBRO") ---


def ler_estado():
    """Lê o progresso do dia a partir de um arquivo JSON."""
    try:
        with open(ARQUIVO_ESTADO_JSON, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Se o arquivo não existe, é a primeira execução de todas.
        return {"ultimo_dia": "", "contagem_hoje": 0}


def salvar_estado(dia, contagem):
    """Salva o progresso do dia no arquivo JSON."""
    with open(ARQUIVO_ESTADO_JSON, "w") as f:
        json.dump({"ultimo_dia": dia, "contagem_hoje": contagem}, f)


# --- 4. LÓGICA PRINCIPAL DO BOT ---

setup_database()

print("Configurando o driver do Selenium para o ambiente de nuvem...")
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)
print("Driver configurado.")

# Calcula o intervalo médio de tempo entre envios para distribuir ao longo do dia
segundos_de_trabalho = (HORA_FIM - HORA_INICIO) * 3600
intervalo_medio = segundos_de_trabalho / ENVIOS_POR_DIA
print(f"O bot irá operar entre {HORA_INICIO}h e {HORA_FIM}h.")
print(f"Intervalo médio entre envios: {intervalo_medio / 60:.2f} minutos.")

while True:
    estado = ler_estado()
    hoje = date.today().isoformat()
    hora_atual = datetime.now().hour

    # Reseta a contagem se for um novo dia
    if estado["ultimo_dia"] != hoje:
        print(f"--- {hoje} ---")
        print("É um novo dia! Resetando a contagem de envios.")
        estado = {"ultimo_dia": hoje, "contagem_hoje": 0}
        salvar_estado(hoje, 0)

    # Verifica se a cota diária já foi atingida
    if estado["contagem_hoje"] >= ENVIOS_POR_DIA:
        print(
            f"Cota diária de {ENVIOS_POR_DIA} envios já foi atingida. Aguardando o próximo dia."
        )
        time.sleep(3600)  # Dorme por 1 hora e verifica de novo
        continue

    # Verifica se está no horário de "trabalho"
    if HORA_INICIO <= hora_atual < HORA_FIM:
        contagem_atual = estado["contagem_hoje"]
        print(
            f"\nRetomando envios. Progresso de hoje: {contagem_atual}/{ENVIOS_POR_DIA}."
        )

        # Gera e envia o próximo contato
        dados = gerar_contato_unico()
        print(f"  Enviando contato {contagem_atual + 1}: {dados['nome']}")

        try:
            driver.get(URL_DA_PAGINA)
            time.sleep(3)
            driver.find_element(By.NAME, "name").send_keys(dados["nome"])
            driver.find_element(By.NAME, "phone").send_keys(dados["telefone"])
            driver.find_element(By.NAME, "email").send_keys(dados["email"])
            time.sleep(1)
            driver.find_element(
                By.XPATH, "//button[contains(text(), 'EU APOIO!')]"
            ).click()

            # Se deu certo, salve na memória (BD) e atualize o estado (JSON)
            salvar_contato_usado(dados)
            nova_contagem = contagem_atual + 1
            salvar_estado(hoje, nova_contagem)
            print(
                f"  Sucesso! Contato salvo. Progresso: {nova_contagem}/{ENVIOS_POR_DIA}."
            )

            # Calcula um intervalo de espera aleatório para parecer mais humano
            tempo_de_espera = intervalo_medio * random.uniform(0.7, 1.3)
            print(
                f"  Aguardando por {tempo_de_espera / 60:.2f} minutos antes do próximo envio."
            )
            time.sleep(tempo_de_espera)

        except Exception as e:
            print(
                f"  ERRO no envio {contagem_atual + 1}: {e}. Tentando novamente em 5 minutos..."
            )
            time.sleep(300)

    else:
        # Fora do horário de trabalho
        print(
            f"Fora do horário de trabalho ({HORA_INICIO}h-{HORA_FIM}h). Verificando novamente em 30 minutos..."
        )
        time.sleep(1800)

driver.quit()
