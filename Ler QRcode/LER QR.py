import sqlite3
import os
import cv2
import qrcode
import winsound
import unicodedata
import csv
from datetime import datetime

def conectar_banco():
    if not os.path.exists('banco_dados'):
        os.makedirs('banco_dados')
    conexao = sqlite3.connect('banco_dados/entradas.db')
    return conexao

def criar_tabela_entradas(conexao):
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_tutor TEXT,
            nome_dogs TEXT,
            hora_entrada TEXT,
            data_entrada DATE
        )
    ''')
    conexao.commit()

def registrar_entrada(conexao, nome_tutor, nome_dogs, hora_entrada, data_entrada):
    cursor = conexao.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM entradas
        WHERE nome_tutor = ? AND nome_dogs = ? AND data_entrada = ?
    ''', (nome_tutor, nome_dogs, data_entrada.strftime('%Y-%m-%d')))
    ja_existe = cursor.fetchone()[0] > 0

    if ja_existe:
        print(f"Já existe um registro de {nome_tutor} ({nome_dogs}) para hoje. Ignorando duplicado.")
        return False

    cursor.execute('''
        INSERT INTO entradas (nome_tutor, nome_dogs, hora_entrada, data_entrada)
        VALUES (?, ?, ?, ?)
    ''', (nome_tutor, nome_dogs, hora_entrada, data_entrada.strftime('%Y-%m-%d')))
    conexao.commit()
    return True

def processar_qr_code(data):
    linhas = [linha.strip() for linha in data.split("\n") if linha.strip()]
    nome_tutor = ""
    dogs = []
    dog_atual = None

    for linha in linhas:
        ln = unicodedata.normalize("NFKD", linha.lower())
        ln = ln.encode("ASCII", "ignore").decode()

        if ln.startswith("tutor:"):
            nome_tutor = linha.split(":", 1)[1].strip()

        elif ln.startswith("dog:"):
            if dog_atual:
                dogs.append(dog_atual)
            dog_atual = linha.split(":", 1)[1].strip()

        elif ln.startswith("raca:") or ln.startswith("raca:"):
            raca = linha.split(":", 1)[1].strip()
            if dog_atual:
                dog_atual = f"{dog_atual} (Raça: {raca})"

    if dog_atual:
        dogs.append(dog_atual)

    return nome_tutor, ', '.join(dogs)

def listar_entradas_do_dia(conexao, exibir=True):
    cursor = conexao.cursor()
    data_atual = datetime.now().date().strftime('%Y-%m-%d')

    cursor.execute('''
        SELECT id, nome_tutor, nome_dogs, hora_entrada
        FROM entradas
        WHERE data_entrada = ?
    ''', (data_atual,))
    entradas = cursor.fetchall()

    if exibir:
        if entradas:
            print(f"\nEntradas do dia {data_atual}:")
            for entrada in entradas:
                print(f"ID: {entrada[0]} | Tutor: {entrada[1]} | Dogs: {entrada[2]} | Hora: {entrada[3]}")
        else:
            print(f"\nNão há entradas registradas para o dia {data_atual}.")
    return entradas

def listar_todos_os_registros(conexao):
    cursor = conexao.cursor()
    cursor.execute('SELECT id, nome_tutor, nome_dogs, hora_entrada, data_entrada FROM entradas ORDER BY data_entrada DESC')
    registros = cursor.fetchall()

    if not registros:
        print("\nNenhum registro encontrado no histórico.")
        return

    print("\nHistórico completo de registros:\n")
    for r in registros:
        print(f"ID: {r[0]} | Tutor: {r[1]} | Dogs: {r[2]} | Hora: {r[3]} | Data: {r[4]}")
    print(f"\nTotal de registros: {len(registros)}")

def apagar_todos_os_dados(conexao):
    confirmacao = input("\nTem certeza que deseja apagar TODOS os dados? (s/n): ").strip().lower()
    if confirmacao == 's':
        cursor = conexao.cursor()
        cursor.execute('DELETE FROM entradas')
        conexao.commit()
        print("Todos os dados foram apagados!")
        exportar_para_csv(conexao)
    else:
        print("Ação cancelada.")

def apagar_registro_por_id(conexao):
    listar_entradas_do_dia(conexao)
    try:
        id_para_apagar = int(input("\nDigite o ID do registro que deseja apagar: ").strip())
        cursor = conexao.cursor()
        cursor.execute('SELECT * FROM entradas WHERE id = ?', (id_para_apagar,))
        registro = cursor.fetchone()

        if not registro:
            print("ID não encontrado.")
            return

        confirmacao = input(f"Tem certeza que deseja apagar o registro ID {id_para_apagar}? (s/n): ").strip().lower()
        if confirmacao == 's':
            cursor.execute('DELETE FROM entradas WHERE id = ?', (id_para_apagar,))
            conexao.commit()
            print(f"Registro ID {id_para_apagar} apagado com sucesso!")
            exportar_para_csv(conexao)
        else:
            print("Ação cancelada.")
    except ValueError:
        print("ID inválido. Digite apenas números.")

def listar_dogs_do_dia(conexao):
    cursor = conexao.cursor()
    hoje_sql = datetime.now().date().strftime('%Y-%m-%d')
    hoje_display = datetime.now().strftime('%d/%m/%Y')

    cursor.execute('SELECT nome_dogs FROM entradas WHERE data_entrada = ?', (hoje_sql,))
    registros = cursor.fetchall()

    dogs_lista = []
    for registro in registros:
        nomes = [n.strip() for n in registro[0].split(',') if n.strip()]
        for item in nomes:
            dogs_lista.append(item)

    if not dogs_lista:
        print(f"\nNenhum dog registrado hoje ({hoje_display}).")
        return

    print(f"\n`CHAMADA DO DIA — {hoje_display}:`\n")
    for i, dog in enumerate(dogs_lista, 1):
        print(f"{i}. {dog.upper()}")
    print(f"\n`TOTAL: {len(dogs_lista)}`")

def exportar_para_csv(conexao):
    entradas = listar_entradas_do_dia(conexao, exibir=False)

    if not os.path.exists('chamadas'):
        os.makedirs('chamadas')

    data_atual = datetime.now().strftime('%d-%m-%Y')
    nome_arquivo = f'chamadas/CHAMADA_DO_DIA_{data_atual}.csv'

    with open(nome_arquivo, 'w', newline='', encoding='utf-8') as csvfile:
        escritor = csv.writer(csvfile)
        escritor.writerow(['ID', 'Tutor', 'Dogs', 'Hora de Entrada'])

        for entrada in entradas:
            escritor.writerow(entrada)

    print(f"CSV atualizado: {nome_arquivo}")

def ler_qr_code_continuo(conexao):
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()

    print("\nIniciando leitura contínua... Pressione 'q' para sair.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        data, bbox, _ = detector.detectAndDecode(frame)

        if data:
            data = data.strip()
            try:
                nome_tutor, nome_dogs = processar_qr_code(data)
                hora_entrada = datetime.now().strftime('%H:%M:%S')
                data_entrada = datetime.now().date()

                if registrar_entrada(conexao, nome_tutor, nome_dogs, hora_entrada, data_entrada):
                    print(f"\nEntrada registrada: {nome_tutor} | {nome_dogs} | {hora_entrada}")
                    exportar_para_csv(conexao)
                    winsound.Beep(1500, 200)
                else:
                    winsound.Beep(800, 200)

            except Exception as e:
                print(f"Erro ao processar QR Code: {e}")

        cv2.imshow('Leitura de QR Code', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def exibir_menu():
    print("\n" + "═" * 55)
    print("SISTEMA DE REGISTRO DE ENTRADAS — MENU PRINCIPAL")
    print("═" * 55)

    print("\nLeitura e Registros")
    print("   1️  Iniciar leitura contínua do QR Code")
    print("   2️  Listar entradas de hoje")
    print("   3️  Listar apenas nomes dos dogs (Chamada)")
    print("   4️  Exportar chamada de hoje para CSV")

    print("\nGerenciamento de Dados")
    print("   5️  Apagar um registro específico")
    print("   6️  Apagar TODOS os dados")
    print("   7️  Listar todos os registros (Histórico completo)")

    print("\nFinalizar")
    print("   8️  Sair\n")

    print("═" * 55)

def main():
    conexao = conectar_banco()
    criar_tabela_entradas(conexao)

    exportar_para_csv(conexao)
    print("\nCSV do dia criado/atualizado automaticamente.\n")

    while True:
        exibir_menu()
        opcao = input("Escolha uma opção: ").strip()

        if opcao == '1':
            ler_qr_code_continuo(conexao)
        elif opcao == '2':
            listar_entradas_do_dia(conexao)
        elif opcao == '3':
            listar_dogs_do_dia(conexao)
        elif opcao == '4':
            exportar_para_csv(conexao)
        elif opcao == '5':
            apagar_registro_por_id(conexao)
        elif opcao == '6':
            apagar_todos_os_dados(conexao)
        elif opcao == '7':
            listar_todos_os_registros(conexao)
        elif opcao == '8':
            print("Encerrando o programa.")
            break
        else:
            print("Opção inválida!")

    conexao.close()

if __name__ == "__main__":
    main()
