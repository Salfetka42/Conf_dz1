import yaml
import zipfile
import os
import tkinter as tk
import tkinter.ttk as ttk
import sys
import logging
import tempfile
import shutil

logging.basicConfig(level=logging.DEBUG)

class Emulator:
    def __init__(self, config_path):
    
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            zip_path = os.path.join(os.path.dirname(config_path), config['filesystem'])
            self.startup_script = config.get('startup_script')
            self.current_directory = '/'
            self.fs_zip = zipfile.ZipFile(zip_path, 'a')  # Используем режим 'a' для записи
        
        

    def _get_full_path(self, path):
        if not path or path == ".":
            return self.current_directory
        if path.startswith("/"):
            return os.path.normpath(path)
        return os.path.normpath(os.path.join(self.current_directory, path))


    def ls(self, args):
        # Получаем полный путь для поиска
        path = self._get_full_path(args[0] if args else ".")
        try:
            # Открываем путь в архиве
            zip_path = zipfile.Path(self.fs_zip, at=path)
            if zip_path.is_dir():  # Если это директория, перечисляем содержимое
                items = [item.name.rstrip("/") for item in zip_path.iterdir()]
                if items:
                    return "\n".join(items)
                return f""   # Если директория пуста
            else:
                return zip_path.name  # Если это файл, возвращаем его имя
        except FileNotFoundError:
            return f"ls: {args[0] if args else '.'}: No such file or directory"


    def cd(self, args):
        """Меняет текущую директорию."""
        if not args:
            return "cd: missing operand"
        
        path = self._get_full_path(args[0])
        path = path.replace("\\", "/")  # Нормализуем путь
        if not path.startswith("/"):
            path = "/" + path

        try:
            zip_path = zipfile.Path(self.fs_zip, at=path)
        except KeyError:
            return f"cd: {path}: No such file or directory"

        if not zip_path.is_dir():
            return f"cd: {path}: Not a directory"

        self.current_directory = path
        return None


    def pwd(self, args):
        return self.current_directory

    def rmdir(self, args):
        if not args:
            return "rmdir: missing operand"
        path_to_remove = self._get_full_path(args[0])
        if not path_to_remove.endswith('/'):
            path_to_remove += '/'

        try:
            zip_path = zipfile.Path(self.fs_zip, at=path_to_remove)

            # Проверяем, существует ли путь
            if not zip_path.exists():
                return f"rmdir: failed to remove '{args[0]}': No such file or directory"

            # Проверяем, что это директория
            if not zip_path.is_dir():
                return f"rmdir: failed to remove '{args[0]}': Not a directory"

            # Удаляем директорию, если она пустая
            if not any(zip_path.iterdir()):
                self.fs_zip.remove(path_to_remove)
                return None

            return f"rmdir: failed to remove '{args[0]}': Directory not empty"
        except FileNotFoundError:
            return f"rmdir: failed to remove '{args[0]}': No such file or directory"
        except Exception as e:
            return f"rmdir: failed to remove '{args[0]}': {str(e)}"




    def exit(self, args):
        self.fs_zip.close()
        self.fs_zip = None
        sys.exit(0)

    def execute_command(self, command):
        parts = command.strip().split()
        if not parts:
            return None
        command_name, *args = parts
        try:
            func = getattr(self, command_name)
            return func(args)
        except AttributeError:
            return f"emulator: {command_name}: command not found"

    def run_startup_script(self):
        if self.startup_script:
            try:
                with open(self.startup_script, 'r') as f:
                    for line in f:
                        result = self.execute_command(line.strip())
                        if result:
                            print(result)
            except FileNotFoundError:
                logging.warning(f"Startup script {self.startup_script} not found.")

class EmulatorGUI:
    def __init__(self, emulator):
        self.emulator = emulator
        self.root = tk.Tk()
        self.root.title("Emulator")

        self.output_text = tk.Text(self.root, wrap=tk.WORD)
        self.output_text.pack(expand=True, fill='both')

        self.input_entry = ttk.Entry(self.root)
        self.input_entry.pack(fill='x')
        self.input_entry.bind("<Return>", self.on_enter)

        button_frame = tk.Frame(self.root)
        button_frame.pack()

        for command in ["ls", "pwd", "cd", "rmdir", "exit"]:
            self.create_button(button_frame, command)

        self.current_dir_label = ttk.Label(self.root, text=f"Current Directory: {self.emulator.current_directory}")
        self.current_dir_label.pack(fill='x')

    def create_button(self, frame, command):
        btn = ttk.Button(frame, text=command, command=lambda cmd=command: self.execute_gui_command(cmd))
        btn.pack(side=tk.LEFT)

    def execute_gui_command(self, command):
        args = self.input_entry.get().strip()
        full_command = f"{command} {args}".strip()
        result = self.emulator.execute_command(full_command)
        self.input_entry.delete(0, tk.END)
        self.show_result(result)
        if command == "cd":
            self.current_dir_label.config(text=f"Current Directory: {self.emulator.current_directory}")

    def on_enter(self, event):
        command = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)
        self.show_result(self.emulator.execute_command(command))

    def show_result(self, result):
        if result:
            self.output_text.insert(tk.END, result + "\n")
            self.output_text.see(tk.END)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":  
    try:
        # Проверяем, был ли указан путь к конфигурационному файлу
        config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        
        # Проверяем наличие файла перед использованием
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
        
        emulator = Emulator(config_file)
        emulator.run_startup_script()  # запуск стартового скрипта
        gui = EmulatorGUI(emulator)
        gui.run()
    except RuntimeError as e:
        logging.error(str(e))
    except FileNotFoundError as e:
        logging.error(str(e))
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")

