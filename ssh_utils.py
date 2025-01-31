import paramiko
import os
import subprocess

def ensure_ssh_key():
    """
    Проверяет наличие SSH-ключа и генерирует его при отсутствии.
    """
    ssh_key_path = os.path.expanduser('~/.ssh/id_rsa')
    if not os.path.exists(ssh_key_path):
        print('SSH ключ не найден. Генерация нового ключа...')
        subprocess.run(['ssh-keygen', '-t', 'rsa', '-b', '2048', '-f', ssh_key_path, '-N', ''], check=True)
        print('SSH ключ успешно сгенерирован.')
    else:
        print('SSH ключ уже существует.')

ensure_ssh_key()


def upload_ssh_key(host, user, password):
    """
    Загружает SSH-ключ на удалённый хост.
    
    Параметры:
    host (str): IP-адрес или доменное имя удалённого хоста.
    user (str): Имя пользователя для подключения к удалённому хосту.
    password (str): Пароль для подключения к удалённому хосту.
    """
    ssh_copy_id_command = f'sshpass -p {remote_password} ssh-copy-id -o StrictHostKeyChecking=no {remote_user}@{remote_host}'
    subprocess.run(ssh_copy_id_command, shell=True, check=True)
    print(f'SSH ключ успешно загружен на {remote_user}@{remote_host}.')

# Пример использования
# upload_ssh_key('remote_host_ip', 'remote_user', 'remote_password')


def ssh_checkout(host, user, passwd, cmd, text, port=22, use_key=False):
    """
    Функция для выполнения команды на удаленной машине через SSH и проверки ее вывода на наличие определенного текста.

    Параметры:
    host (str): Адрес хоста для подключения по SSH.
    user (str): Имя пользователя для подключения.
    passwd (str): Пароль для подключения.
    cmd (str): Команда для выполнения на удаленной машине.
    text (str): Текст, который должен присутствовать в выводе команды для успешного выполнения.
    port (int): Порт для подключения по SSH. По умолчанию 22.
    use_key (bool): Флаг использования ssh-ключа для подключения

    Возвращает:
    True, если текст найден в выводе команды и команда завершилась успешно (код возврата 0), иначе False.
    """
    # Создаем SSH-клиент
    client = paramiko.SSHClient()
    # Автоматически добавляем ключи хостов
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Подключаемся к удаленному хосту
    if use_key:
        key_path = os.path.expanduser('~/.ssh/id_rsa')
        key = paramiko.RSAKey(filename=key_path)
        client.connect(hostname=host, username=user, pkey=key, port=port)
    else:
        client.connect(hostname=host, username=user, password=passwd, port=port)
    # Выполняем команду на удаленном хосте
    stdin, stdout, stderr = client.exec_command(cmd)
    # Получаем код возврата команды
    exit_code = stdout.channel.recv_exit_status()
    # Читаем вывод команды и ошибки
    out = (stdout.read() + stderr.read()).decode('utf-8')
    # Закрываем SSH-соединение
    client.close()
    # Проверяем наличие текста в выводе команды и успешное выполнение команды
    if text in out and exit_code == 0:
        return True
    else:
        return False

def ssh_getout(host, user, passwd, cmd, port=22):
    """
    Функция для выполнения команды на удаленной машине через SSH и возврата ее полного вывода.

    Параметры:
    host (str): Адрес хоста для подключения по SSH.
    user (str): Имя пользователя для подключения.
    passwd (str): Пароль для подключения.
    cmd (str): Команда для выполнения на удаленной машине.
    port (int): Порт для подключения по SSH. По умолчанию 22.

    Возвращает:
    str: Полный вывод команды (stdout и stderr) в виде строки.
    """
    # Создаем SSH-клиент
    client = paramiko.SSHClient()
    # Автоматически добавляем ключи хостов
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Подключаемся к удаленному хосту
    client.connect(hostname=host, username=user, password=passwd, port=port)
    # Выполняем команду на удаленном хосте
    stdin, stdout, stderr = client.exec_command(cmd)
    # Читаем вывод команды и ошибки
    out = (stdout.read() + stderr.read()).decode('utf-8')
    # Закрываем SSH-соединение
    client.close()
    return out

def upload_files(host, user, passwd, local_path, remote_path, port=22):
    """
    Функция для загрузки файлов на удаленную машину через SFTP.

    Параметры:
    host (str): Адрес хоста для подключения по SSH.
    user (str): Имя пользователя для подключения.
    passwd (str): Пароль для подключения.
    local_path (str): Путь к локальному файлу, который нужно загрузить.
    remote_path (str): Путь к удаленному каталогу, куда нужно загрузить файл.
    port (int): Порт для подключения по SSH. По умолчанию 22.
    """
    print(f'Загружаем файл {local_path} в каталог {remote_path}')
    # Создаем транспортное соединение
    transport = paramiko.Transport((host, port))
    transport.connect(None, username=user, password=passwd)
    # Создаем SFTP-клиент
    sftp = paramiko.SFTPClient.from_transport(transport)
    # Загружаем файл
    sftp.put(local_path, remote_path)
    # Закрываем SFTP и транспортное соединение
    if sftp:
        sftp.close()
    if transport:
        transport.close()

def download_files(host, user, passwd, remote_path, local_path, port=22):
    """
    Функция для скачивания файлов с удаленной машины через SFTP.

    Параметры:
    host (str): Адрес хоста для подключения по SSH.
    user (str): Имя пользователя для подключения.
    passwd (str): Пароль для подключения.
    remote_path (str): Путь к удаленному файлу, который нужно скачать.
    local_path (str): Путь к локальному каталогу, куда нужно скачать файл.
    port (int): Порт для подключения по SSH. По умолчанию 22.
    """
    print(f'Скачиваем файл {remote_path} в каталог {local_path}')
    # Создаем транспортное соединение
    transport = paramiko.Transport((host, port))
    transport.connect(None, username=user, password=passwd)
    # Создаем SFTP-клиент
    sftp = paramiko.SFTPClient.from_transport(transport)
    # Скачиваем файл
    sftp.get(remote_path, local_path)
    # Закрываем SFTP и транспортное соединение
    if sftp:
        sftp.close()
    if transport:
        transport.close()

def ssh_checkout_negative(host, user, passwd, cmd, text, port=22):
    """
    Функция для выполнения команды на удаленной машине через SSH и проверки ее вывода на наличие определенного текста,
    но ожидая, что команда завершится с ошибкой.

    Параметры:
    host (str): Адрес хоста для подключения по SSH.
    user (str): Имя пользователя для подключения.
    passwd (str): Пароль для подключения.
    cmd (str): Команда для выполнения на удаленной машине.
    text (str): Текст, который должен присутствовать в выводе команды для успешного выполнения.
    port (int): Порт для подключения по SSH. По умолчанию 22.

    Возвращает:
    True, если текст найден в выводе команды и команда завершилась с ошибкой (не нулевой код возврата), иначе False.
    """
    # Создаем SSH-клиент
    client = paramiko.SSHClient()
    # Автоматически добавляем ключи хостов
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Подключаемся к удаленному хосту
    client.connect(hostname=host, username=user, password=passwd, port=port)
    # Выполняем команду на удаленном хосте
    stdin, stdout, stderr = client.exec_command(cmd)
    # Получаем код возврата команды
    exit_code = stdout.channel.recv_exit_status()
    # Читаем вывод команды и ошибки
    out = (stdout.read() + stderr.read()).decode('utf-8')
    # Закрываем SSH-соединение
    client.close()
    # Проверяем наличие текста в выводе команды и что команда завершилась с ошибкой
    if text in out and exit_code != 0:
        return True
    else:
        return False
