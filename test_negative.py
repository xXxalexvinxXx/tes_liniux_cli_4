from ssh_utils import ssh_checkout_negative, ssh_checkout, ssh_getout, upload_files
import yaml
from datetime import datetime

# Чтение конфигурационного файла config.yaml
with open('config.yaml') as f:
    data = yaml.safe_load(f)


class Testneg:
    def save_log(self, starttime, name):
        """
        Сохраняет лог с указанного времени в файл.

        Параметры:
        starttime (str): Время начала логирования.
        name (str): Имя файла для сохранения лога.
        """
        with open(name, 'w') as f:
            f.write(ssh_getout(data["ip"], data["user"], data["passwd"], "journalctl --since '{}'".format(starttime)))

    def check_and_install_p7zip(self):
        """
        Проверяет наличие пакета p7zip-full и устанавливает его при необходимости.
        """
        if not ssh_checkout(data["ip"], data["user"], data["passwd"], "dpkg -s p7zip-full",
                            "Status: install ok installed"):
            ssh_checkout(data["ip"], data["user"], data["passwd"],
                         "echo '{}' | sudo -S apt-get update".format(data["passwd"]), "")
            ssh_checkout(data["ip"], data["user"], data["passwd"],
                         "echo '{}' | sudo -S apt-get install -y p7zip-full".format(data["passwd"]), "")

    def check_and_install_sysstat(self):
        """
        Проверяет наличие пакета sysstat и устанавливает его при необходимости.
        """
        if not ssh_checkout(data["ip"], data["user"], data["passwd"], "dpkg -s sysstat",
                            "Status: install ok installed"):
            ssh_checkout(data["ip"], data["user"], data["passwd"],
                         "echo '{}' | sudo -S apt-get update".format(data["passwd"]), "")
            ssh_checkout(data["ip"], data["user"], data["passwd"],
                         "echo '{}' | sudo -S apt-get install -y sysstat".format(data["passwd"]), "")

    def get_max_cpu_usage(self):
        """
        Возвращает максимальную загрузку процессора за время теста.
        """
        usage = ssh_getout(data["ip"], data["user"], data["passwd"],
                           "grep 'all' /tmp/mpstat.log | awk '{print $3}' | sort -nr | head -1")
        return usage.strip()

    def start_cpu_monitoring(self):
        """
        Запускает мониторинг загрузки процессора.
        """
        ssh_checkout(data["ip"], data["user"], data["passwd"], "mpstat -P ALL 1 > /tmp/mpstat.log &", "")

    def stop_cpu_monitoring(self):
        """
        Останавливает мониторинг загрузки процессора.
        """
        ssh_checkout(data["ip"], data["user"], data["passwd"], "pkill mpstat", "")

    def test_nstep1(self, make_folders, make_files, make_bad_arx, start_time):
        """
        Тест негативного сценария 1:
        Пытаемся извлечь поврежденный архив и проверяем, что возникает ошибка.

        Параметры:
        make_folders (str): Путь к каталогу, в который будут помещены извлеченные файлы.
        make_files (list): Список созданных файлов.
        make_bad_arx (str): Имя поврежденного архива.
        start_time (str): Время начала теста.
        """
        # self.start_cpu_monitoring()
        self.check_and_install_p7zip()
        command = "cd {}; 7z e {}.{} -o{} -y".format(data["folder_out"], make_bad_arx, data["type"], data["folder_ext"])
        result = ssh_checkout_negative(data["ip"], data["user"], data["passwd"], command, "ERROR:")
        # self.stop_cpu_monitoring()
        self.save_log(start_time, "log1_neg.txt")
        max_cpu_usage = self.get_max_cpu_usage()
        assert result, "test1 FAIL"
        print(f'Максимальная загрузка процессора во время нег.теста 1: {max_cpu_usage}%')

    def test_nstep2(self, make_files, make_bad_arx, start_time):
        """
        Тест негативного сценария 2:
        Пытаемся проверить целостность поврежденного архива и проверяем, что возникает ошибка.

        Параметры:
        make_files (list): Список созданных файлов.
        make_bad_arx (str): Имя поврежденного архива.
        start_time (str): Время начала теста.
        """
        # self.start_cpu_monitoring()
        self.check_and_install_p7zip()
        command = "cd {}; 7z t {}.{}".format(data["folder_out"], make_bad_arx, data["type"])
        result = ssh_checkout_negative(data["ip"], data["user"], data["passwd"], command, "ERROR:")
        # self.stop_cpu_monitoring()
        self.save_log(start_time, "log2_neg.txt")
        max_cpu_usage = self.get_max_cpu_usage()
        assert result, "test2 FAIL"
        print(f'Максимальная загрузка процессора во время нег.теста 2: {max_cpu_usage}%')

    def test_nstep3(self, start_time):
        """
        Тест негативного сценария 3:
        Пытаемся удалить и проверить удаление пакета.

        Параметры:
        start_time (str): Время начала теста.
        """
        # self.start_cpu_monitoring()
        self.check_and_install_p7zip()
        res = []
        res.append(ssh_checkout(
            data["ip"], data["user"], data["passwd"],
            "echo '{}' | sudo -S dpkg -r {}".format(data["passwd"], data["pkgname"]),
            "Удаляется"
        ))
        res.append(ssh_checkout(
            data["ip"], data["user"], data["passwd"],
            "echo '{}' | sudo -S dpkg -s {}".format(data["passwd"], data["pkgname"]),
            "Status: deinstall ok"
        ))
        # self.stop_cpu_monitoring()
        self.save_log(start_time, "log3_neg.txt")
        max_cpu_usage = self.get_max_cpu_usage()
        assert all(res), "test3 FAIL"
        print(f'Максимальная загрузка процессора во время нег.теста 3: {max_cpu_usage}%')
