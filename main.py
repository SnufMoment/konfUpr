import os
import sys
import shlex
from typing import List, Dict, Optional


class VirtualFileSystem:

    def __init__(self):
        self.root = {}
        self.current_path = '/'
        self._init_default_structure()

    def _init_default_structure(self):
        self.root['/'] = {}
        self.root['/']['home'] = {}
        # Используем реальное имя пользователя
        self.root['/']['home'][self._get_real_username()] = {}
        self.current_path = f"/home/{self._get_real_username()}"

    def _get_real_username(self) -> str:
        """Получает реальное имя пользователя системы"""
        # Пытаемся получить имя пользователя различными способами
        username = os.getenv('USER')
        if not username:
            username = os.getenv('USERNAME')
        if not username:
            username = os.getenv('LOGNAME')
        if not username:
            username = 'user'  # значение по умолчанию
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
    def __init__(self):
        self.vfs = VirtualFileSystem()
        self.commands = {
            'ls': self._cmd_ls,
            'cd': self._cmd_cd,
            'exit': self._cmd_exit,
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
        files = self.vfs.list_directory()
        if args:
            raise ValueError(f"ls: неподдерживаемые аргументы: {' '.join(args)}")
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

    def run(self):
        print("Эмулятор оболочки UNIX (Этап 1)")
        print("Введите 'exit' для выхода.\n")

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
                # После ошибки выводим новое приглашение на следующей строке
                sys.stdout.flush()
                continue


if __name__ == "__main__":
    emulator = ShellEmulator()
    emulator.run()