#!/usr/bin/env python3
import os
import sys
import signal
import atexit
import threading

class FIFOServer:
    def __init__(self):
        self.running = True
        self.fifo_main = "/tmp/ping_pong_main"
        self.clients = {}
        self.lock = threading.Lock()
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        atexit.register(self.cleanup)
    
    def signal_handler(self, signum, frame):
        print("\nСервер завершает работу...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Очистка FIFO файлов"""
        print("Очистка FIFO файлов...")
        # Удаляем главный FIFO
        if os.path.exists(self.fifo_main):
            try:
                os.unlink(self.fifo_main)
                print(f"Удален FIFO: {self.fifo_main}")
            except Exception as e:
                print(f"Ошибка удаления {self.fifo_main}: {e}")
        
        # Удаляем все клиентские FIFO
        import glob
        for fifo in glob.glob("/tmp/ping_pong_*"):
            try:
                os.unlink(fifo)
                print(f"Удален FIFO: {fifo}")
            except:
                pass
    
    def create_fifos(self):
        """Создание главного FIFO канала"""
        self.cleanup()
        try:
            os.mkfifo(self.fifo_main)
            print(f"Создан FIFO: {self.fifo_main}")
            return True
        except Exception as e:
            print(f"Ошибка создания FIFO: {e}")
            return False
    
    def process_message(self, message):
        if message.lower() == "ping":
            return "pong"
        elif message.lower() == "пинг":
            return "понг"
        else:
            return "ERROR: Unknown command"
    
    def handle_client(self, client_name):
        """Обработка клиента в отдельном потоке"""
        fifo_request = f"/tmp/ping_pong_{client_name}_req"
        fifo_response = f"/tmp/ping_pong_{client_name}_resp"
        try:
            os.mkfifo(fifo_request)
            os.mkfifo(fifo_response)
        except:
            return
        
        print(f"\n[+] Клиент '{client_name}' подключился")
        
        try:
            while self.running:
                # Состояние 1: Ожидание запроса
                try:
                    with open(fifo_request, 'r') as f:
                        message = f.read().strip()
                except:
                    break
                
                if not message:
                    continue
                
                if message.upper() == "DISCONNECT":
                    break
                
                print(f"[{client_name}] Получено: '{message}'")
                print(f"[{client_name}] [Обработка запроса]")
                
                response = self.process_message(message)
                
                print(f"[{client_name}] [Отправка ответа] -> '{response}'")
                
                try:
                    with open(fifo_response, 'w') as f:
                        f.write(response)
                except:
                    break
                    
        finally:
            # Очистка
            for fifo in [fifo_request, fifo_response]:
                if os.path.exists(fifo):
                    try:
                        os.unlink(fifo)
                    except:
                        pass
            
            with self.lock:
                if client_name in self.clients:
                    del self.clients[client_name]
            
            print(f"[-] Клиент '{client_name}' отключился")
    
    def run(self):
        """Запуск сервера"""
        if not self.create_fifos():
            return
        
        print("Сервер запущен. Ожидание подключений...")
        
        try:
            while self.running:
                print("\n[Ожидание подключения]")
                
                try:
                    with open(self.fifo_main, 'r') as f:
                        client_name = f.read().strip()
                except Exception as e:
                    if self.running:
                        print(f"Ошибка чтения: {e}")
                    continue
                
                if not client_name:
                    continue
                
                with self.lock:
                    if client_name in self.clients:
                        print(f"[!] Клиент '{client_name}' уже подключен")
                        continue
                    
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_name,),
                        daemon=True
                    )
                    self.clients[client_name] = thread
                    thread.start()
                    
        except Exception as e:
            if self.running:
                print(f"Ошибка в основном цикле сервера: {e}")
        finally:
            self.cleanup()
            print("Сервер завершил работу")


if __name__ == "__main__":
    server = FIFOServer()
    server.run()
