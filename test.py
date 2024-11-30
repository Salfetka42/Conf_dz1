import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import os
from om import Emulator

class TestEmulator(unittest.TestCase):

    def setUp(self):
        # Создаем временную директорию для тестов
        self.test_dir = tempfile.mkdtemp()

        # Создаем вложенные директории для тестов
        self.dir1 = os.path.join(self.test_dir, 'dir1')
        os.mkdir(self.dir1)

        # Создаем файл, который будет использоваться в тестах
        self.file1 = os.path.join(self.test_dir, 'file1.txt')
        with open(self.file1, 'w') as f:
            f.write("This is a test file.")

        # Создаем экземпляр эмулятора с использованием временной директории
        self.emulator = Emulator("config.yaml")
        self.emulator.fs_zip = self.test_dir  # Привязываем тестовую директорию

        # Устанавливаем начальную директорию
        self.emulator.current_directory = self.test_dir

    def tearDown(self):
        # Удаляем тестовую директорию и все ее содержимое
        shutil.rmtree(self.test_dir)


    @patch('zipfile.Path')
    def test_ls_default(self, MockZipPath):
        # Эмуляция директории
        mock_dir = MagicMock()
        mock_dir.is_dir.return_value = True
        mock_item1 = MagicMock()
        mock_item1.name = 'file1'
        mock_item2 = MagicMock()
        mock_item2.name = 'file2'
        mock_dir.iterdir.return_value = [mock_item1, mock_item2]
        MockZipPath.return_value = mock_dir

        result = self.emulator.ls([])  # Пустой список аргументов (ls)
        self.assertEqual(result, "file1\nfile2")

    @patch('zipfile.Path')
    def test_ls_with_argument(self, MockZipPath):
        # Эмуляция директории с файлом
        mock_dir = MagicMock()
        mock_dir.is_dir.return_value = True
        mock_item = MagicMock()
        mock_item.name = 'file1'
        mock_dir.iterdir.return_value = [mock_item]
        MockZipPath.return_value = mock_dir

        result = self.emulator.ls(["/dir1"])  # Аргумент для ls
        self.assertEqual(result, "file1")

    def test_ls_no_such_directory(self):
        # Ошибка, если директория не существует
        result = self.emulator.ls(["/nonexistent"])
        self.assertEqual(result, "ls: /nonexistent: No such file or directory")

    def test_cd_invalid_directory(self):
        result = self.emulator.cd(["/nonexistent"])
        self.assertEqual(result, "cd: /nonexistent: No such file or directory")

    def test_cd_not_a_directory(self):
       result = self.emulator.cd([self.file1])
       self.assertEqual(result, f"cd: {self.file1}: Not a directory")
    
    def test_cd_valid_directory(self):
        result = self.emulator.cd([self.dir1])
        self.assertEqual(self.emulator.current_directory, self.dir1)



    def test_rmdir_no_such_directory(self, MockZipPath):
        result = self.emulator.rmdir(["/nonexistent"])
        self.assertEqual(result, "rmdir: failed to remove '/nonexistent': No such file or directory")


    def test_pwd(self):
        # Проверка текущей директории
        result = self.emulator.pwd([])
        self.assertEqual(result, "/")

    def test_rmdir_empty_directory(self):
        # Удаление пустой директории
        dir_to_remove = os.path.join(self.test_dir, 'dir2')
        os.mkdir(dir_to_remove)  # Создаем пустую директорию
        result = self.emulator.rmdir([dir_to_remove])
        self.assertEqual(result, f"rmdir: successfully removed '{dir_to_remove}'")

    def test_rmdir_directory_not_empty(self):
        # Попытка удалить непустую директорию
        dir_to_remove = os.path.join(self.test_dir, 'dir3')
        os.mkdir(dir_to_remove)  # Создаем директорию
        file_in_dir = os.path.join(dir_to_remove, 'file_in_dir.txt')
        with open(file_in_dir, 'w') as f:
            f.write("This file is in a directory.")
        
        result = self.emulator.rmdir([dir_to_remove])
        self.assertEqual(result, f"rmdir: failed to remove '{dir_to_remove}': Directory not empty")

    def test_rmdir_no_such_directory(self):
        # Ошибка при попытке удалить несуществующую директорию
        result = self.emulator.rmdir(["/nonexistent"])
        self.assertEqual(result, "rmdir: failed to remove '/nonexistent': No such file or directory")

    def test_exit(self):
        # Пытаемся выйти из эмулятора
        with self.assertRaises(SystemExit):
            self.emulator.exit([])

if __name__ == "__main__":
    unittest.main()
