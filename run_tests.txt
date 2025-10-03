#!/bin/bash
# Скрипт для тестирования всех параметров

echo "=== Тест 1: Запуск без параметров ==="
python emulator.py

echo -e "\n=== Тест 2: Запуск с указанием только VFS ==="
python emulator.py /virtual/vfs

echo -e "\n=== Тест 3: Запуск с VFS и скриптом ==="
python emulator.py /virtual/vfs test_script1.sh

echo -e "\n=== Тест 4: Запуск с ошибочным скриптом ==="
python emulator.py /virtual/vfs test_script2.sh

echo -e "\n=== Тест 5: Запуск со скриптом работы с файлами ==="
python emulator.py /virtual/vfs test_script3.sh