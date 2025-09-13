import os
import sys
import shlex
from getpass import getuser
from platform import node


class ShellEmulator:
    def __init__(self):
        self.username = getuser()
        self.hostname = node()
        self.cwd = os.path.expanduser("~")

    def prompt(self):
        """Формирует приглашение вида: username@hostname:~$"""

        rel_path = os.path.relpath(self.cwd, os.path.expanduser("~"))
        if rel_path == ".":
            display_path = "~"
        else:
            display_path = rel_path
        return f"{self.username}@{self.hostname}:{display_path}$ "

    def parse_command(self, line):

        try:
            return shlex.split(line)
        except ValueError as e:
            print(f"Ошибка разбора команды: {e}")
            return None

    def execute_command(self, args):

        if not args:
            return

        cmd = args[0]

        if cmd == "exit":
            print("Выход из эмулятора.")
            sys.exit(0)

        elif cmd == "ls":
            print(f"ls {' '.join(args[1:])}")

        elif cmd == "cd":
            if len(args) > 1:
                new_dir = args[1]
                try:
                    os.chdir(new_dir)
                    self.cwd = os.getcwd()
                except FileNotFoundError:
                    print(f"cd: нет такого файла или каталога: {new_dir}")
                except PermissionError:
                    print(f"cd: доступ запрещён: {new_dir}")
                except Exception as e:
                    print(f"cd: ошибка: {e}")
            else:

                os.chdir(os.path.expanduser("~"))
                self.cwd = os.getcwd()

        else:
            print(f"{cmd}: команда не найдена")

    def run(self):

        print("Введите 'exit' для выхода.")
        while True:
            try:
                line = input(self.prompt()).strip()
                if not line:
                    continue

                args = self.parse_command(line)
                if args is None:
                    continue


                self.execute_command(args)

            except KeyboardInterrupt:
                print("")
                continue
            except EOFError:
                print()
                break


if __name__ == "__main__":
    shell = ShellEmulator()
    shell.run()