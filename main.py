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
        self.root['/']['home'][os.getenv('USER', 'user')] = {}
        self.current_path = f"/home/{os.getenv('USER', 'user')}"

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
            path = f"/home/{os.getenv('USER', 'user')}"
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
        username = os.getenv('USER', 'user')
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
            print(f"Ошибка парсинга: {e}", file=sys.stderr)
            return '', []

    def execute_command(self, cmd: str, args: List[str]) -> bool:
        if not cmd:
            return True

        if cmd not in self.commands:
            print(f"{cmd}: команда не найдена", file=sys.stderr)
            return True

        try:
            return self.commands[cmd](args)
        except Exception as e:
            print(f"Ошибка выполнения команды '{cmd}': {e}", file=sys.stderr)
            return True

    def _cmd_ls(self, args: List[str]) -> bool:
        files = self.vfs.list_directory()
        if args:
            print(f"ls: неподдерживаемые аргументы: {' '.join(args)}", file=sys.stderr)
            return True
        for f in files:
            print(f)
        return True

    def _cmd_cd(self, args: List[str]) -> bool:
        if len(args) > 1:
            print("cd: слишком много аргументов", file=sys.stderr)
            return True
        if len(args) == 0:
            success = self.vfs.change_directory('~')
        else:
            success = self.vfs.change_directory(args[0])
        if not success:
            print(f"cd: нет такого каталога: {args[0] if args else ''}", file=sys.stderr)
        return True

    def _cmd_exit(self, args: List[str]) -> bool:
        if args:
            print(f"exit: неподдерживаемые аргументы: {' '.join(args)}", file=sys.stderr)
            return True
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

            cmd, args = self.parse_command(line)
            if not self.execute_command(cmd, args):
                break


if __name__ == "__main__":
    emulator = ShellEmulator()
    emulator.run()