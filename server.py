#!/usr/bin/env python3
import os
import sys
import signal
import atexit

class FIFOServer:
    def __init__(self):
        self.running = True
        self.fifo_request = "/tmp/ping_pong_request"
        self.fifo_response = "/tmp/ping_pong_response"
        self.current_client = None
        
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
        for fifo in [self.fifo_request, self.fifo_response]:
            if os.path.exists(fifo):
                try:
                    os.unlink(fifo)
                    print(f"Удален FIFO: {fifo}")
                except Exception as e:
                    print(f"Ошибка удаления {fifo}: {e}")
    
    def create_fifos(self):
        """Создание FIFO каналов"""
        self.cleanup()
        try:
            os.mkfifo(self.fifo_request)
            os.mkfifo(self.fifo_response)
            print(f"Созданы FIFO:")
            print(f"  Запросы:  {self.fifo_request}")
            print(f"  Ответы:   {self.fifo_response}")
            return True
        except Exception as e:
            print(f"Ошибка создания FIFO: {e}")
            return False
    
    def process_message(self, message):
        # Регистрация нового клиента
        if message.startswith("CONNECT:"):
            client_name = message[8:].strip()
            self.current_client = client_name
            return "OK", False, True, False 
        # Отключение
        if message.upper() == "DISCONNECT":
            return "OK", True, False, False
        
        # Завершение сервера
        if message.upper() == "SHUTDOWN":
            return "OK", True, False, True
        
        # Обычные команды
        if message.lower() == "ping":
            return "pong", False, False, False
        elif message.lower() == "пинг":
            return "понг", False, False, False
        else:
            print(f"[Ошибка] Неизвестная команда: '{message}'")
            return "ERROR: Unknown command", False, False, False
    
    def run(self):
        """Запуск сервера"""
        if not self.create_fifos():
            return
        
        print("Сервер запущен. Ожидание подключений...")
        
        try:
            while self.running:
                # Состояние 1: Ожидание запроса
                print("\n[Ожидание запроса]")
                
                try:
                    with open(self.fifo_request, 'r') as f:
                        message = f.read().strip()
                except Exception as e:
                    print(f"Ошибка чтения: {e}")
                    continue
                
                if not message:
                    continue
                response, disconnect, is_connect, shutdown = self.process_message(message)
                
                if is_connect:
                    print(f"[+] Клиент '{self.current_client}' подключился")
                    print("[Обработка запроса]")
                else:
                    print(f"Получено: '{message}'")
                    print("[Обработка запроса]")
                print(f"[Отправка ответа] -> '{response}'")
                
                try:
                    with open(self.fifo_response, 'w') as f:
                        f.write(response)
                except Exception as e:
                    print(f"Ошибка отправки: {e}")
                
                if shutdown:
                    print(f"[-] Клиент '{self.current_client}' завершил работу сервера")
                    self.running = False
                    break
                
                if disconnect:
                    print(f"[-] Клиент '{self.current_client}' отключился")
                    self.current_client = None
                    print("\nОжидание нового подключения...")
                    
        except Exception as e:
            if self.running:
                print(f"Ошибка в основном цикле сервера: {e}")
        finally:
            self.cleanup()
            print("Сервер завершил работу")


if __name__ == "__main__":
    server = FIFOServer()
    server.run()
