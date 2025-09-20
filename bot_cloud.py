# bot_cloud.py

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from faker import Faker
from unidecode import unidecode
from selenium.common.exceptions import NoSuchElementException

# --- 1. CONFIGURAÇÕES E GERAÇÃO DE DADOS CONSISTENTES ---

# Inicializa o Faker para o Brasil
fake = Faker("pt_BR")


def gerar_dados_consistentes():
    """
    Gera um conjunto de dados onde o nome e o e-mail são compatíveis
    e o telefone é um número válido de São Paulo (DDD 11).
    """
    primeiro_nome = fake.first_name()
    sobrenome = fake.last_name()
    nome_completo = f"{primeiro_nome} {sobrenome}"

    # Cria uma base para o e-mail a partir do nome, sem acentos e em minúsculas
    nome_email = unidecode(f"{primeiro_nome}.{sobrenome}").lower()
    email = f"{nome_email}{random.randint(10, 99)}@{fake.free_email_domain()}"

    # Gera um número de celular de São Paulo (11) com 9 dígitos, começando com 9
    # Formato: 119XXXXXXXX
    telefone = f"119{random.randint(10000000, 99999999)}"

    return {"nome": nome_completo, "email": email, "telefone": telefone}


# URL DO FORMULÁRIO
URL_DA_PAGINA = "https://leidosilencio.paginas.digital/leidosilencio"


# --- 2. CONFIGURAÇÃO DO SELENIUM PARA AMBIENTE DE NUVEM (HEADLESS) ---

print("Configurando o driver do Selenium para o ambiente de nuvem...")
chrome_options = Options()
chrome_options.add_argument(
    "--headless"
)  # ESSENCIAL: Roda o Chrome sem abrir uma janela visual
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

# O Selenium Manager tentará encontrar o Chrome e o ChromeDriver instalados pelo packages.txt
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)

print("Driver configurado com sucesso.")

# --- 3. LÓGICA DE PREENCHIMENTO EM LOOP INFINITO ---

print("Iniciando o bot em modo infinito. Os logs aparecerão aqui.")
contador = 0

while True:
    contador += 1
    print(f"\n--- Iniciando preenchimento nº {contador} ---")

    try:
        # Abre a página do formulário
        driver.get(URL_DA_PAGINA)
        time.sleep(3)

        # Gera um novo conjunto de dados consistentes
        dados = gerar_dados_consistentes()
        print(
            f"Dados gerados: Nome='{dados['nome']}', E-mail='{dados['email']}', Tel='{dados['telefone']}'"
        )

        # Preenche os campos do formulário
        driver.find_element(By.NAME, "name").send_keys(dados["nome"])
        driver.find_element(By.NAME, "phone").send_keys(dados["telefone"])
        driver.find_element(By.NAME, "email").send_keys(dados["email"])

        time.sleep(random.uniform(0.5, 1.5))

        # Clica no botão "EU APOIO!"
        driver.find_element(By.XPATH, "//button[contains(text(), 'EU APOIO!')]").click()
        print(f"Formulário nº {contador} enviado com sucesso!")

        time.sleep(random.uniform(3, 5))

    except NoSuchElementException as e:
        print(
            f"ERRO: Não foi possível encontrar um elemento na página. Verificando screenshot..."
        )
        # Salva uma 'foto' da página para ajudar a depurar o que deu errado
        driver.save_screenshot("error_screenshot.png")
        print(f"Screenshot 'error_screenshot.png' salvo. Erro: {e}")
        time.sleep(10)  # Espera um pouco mais antes de tentar de novo
        continue
    except Exception as e:
        print(f"Ocorreu um erro inesperado e fatal: {e}")
        driver.save_screenshot("fatal_error_screenshot.png")
        print("Screenshot de erro fatal salvo. O bot será encerrado.")
        break

# Encerra o navegador ao sair do loop
driver.quit()
print("\nBot finalizado.")
