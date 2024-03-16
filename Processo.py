import secrets
import psutil
import random
import socket
import threading
import json
import os
import platform
from itertools import zip_longest


class Processo:
    def __init__(self):
        self.processos = []
        self.nome_processo = ''
        self.numero_processo = 0
        self.eventos = []
        self.vetor = []
        self.sair = False
        
    def limpar_tela(self):
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
        
    def selecionar_porta_disponivel_aleatoria(self):
        conexoes = psutil.net_connections(kind='inet')
        portas = set(range(1, 65536))
        portas_usadas = {conn.laddr.port for conn in conexoes}
        portas_disponiveis = portas - portas_usadas
        if portas_disponiveis:
            porta_disponivel_aleatoria = random.choice(list(portas_disponiveis))
            return porta_disponivel_aleatoria
        else:
            return False

    def criar_servidor(self):
        ip = "0.0.0.0"
        porta = self.selecionar_porta_disponivel_aleatoria()

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
            print ('\033[32m'+'vetor recebido -> '+vetor_recebido+'\033[0;0m') #verdade
            print ('\033[36m'+'vetor atual -> '+str(self.vetor)+'\033[0;0m') #azul
            vetor_resultante = [a + b for a, b in zip_longest(json.loads(vetor_recebido), self.vetor, fillvalue=0)]
            
            if self.vetor:
                novo_vetor = json.loads(vetor_recebido)
            else:
                novo_vetor = [a + b for a, b in zip_longest(vetor_resultante, self.vetor, fillvalue=0)]
            self.atualizar_vetor(novo_vetor=novo_vetor)
            
            print ('\033[31m'+'vetor atualizado -> '+str(self.vetor)+'\033[0;0m') #vermelho

            cliente.send(requisicao)
            cliente.close()
            
    def criar_evento(self):
        evento_id = secrets.token_hex(8)
        self.eventos.append(evento_id)
        self.atualizar_vetor(local = True)
        return f"Evento '{evento_id}' criado com sucesso"

    def ver_eventos(self):
        lista_eventos = ''
        for i, item in enumerate(self.eventos):
            lista_eventos += f'{i+1}. {item}\n'
        return lista_eventos

    def atualizar_vetor (self, novo_vetor = None, local = False):
        vetor_incremento = [0] * (self.numero_processo + 1)
        vetor_incremento[self.numero_processo] = 1
        if local:
            self.vetor = [a + b for a, b in zip_longest(self.vetor, vetor_incremento, fillvalue=0)]
        else:
            self.vetor = [a + b for a, b in zip_longest(novo_vetor, vetor_incremento, fillvalue=0)]
           
        
    def cliente(self, port, host="localhost"):
        try:
            dados_string = json.dumps(self.vetor)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.sendall(bytes(dados_string, encoding="utf-8"))
            dados_recebidos = sock.recv(1024).decode("utf-8")
            if(dados_recebidos):
                print ('\033[33m'+'vetor enviado -> '+str(self.vetor)+'\033[0;0m') #amarelo

        finally:
            sock.close()
            
    def enviar_mensagem(self):
        with open('processos.json', 'r') as arquivo:
            processos = json.load(arquivo)
            del processos[self.nome_processo]
            if processos:
                processo_aleatorio = random.choice(list(processos.keys()))
                porta = processos[processo_aleatorio]
         
                self.atualizar_vetor (local = True)
                self.cliente(port=porta)
            else:
                print('Nenhum processo disponível')

    def menu_principal(self):
        while True:
            try:
                opcao = int(input(f'1. Criar evento\n2.Ver eventos\n3. Ver vetor\n4. Enviar mensagem\n0. Sair\n'))
                if opcao < 0 or opcao > 4:
                    self.limpar_tela()
                    raise ValueError("Por favor, escolha um número entre 0 e 4.\n")
            except:
                self.limpar_tela()
                print("Por favor, escolha um número entre 0 e 4.\n")
                continue

            if opcao == 1:
                print(self.criar_evento())
            elif opcao == 2:
                print(self.eventos)
            elif opcao == 3:
                print(self.vetor)
            elif opcao == 4:
                self.enviar_mensagem()
            elif opcao == 0:
                with open('processos.json', 'r') as arquivo:
                    processos = json.load(arquivo)
                    if self.nome_processo in processos:
                        del processos[self.nome_processo]
                    with open('processos.json', 'w') as arquivo:
                        json.dump(processos, arquivo)
                self.limpar_tela()
                print('Processo finalizado e removido do registro\nFeche a janela.')
                break

                
        
    def iniciar_servidor(self):
        servidor = threading.Thread(target=self.criar_servidor)
        servidor.start()


p1 = Processo()
p1.iniciar_servidor()
p1.menu_principal()
