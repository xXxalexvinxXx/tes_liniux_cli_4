import pytest
from ssh_utils import ssh_checkout
import random, string
import yaml
from datetime import datetime

# Чтение конфигурационного файла config.yaml
with open('config.yaml') as f:
    data = yaml.safe_load(f)


# Фикстура для создания необходимых каталогов
@pytest.fixture()
def make_folders():
    """
    Создает необходимые каталоги на удаленной машине.
    """
    return ssh_checkout(
        data["ip"], data["user"], data["passwd"],
        "mkdir {} {} {} {}".format(data["folder_in"], data["folder_out"], data["folder_ext"], data["folder_ext2"]),
        ""
    )


# Фикстура для очистки каталогов на удаленной машине
@pytest.fixture()
def clear_folders():
    """
    Очищает содержимое указанных каталогов на удаленной машине.
    """
    return ssh_checkout(
        data["ip"], data["user"], data["passwd"],
        "rm -rf {}/{}/* {}/* {}/* {}/*".format(
            data["folder_in"], data["folder_out"], data["folder_ext"], data["folder_ext2"]
        ),
        ""
    )


# Фикстура для создания файлов на удаленной машине
@pytest.fixture()
def make_files():
    """
    Создает указанное количество случайных файлов на удаленной машине.
    """
    list_of_files = []
    for i in range(data["count"]):
        filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if ssh_checkout(
                data["ip"], data["user"], data["passwd"],
                "cd {}; dd if=/dev/urandom of={} bs=1M count=1 iflag=fullblock".format(data["folder_in"], filename),
                ""
        ):
            list_of_files.append(filename)
    return list_of_files


# Фикстура для создания подкаталога на удаленной машине
@pytest.fixture()
def make_subfolder():
    """
    Создает подкаталог и случайный файл в нем на удаленной машине.
    """
    testfilename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    subfoldername = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    if not ssh_checkout(
            data["ip"], data["user"], data["passwd"],
            "cd {}; mkdir {}".format(data["folder_in"], subfoldername),
            ""
    ):
        return None, None
    if not ssh_checkout(
            data["ip"], data["user"], data["passwd"],
            "cd {}/{}; dd if=/dev/urandom of={} bs=1M count=1 iflag=fullblock".format(data["folder_in"], subfoldername,
                                                                                      testfilename),
            ""
    ):
        return subfoldername, None
    else:
        return subfoldername, testfilename


# Фикстура для создания поврежденного архива на удаленной машине
@pytest.fixture()
def make_bad_arx():
    """
    Создает поврежденный архив на удаленной машине и удаляет его после использования.
    """
    ssh_checkout(
        data["ip"], data["user"], data["passwd"],
        "cd {}; 7z a {}/arxbad -t{}".format(data["folder_in"], data["folder_out"], data["type"]),
        "Everything is Ok"
    )
    ssh_checkout(
        data["ip"], data["user"], data["passwd"],
        "truncate -s 1 {}/arxbad.{}".format(data["folder_out"], data["type"]),
        "Everything is Ok"
    )
    yield "arxbad"
    ssh_checkout(
        data["ip"], data["user"], data["passwd"],
        "rm -f {}/arxbad.{}".format(data["folder_out"], data["type"]),
        ""
    )


# Фикстура для вывода времени начала и окончания теста
@pytest.fixture(autouse=True)
def print_time():
    """
    Выводит время начала и окончания выполнения каждого теста.
    """
    print("Start: {}".format(datetime.now().strftime("%H:%M:%S.%f")))
    yield print("Stop: {}".format(datetime.now().strftime("%H:%M:%S.%f")))


# Фикстура для получения текущего времени
@pytest.fixture()
def start_time():
    """
    Возвращает текущее время в формате '%Y-%m-%d %H:%M:%S'.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
