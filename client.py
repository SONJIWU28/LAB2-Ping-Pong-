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
        self.fifo_main = "/tmp/ping_pong_main"
        self.fifo_request = None
        self.fifo_response = None
        
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
            if os.path.exists(self.fifo_main):
                return True
            time.sleep(0.1)
        
        return False
    
    def send_message(self, message):
        """Отправка сообщения серверу"""
        if not os.path.exists(self.fifo_request):
            return False
        try:
            with open(self.fifo_request, 'w') as f:
                f.write(message)
            return True
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            return False
    
    def receive_response(self):
        """Получение ответа от сервера"""
        if not os.path.exists(self.fifo_response):
            return None
        try:
            with open(self.fifo_response, 'r') as f:
                response = f.read().strip()
            return response
        except Exception as e:
            return None
    
    def connect(self):
        """Подключение к серверу"""
        if not self.wait_for_server():
            print("Ошибка: Сервер не запущен")
            return False
        
        # Устанавливаем пути к персональным FIFO
        self.fifo_request = f"/tmp/ping_pong_{self.client_name}_req"
        self.fifo_response = f"/tmp/ping_pong_{self.client_name}_resp"
        
        # Отправляем имя для регистрации
        print(f"Регистрация как '{self.client_name}'...")
        
        try:
            with open(self.fifo_main, 'w') as f:
                f.write(self.client_name)
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            return False
        
        # Ждём создания персональных FIFO
        timeout = 5
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(self.fifo_request) and os.path.exists(self.fifo_response):
                break
            time.sleep(0.1)
        else:
            print("Ошибка: Сервер не создал каналы")
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
        
        self.connected = False
        self.running = False
            
        try:
            if self.fifo_request and os.path.exists(self.fifo_request):
                with open(self.fifo_request, 'w') as f:
                    f.write("DISCONNECT")
        except:
            pass
    
    def run(self):
        """Запуск клиента"""
        self.client_name = self.get_client_name()
        
        if not self.connect():
            return
        
        print("\nВведите 'ping' или 'пинг' (exit - выход)")
        
        try:
            while self.running:
                message = input("\nВведите сообщение: ").strip()
                
                if not self.running:
                    break
                
                if not message:
                    continue
                
                if message.lower() == 'exit':
                    break
                
                # Состояние 1: Отправка запроса
                print(f"[Отправка запроса] -> '{message}'")
                
                if not self.send_message(message):
                    # Сервер отключился
                    print("Сервер отключился")
                    self.connected = False
                    break
                
                # Состояние 2: Ожидание ответа
                print("[Ожидание ответа]")
                
                response = self.receive_response()
                
                if response is None:
                    # Сервер отключился
                    print("Сервер отключился")
                    self.connected = False
                    break
                
                # Состояние 3: Получение ответа
                print(f"[Получен ответ] <- '{response}'")
                    
        except (EOFError, KeyboardInterrupt):
            print("\nЗавершение работы...")
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            self.disconnect()
            print("Сеанс завершён")


if __name__ == "__main__":
    client = FIFOClient()
    client.run()
