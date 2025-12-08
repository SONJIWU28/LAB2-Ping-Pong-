#!/bin/bash
clear
qemu-system-aarch64 \
  -M virt \
  -cpu cortex-a57 \
  -m 256 \
  -nographic \
  -bios QEMU_EFI.fd \
  -cdrom alpine-virt-3.19.0-aarch64.iso \
  -virtfs local,path=shared,mount_tag=shared,security_model=none \
  -netdev user,id=net0,hostfwd=tcp::8000-:8000 \
  -device virtio-net-device,netdev=net0
