import secrets
import psutil
import random
import socket
import threading
import json
import os
import platform
from itertools import zip_longest
import string


def gerar_senha():
    letras = string.ascii_letters
    senha = ''.join(random.choices(letras, k=3))
    return senha
def limpar_tela():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')


def ler_arquivo(nome_arquivo):
    try:
        with open(nome_arquivo, 'r') as arquivo:
            conteudo = arquivo.read()
            return conteudo
    except FileNotFoundError:
        return False


def escrever_arquivo(nome_arquivo, conteudo):
    try:
        with open(nome_arquivo, 'w') as arquivo:
            arquivo.write(conteudo)
        return True
    except FileNotFoundError:
        return False


import json

def gerar_grafico():
    dados = ler_arquivo('dados.json')
    dados = json.loads(dados)

    processo = {}
    processos = []
    nodes = []

    ultimo_evento_processo = {}
    eventos = {}
    mensagem = 0
    edges = []

    evento = 0

    for indice, dado in enumerate(dados):

        nome_processo = dado[0]
        evento_id = dado[1]
        vetor = dado[2]

        if nome_processo not in processos:
            evento += 1
            processo[nome_processo] = len(processos)

            nodes.append({
                "id": evento,
                "label": nome_processo,
                "x": 0,
                "y": processo[nome_processo] * 100,
                "fixed": True,
                "color": "#ffffff",
                "borderWidth": 0
            })

            ultimo_evento_processo[nome_processo] = evento
            processos.append(nome_processo)

        evento += 1
        nodes.append({
            "id": evento,
            "label": f"{str(vetor)}\n{evento_id}",
            "x": evento * 100,
            "y": processo[nome_processo] * 100,
            "fixed": True,
            "shape": "dot",
            "size": 10
        })

        if len(dado) > 3:
            env = eventos[dado[3]]
            mensagem += 1
            edges.append({"from": env, "to": evento, "label": 'm' + str(mensagem), "arrows": 'to'})

        eventos[evento_id] = evento

        edges.append({"from": ultimo_evento_processo[nome_processo], "to": evento})

        ultimo_evento_processo[nome_processo] = evento

    data = {
        "nodes": nodes,
        "edges": edges,
    }

    data = json.dumps(data)

    dados = ler_arquivo('modelo.html')
    dados = dados.replace("#jsonString", data)
    escrever_arquivo('Gráfico de FLuxo.html', dados)

    return 'Gráfico criado com sucesso!'


def limpar_dados():
    escrever_arquivo('dados.json', '')
    #escrever_arquivo('processos.json', '{}')
    return 'Dados apagados com sucesso!'


def e_json(json_str):
    try:
        lista = json.loads(json_str)
        return lista
    except json.decoder.JSONDecodeError:
        return False


def selecionar_porta_disponivel_aleatoria():
    conexoes = psutil.net_connections(kind='inet')
    portas = set(range(1, 65536))
    portas_usadas = {conn.laddr.port for conn in conexoes}
    portas_disponiveis = portas - portas_usadas
    if portas_disponiveis:
        porta_disponivel_aleatoria = random.choice(list(portas_disponiveis))
        return porta_disponivel_aleatoria
    else:
        return False


class Processo:
    def __init__(self):
        self.processos = []
        self.nome_processo = ''
        self.numero_processo = 0
        self.eventos = []
        self.vetor = []
        self.sair = False

    def criar_servidor(self):
        ip = "0.0.0.0"
        porta = selecionar_porta_disponivel_aleatoria()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((ip, porta))
        server.listen(5)
        with open('processos.json', 'r') as arquivo:
            processos = json.load(arquivo)
            with open('processos.json', 'w') as f:
                quantidade_processos = len(processos)
                numero_processo_atual = quantidade_processos + 1
                self.numero_processo = numero_processo_atual - 1
                self.nome_processo = f'processo{numero_processo_atual}'
                processos[self.nome_processo] = porta
                json.dump(processos, f)

        while not self.sair:
            cliente, endereço = server.accept()
            requisicao = cliente.recv(1024)
            vetor_recebido = requisicao.decode('utf-8')
            print('\033[32m' + 'vetor recebido -> ' + str(json.loads(vetor_recebido)[0]) + '\033[0;0m')  # verdade
            print('\033[36m' + 'vetor atual -> ' + str(self.vetor) + '\033[0;0m')  # azul
            vetor_resultante = [a + b for a, b in zip_longest(json.loads(vetor_recebido)[0], self.vetor, fillvalue=0)]

            if self.vetor:
                novo_vetor = json.loads(vetor_recebido)[0]
            else:
                novo_vetor = [a + b for a, b in zip_longest(vetor_resultante, self.vetor, fillvalue=0)]
            self.atualizar_vetor(novo_vetor=novo_vetor, msg=True, evento_id=json.loads(vetor_recebido)[1])
            print('\033[31m' + 'vetor atualizado -> ' + str(self.vetor) + '\033[0;0m')  # vermelho

            cliente.send(str(self.vetor).encode('utf-8'))

            cliente.close()

    def criar_evento(self, menu=True, evento_id_cliente=False):
        evento_id = gerar_senha()
        self.eventos.append(evento_id)
        if menu:
            self.atualizar_vetor(local=True)
        dJson = ler_arquivo('dados.json')
        if dJson != False:
            dados = e_json(dJson)
            dado = [self.nome_processo, evento_id, self.vetor]
            if evento_id_cliente:
                dado.append(evento_id_cliente)
            if dados:
                dados.append(dado)
            else:
                dados = [dado]
            escrever_arquivo('dados.json', json.dumps(dados))
        return [evento_id, f"Evento '{evento_id}' criado com sucesso"]

    def ver_eventos(self):
        lista_eventos = ''
        for i, item in enumerate(self.eventos):
            lista_eventos += f'{i + 1}. {item}\n'
        return lista_eventos

    def atualizar_vetor(self, novo_vetor=None, local=False, msg=False, evento_id=False):
        vetor_incremento = [0] * (self.numero_processo + 1)
        vetor_incremento[self.numero_processo] = 1
        if local:
            self.vetor = [a + b for a, b in zip_longest(self.vetor, vetor_incremento, fillvalue=0)]
        else:
            self.vetor = [a + b for a, b in zip_longest(novo_vetor, vetor_incremento, fillvalue=0)]
        if msg:
            if evento_id:
                return self.criar_evento(menu=False, evento_id_cliente=evento_id)[0]
                # self.criar_evento(menu=False, evento_id=evento_id)
            else:
                return self.criar_evento(menu=False)[0]

    def cliente(self, port, evento_id, host="localhost"):
        try:
            dados_string = json.dumps([self.vetor, evento_id])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.sendall(bytes(dados_string, encoding="utf-8"))
            dados_recebidos = sock.recv(1024).decode("utf-8")
            if dados_recebidos:
                print('\033[33m' + 'vetor enviado -> ' + str(self.vetor) + '\033[0;0m')  # amarelo

        finally:
            sock.close()

    def enviar_mensagem(self):
        with open('processos.json', 'r') as arquivo:
            processos = json.load(arquivo)
            del processos[self.nome_processo]
            if processos:
                processo_aleatorio = random.choice(list(processos.keys()))
                porta = processos[processo_aleatorio]
                evento_id = self.atualizar_vetor(local=True, msg=True)
                self.cliente(port=porta, evento_id=evento_id)
            else:
                print('Nenhum processo disponível')

    def menu_principal(self):
        while True:
            try:
                opcao = int(input(
                    f'1. Criar evento\n2.Ver eventos\n3. Ver vetor\n4. Enviar mensagem\n5.Limpar dados\n6.Gerar gráfico\n0. Sair\n'))
                if opcao < 0 or opcao > 6:
                    limpar_tela()
                    raise ValueError("Por favor, escolha um número entre 0 e 4.\n")
            except:
                limpar_tela()
                print("Por favor, escolha um número entre 0 e 4.\n")
                continue

            if opcao == 1:
                print(self.criar_evento()[1])
            elif opcao == 2:
                print(self.eventos)
            elif opcao == 3:
                print(self.vetor)
            elif opcao == 4:
                self.enviar_mensagem()
            elif opcao == 5:
                print(limpar_dados())
            elif opcao == 6:
                print(gerar_grafico())
            elif opcao == 0:
                with open('processos.json', 'r') as arquivo:
                    processos = json.load(arquivo)
                    if self.nome_processo in processos:
                        del processos[self.nome_processo]
                    with open('processos.json', 'w') as arquivo:
                        json.dump(processos, arquivo)
                limpar_tela()
                print('Processo finalizado e removido do registro\nFeche a janela.')
                break

    def iniciar_servidor(self):
        servidor = threading.Thread(target=self.criar_servidor)
        servidor.start()


p1 = Processo()
p1.iniciar_servidor()
p1.menu_principal()
