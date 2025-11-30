#!/usr/bin/env python3
import os
import sys
import signal
import time

class FIFOClient:
    def __init__(self):
        self.running = True
        self.connected = False
        self.client_name = None
        self.fifo_request = "/tmp/ping_pong_request"
        self.fifo_response = "/tmp/ping_pong_response"
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        print("\nЗавершение работы клиента...")
        self.running = False
        self.disconnect()
        sys.exit(0)
    
    def get_client_name(self):
        """Запрос имени клиента"""
        while True:
            name = input("Введите ваше имя: ").strip()
            if not name:
                print("Имя не может быть пустым")
                continue
            if ' ' in name:
                print("Имя не должно содержать пробелов")
                continue
            
            return name
    
    def wait_for_server(self, timeout=5):
        """Ожидание запуска сервера"""
        print("Подключение к серверу...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(self.fifo_request) and os.path.exists(self.fifo_response):
                return True
            time.sleep(0.1)
        
        return False
    
    def send_message(self, message):
        """Отправка сообщения серверу"""
        try:
            with open(self.fifo_request, 'w') as f:
                f.write(message)
            return True
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            return False
    
    def receive_response(self):
        """Получение ответа от сервера"""
        try:
            with open(self.fifo_response, 'r') as f:
                response = f.read().strip()
            return response
        except Exception as e:
            print(f"Ошибка получения ответа: {e}")
            return None
    
    def connect(self):
        """Подключение к серверу"""
        if not self.wait_for_server():
            print("Ошибка: Сервер не запущен")
            return False
        
        # Отправляем имя для регистрации
        print(f"Регистрация как '{self.client_name}'...")
        
        if not self.send_message(f"CONNECT:{self.client_name}"):
            return False
        
        response = self.receive_response()
        
        if response != "OK":
            print(f"Ошибка: Не удалось подключиться ({response})")
            return False
        
        print(f"Успешно подключено к серверу!")
        print(f"  Запросы:  {self.fifo_request}")
        print(f"  Ответы:   {self.fifo_response}")
        
        self.connected = True
        return True
    
    def disconnect(self):
        """Отключение от сервера"""
        if not self.connected:
            return
            
        try:
            if os.path.exists(self.fifo_request):
                with open(self.fifo_request, 'w') as f:
                    f.write("DISCONNECT")
                if os.path.exists(self.fifo_response):
                    with open(self.fifo_response, 'r') as f:
                        f.read()
        except:
            pass
        
        self.connected = False
        self.running = False
    
    def run(self):
        """Запуск клиента"""
        self.client_name = self.get_client_name()
        
        if not self.connect():
            return
        
        print("\nВведите 'ping' или 'пинг' (exit - выход, shutdown - завершить сервер)")
        
        try:
            while self.running:
                message = input("\nВведите сообщение: ").strip()
                
                if not self.running:
                    break
                
                if not message:
                    continue
                
                if message.lower() == 'exit':
                    break
                
                if message.lower() == 'shutdown':
                    print("[Отправка запроса] -> 'SHUTDOWN'")
                    self.send_message("SHUTDOWN")
                    self.receive_response()
                    print("Сервер завершён")
                    self.connected = False
                    break
                
                # Состояние 1: Отправка запроса
                print(f"[Отправка запроса] -> '{message}'")
                
                if not self.send_message(message):
                    # Состояние 4: Обработка ошибки
                    print("[Ошибка] Не удалось отправить сообщение")
                    continue
                
                # Состояние 2: Ожидание ответа
                print("[Ожидание ответа]")
                
                response = self.receive_response()
                
                if response is None:
                    # Состояние 4: Обработка ошибки
                    print("[Ошибка] Не удалось получить ответ")
                    continue
                
                # Состояние 3: Получение ответа
                print(f"[Получен ответ] <- '{response}'")
                    
        except (EOFError, KeyboardInterrupt):
            print("\nЗавершение работы...")
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            self.disconnect()
            print("Клиент завершил работу")


if __name__ == "__main__":
    client = FIFOClient()
    client.run()
