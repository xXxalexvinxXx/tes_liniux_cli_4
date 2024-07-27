import yaml
from utils import getout
from ssh_utils import ssh_checkout, upload_files, ssh_getout

# Загружаем конф. файл
with open('config.yaml') as f:
    data = yaml.safe_load(f)


# Определяем класс содержащий полоэительные тесты
class TestPositive:

    def check_and_install_sysstat(self):
        """
        Проверяет наличие пакета sysstat и устанавливает его при необходимости.
        """
        if not ssh_checkout(data['ip'], data['user'], data['passwd'], 'dpkg -s sysstat',
                            'Status: install ok installed'):
            ssh_checkout(data['ip'], data['user'], data['passwd'],
                         'echo "{}" | sudo -S apt-get update'.format(data['passwd']), '')
            ssh_checkout(data['ip'], data['user'], data['passwd'],
                         'echo "{}" | sudo -S apt-get install -y sysstat'.format(data['passwd']), '')

    # опредезяем метод для сохранения логов в файл
    def save_log(self, starttime, name):
        """
        Сохраняет лог с указанного времени в файл.

        Параметры:
        starttime (str): Время начала логирования.
        name (str): Имя файла для сохранения лога.
        """
        with open(name, 'w') as f:
            f.write(ssh_getout(data['ip'], data['user'], data['passwd'], 'journalctl --since "{}"'.format(starttime)))

    def get_max_cpu_usage(self):
        """
        Возвращает максимальную загрузку процессора за время теста.
        """
        usage = ssh_getout(data['ip'], data['user'], data['passwd'],
                           "grep 'all' /tmp/mpstat.log | awk '{print $3}' | sort -nr | head -1")
        return usage.strip()

    # Тест 1. Загрузка пакета и проверка установки
    def test_step1(self, start_time):
        res = []
        # Загрузка пакета на удаленный хост
        upload_files(data['ip'], data['user'], data['passwd'], data['pkgname'] + '.deb',
                     '/home/{}/{}.deb'.format(data['user'], data['pkgname']))
        # Установка пакета на удаленном хосте и проверка успеха
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'echo "{}" | sudo -S dpkg -i'
                                                                          ' /home/{}/{}.deb'.format(data['passwd'],
                                                                                                    data['user'],
                                                                                                    data['pkgname']),
                                'Настраивается пакет'))
        # Проверка статуса пакета (установлен)
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'echo "{}" | '
                                                                          'sudo -S dpkg -s {}'.format(data['passwd'],
                                                                                                      data['pkgname']),
                                'Status: install ok installed'))
        # Сохранение лога в файл
        self.save_log(start_time, 'log1.txt')
        max_cpu_usage = self.get_max_cpu_usage()
        assert all(res), 'test1 FAIL'
        print(f'Максимальная загрузка процессора во время теста 1: {max_cpu_usage}%')

    # Тест 2. Упаковка папки и проверка архива
    def test_step2(self, make_folders, clear_folders, make_files, start_time):
        # Создание архива определенной папки
        res1 = ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {};'
                                                                      ' 7z a {}/arx2'.format(data['folder_in'],
                                                                                             data['folder_out']),
                            'Everything is Ok')
        # Проверка создания файла архива
        res2 = ssh_checkout(data['ip'], data['user'], data['passwd'], 'ls {}'.format(data['folder_out']), 'arx2.7z')
        # Сохранение лога в файл
        self.save_log(start_time, 'log2.txt')
        max_cpu_usage = self.get_max_cpu_usage()
        assert res1 and res2, 'test2 FAIL'
        print(f'Максимальная загрузка процессора во время теста 2: {max_cpu_usage}%')

    # Тест 3. Распаковка архива и проверка распакованных файлов
    def test_step3(self, clear_folders, make_files, start_time):
        res = []
        # Создание архива определенной папки
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z a '
                                                                          '{}/arx2'.format(data['folder_in'],
                                                                                           data['folder_out']),
                                'Everything is Ok'))
        # Распаковка архива в определенную папку
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z e '
                                                                          'arx2.7z -o{} -y'.format(data['folder_out'],
                                                                                                   data['folder_ext']),
                                'Everything is Ok'))
        # Проверка файлов в папке
        for item in make_files:
            res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'ls {}'.format(data['folder_ext']), item))
        max_cpu_usage = self.get_max_cpu_usage()
        # Сохранение лога в файл
        self.save_log(start_time, 'log3.txt')
        assert all(res), 'test3 FAIL'
        print(f'Максимальная загрузка процессора во время теста 3: {max_cpu_usage}%')

    # Тест 4. Проверка целостности архива
    def test_step4(self, start_time):
        # Сохранение лога в файл
        self.save_log(start_time, 'log4.txt')
        max_cpu_usage = self.get_max_cpu_usage()
        assert ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z t'
                                                                      ' arx2.7z'.format(data['folder_out']),
                            'Everything is Ok'), 'test4 FAIL'
        print(f'Максимальная загрузка процессора во время теста 3: {max_cpu_usage}%')

    # Тест 5. Обновление архива
    def test_step5(self, start_time):
        # Сохранение лога в файл
        self.save_log(start_time, 'log5.txt')
        max_cpu_usage = self.get_max_cpu_usage()
        assert ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z u'
                                                                      ' arx2.7z'.format(data['folder_in']),
                            'Everything is Ok'), 'test5 FAIL'
        print(f'Максимальная загрузка процессора во время теста 5: {max_cpu_usage}%')

    # Тест 6. Листинг архива и проверка файлов
    def test_step6(self, clear_folders, make_files, start_time):
        res = []
        # Создание архива определенной папки
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z a '
                                                                          '{}/arx2'.format(data['folder_in'],
                                                                                           data['folder_out']),
                                'Everything is Ok'))
        # Проверка файлов в папке
        for item in make_files:
            res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z l'
                                                                              ' arx2.7z'.format(data['folder_out'],
                                                                                                data['folder_ext']),
                                    item))
        # Сохранение лога в файл
        self.save_log(start_time, 'log6.txt')
        max_cpu_usage = self.get_max_cpu_usage()
        assert all(res), 'test6 FAIL'
        print(f'Максимальная загрузка процессора во время теста 6: {max_cpu_usage}%')

    # Тест 7. Создание архива и извлечение в подпапку, проверка файлов
    def test_step7(self, clear_folders, make_files, make_subfolder, start_time):
        res = []
        # Создание архива определенной папки
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z a '
                                                                          '{}/arx'.format(data['folder_in'],
                                                                                          data['folder_out']),
                                'Everything is Ok'))
        # Извлечение в определенную папку
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {};'
                                                                          ' 7z x arx.7z -o{} -y'.format(
            data['folder_out'], data['folder_ext2']), 'Everything is Ok'))
        # Проверка файлов в папке и их содержания
        for item in make_files:
            res.append(
                ssh_checkout(data['ip'], data['user'], data['passwd'], 'ls {}'.format(data['folder_ext2']), item))

        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'ls {}'.format(data['folder_ext2']),
                                make_subfolder[0]))
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'ls {}/{}'.format(data['folder_ext2'],
                                                                                            make_subfolder[0]),
                                make_subfolder[1]))
        # Сохранение лога в файл
        self.save_log(start_time, 'log7.txt')
        max_cpu_usage = self.get_max_cpu_usage()
        assert all(res), 'test7 FAIL'
        print(f'Максимальная загрузка процессора во время теста 7: {max_cpu_usage}%')

    # Тест 8. Удаление файла из архива
    def test_step8(self, start_time):
        # Сохранение лога в файл
        self.save_log(start_time, 'log8.txt')
        max_cpu_usage = self.get_max_cpu_usage()
        assert ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z d arx.7z'.format(data['folder_out']),
                            'Everything is Ok'), 'test8 FAIL'
        print(f'Максимальная загрузка процессора во время теста 8: {max_cpu_usage}%')

    # Тест 9. Подсчет и проверка хэша файлов
    def test_step9(self, clear_folders, make_files, start_time):
        # Сохранение лога в файл
        self.save_log(start_time, 'log9.txt')
        res = []
        for item in make_files:
            res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z h {}'.format(data['folder_in'],
                                                                                                      item),
                                    'Everything is Ok'))
            hash_f = ssh_getout(data['ip'], data['user'], data['passwd'], 'cd {}; '
                                                                          'crc32 {}'.format(data['folder_in'],
                                                                                            item)).upper()
            res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'cd {}; 7z h {}'.format(data['folder_in'],
                                                                                                      item), hash_f))
        max_cpu_usage = self.get_max_cpu_usage()
        assert all(res), 'test9 FAIL'
        print(f'Максимальная загрузка процессора во время теста 9: {max_cpu_usage}%')

    # Тест 10. Удаление пакета
    def test_step10(self, start_time):
        res = []
        # Удаление пакета
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'echo "{}" | sudo -S dpkg -r'
                                                                          ' {}'.format(data['passwd'], data['pkgname']),
                                'Удаляется'))
        # Проверка статуса
        res.append(ssh_checkout(data['ip'], data['user'], data['passwd'], 'echo "{}" | '
                                                                          'sudo -S dpkg -s {}'.format(data['passwd'],
                                                                                                      data['pkgname']),
                                'Status: deinstall ok'))
        # Сохранение лога в файл
        self.save_log(start_time, 'log10.txt')
        max_cpu_usage = self.get_max_cpu_usage()
        assert all(res), 'test10 FAIL'
        print(f'Максимальная загрузка процессора во время теста 10: {max_cpu_usage}%')
