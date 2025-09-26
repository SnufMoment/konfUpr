import os
import sys
import shlex
from typing import List, Dict, Optional


class VirtualFileSystem:

    def __init__(self, vfs_path: str = None):
        self.root = {}
        self.current_path = '/'
        self.vfs_path = vfs_path  # используется только для информации, не для реальных файлов
        self._init_default_structure()

    def _init_default_structure(self):
        self.root['/'] = {}
        self.root['/']['home'] = {}
        self.root['/']['home'][self._get_real_username()] = {}
        self.root['/']['bin'] = {}
        self.root['/']['bin']['ls'] = "executable"
        self.root['/']['bin']['cd'] = "executable"
        self.root['/']['bin']['pwd'] = "executable"
        self.root['/']['etc'] = {}
        self.root['/']['etc']['passwd'] = "root:x:0:0:root:/root:/bin/bash\nuser:x:1000:1000:user:/home/user:/bin/bash"
        self.root['/']['etc']['hosts'] = "127.0.0.1 localhost\n::1 localhost"
        self.root['/']['tmp'] = {}
        self.current_path = f"/home/{self._get_real_username()}"

    def _get_real_username(self) -> str:
        """Получает реальное имя пользователя системы"""
        username = os.getenv('USER')
        if not username:
            username = os.getenv('USERNAME')
        if not username:
            username = os.getenv('LOGNAME')
        if not username:
            username = 'user'
        return username

    def get_current_dir(self) -> Dict:
        path_parts = [p for p in self.current_path.split('/') if p]
        current = self.root['/']
        for part in path_parts:
            if part not in current:
                return {}
            current = current[part]
        return current

    def change_directory(self, path: str) -> bool:
        if path == '~':
            path = f"/home/{self._get_real_username()}"
        elif path == '.':
            return True
        elif path == '..':
            if self.current_path == '/':
                return True
            parts = self.current_path.split('/')
            if len(parts) <= 2:
                self.current_path = '/'
            else:
                self.current_path = '/'.join(parts[:-1]) or '/'
            return True

        if path.startswith('/'):
            target = path
        else:
            target = f"{self.current_path}/{path}" if self.current_path != '/' else f"/{path}"

        parts = [p for p in target.split('/') if p]
        current = self.root['/']

        for i, part in enumerate(parts):
            if part not in current:
                return False
            current = current[part]
            if i == len(parts) - 1 and not isinstance(current, dict):
                return False

        self.current_path = target
        return True

    def list_directory(self) -> List[str]:
        current_dir = self.get_current_dir()
        return sorted(current_dir.keys()) if isinstance(current_dir, dict) else []

    def get_prompt(self) -> str:
        username = self._get_real_username()
        hostname = os.getenv('HOSTNAME', 'localhost')
        display_path = self.current_path
        home_path = f"/home/{username}"
        if self.current_path == home_path:
            display_path = '~'
        elif self.current_path.startswith(home_path + '/'):
            display_path = '~' + self.current_path[len(home_path):]

        return f"{username}@{hostname}:{display_path}$ "


class ShellEmulator:
    def __init__(self, vfs_path: str = None, script_path: str = None):
        self.vfs = VirtualFileSystem(vfs_path)
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.commands = {
            'ls': self._cmd_ls,
            'cd': self._cmd_cd,
            'exit': self._cmd_exit,
            'pwd': self._cmd_pwd,
            'cat': self._cmd_cat,
        }

    def parse_command(self, line: str) -> tuple[str, List[str]]:
        try:
            tokens = shlex.split(line)
            if not tokens:
                return '', []
            cmd = tokens[0]
            args = tokens[1:]
            return cmd, args
        except ValueError as e:
            raise ValueError(f"Ошибка парсинга: {e}")

    def execute_command(self, cmd: str, args: List[str]) -> bool:
        if not cmd:
            return True

        if cmd not in self.commands:
            raise ValueError(f"{cmd}: команда не найдена")

        return self.commands[cmd](args)

    def _cmd_ls(self, args: List[str]) -> bool:
        if args:
            # Проверяем, если указан путь
            if len(args) == 1:
                path = args[0]
                if path.startswith('/'):
                    target_path = path
                else:
                    target_path = f"{self.vfs.current_path}/{path}" if self.vfs.current_path != '/' else f"/{path}"

                # Для простоты реализации просто покажем содержимое текущей директории
                # В реальной реализации нужно было бы перейти по указанному пути
                pass
            elif len(args) > 1:
                raise ValueError(f"ls: неподдерживаемые аргументы: {' '.join(args)}")

        files = self.vfs.list_directory()
        for f in files:
            print(f)
        return True

    def _cmd_cd(self, args: List[str]) -> bool:
        if len(args) > 1:
            raise ValueError("cd: слишком много аргументов")
        if len(args) == 0:
            success = self.vfs.change_directory('~')
        else:
            success = self.vfs.change_directory(args[0])
        if not success:
            raise ValueError(f"cd: нет такого каталога: {args[0] if args else ''}")
        return True

    def _cmd_exit(self, args: List[str]) -> bool:
        if args:
            raise ValueError(f"exit: неподдерживаемые аргументы: {' '.join(args)}")
        print("Выход...")
        return False

    def _cmd_pwd(self, args: List[str]) -> bool:
        if args:
            raise ValueError(f"pwd: неподдерживаемые аргументы: {' '.join(args)}")
        print(self.vfs.current_path)
        return True

    def _cmd_cat(self, args: List[str]) -> bool:
        if len(args) != 1:
            raise ValueError("cat: требуется один аргумент")

        path = args[0]
        # Для простоты поддерживаем только файлы в /etc
        if path in ['/etc/passwd', '/etc/hosts']:
            if path == '/etc/passwd':
                print("root:x:0:0:root:/root:/bin/bash")
                print("user:x:1000:1000:user:/home/user:/bin/bash")
            elif path == '/etc/hosts':
                print("127.0.0.1 localhost")
                print("::1 localhost")
        else:
            raise ValueError(f"cat: {path}: Нет такого файла или каталога")
        return True

    def run_script(self) -> bool:
        """Выполняет стартовый скрипт"""
        if not self.script_path:
            return False

        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Отображаем команду как будто пользователь ввел её
                prompt = self.vfs.get_prompt()
                print(f"{prompt} {line}")

                try:
                    cmd, args = self.parse_command(line)
                    if not self.execute_command(cmd, args):
                        return True  # exit command
                except Exception as e:
                    print(f"{e}")
                    print(f"Ошибка в скрипте {self.script_path} на строке {line_num}: {line}")
                    return False  # Останавливаемся при первой ошибке

        except FileNotFoundError:
            print(f"Ошибка: файл скрипта не найден: {self.script_path}")
            return False
        except Exception as e:
            print(f"Ошибка при выполнении скрипта: {e}")
            return False

        return True

    def run(self):
        # Отладочный вывод параметров
        print("Эмулятор оболочки UNIX (Этап 2)")
        print(f"VFS путь: {self.vfs_path or 'по умолчанию'}")
        print(f"Скрипт: {self.script_path or 'не задан'}")
        print("Введите 'exit' для выхода.\n")

        # Если задан скрипт, выполняем его
        if self.script_path:
            success = self.run_script()
            if not success:
                return  # Завершаем работу при ошибке в скрипте

        # Интерактивный режим
        while True:
            prompt = self.vfs.get_prompt()
            try:
                line = input(prompt).strip()
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue

            if not line:
                continue

            try:
                cmd, args = self.parse_command(line)
                if not self.execute_command(cmd, args):
                    break
            except Exception as e:
                print(f"{e}")
                sys.stdout.flush()
                continue


def print_usage():
    """Выводит информацию об использовании"""
    print("Использование:")
    print("  python emulator.py [vfs_path] [script_path]")
    print("  vfs_path   - путь к физическому расположению VFS (используется только для информации)")
    print("  script_path - путь к стартовому скрипту")
    print("\nПримеры:")
    print("  python emulator.py")
    print("  python emulator.py /tmp/vfs_test")
    print("  python emulator.py /tmp/vfs_test test_script1.sh")


def main():
    # Обработка аргументов командной строки
    vfs_path = None
    script_path = None

    if len(sys.argv) > 3:
        print("Слишком много аргументов")
        print_usage()
        sys.exit(1)
    elif len(sys.argv) >= 2:
        vfs_path = sys.argv[1]
    if len(sys.argv) >= 3:
        script_path = sys.argv[2]

    # Создаем и запускаем эмулятор
    emulator = ShellEmulator(vfs_path, script_path)
    emulator.run()


if __name__ == "__main__":
    main()