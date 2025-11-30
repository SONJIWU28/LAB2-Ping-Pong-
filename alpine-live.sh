#!/bin/bash
# Установка
sudo apt update
sudo apt install -y qemu-system-arm qemu-efi-aarch64 wget

# Папка
WORKDIR="$HOME/alpine-arm-live"
mkdir -p "$WORKDIR/shared"
cd "$WORKDIR"

# Скачивание Alpine
if [ ! -f "alpine-virt-3.19.0-aarch64.iso" ]; then
    wget -q --show-progress \
        https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/aarch64/alpine-virt-3.19.0-aarch64.iso
fi

# UEFI
cp /usr/share/qemu-efi-aarch64/QEMU_EFI.fd . 2>/dev/null

# Скрипт запуска с СЕТЬЮ
cat > run.sh << 'SCRIPT'
#!/bin/bash
clear
echo "Alpine Linux ARM - Live режим"
echo ""
echo ""
qemu-system-aarch64 \
  -M virt \
  -cpu cortex-a57 \
  -m 256 \
  -nographic \
  -bios QEMU_EFI.fd \
  -cdrom alpine-virt-3.19.0-aarch64.iso \
  -virtfs local,path=shared,mount_tag=shared,security_model=none \
  -netdev user,id=net0 \
  -device virtio-net-device,netdev=net0
SCRIPT

chmod +x run.sh
cat > shared/КОМАНДЫ.txt << 'EOF'
КОМАНДЫ В ALPINE:
=================

1. Логин: root 

2. Настройка сети:
   setup-interfaces -a
   rc-service networking start
3. Установка Python:
   apk add python3
4. Монтирование:
   mkdir /mnt/shared
   mount -t 9p -o trans=virtio shared /mnt/shared
5. Запуск:
   cd /mnt/shared
   python3 linux_server.py
Проверка ARM: uname -m
Выход: Ctrl+A, X
EOF

