from pypsexec.client import Client


def run_psexec_command(host: str, command: str):
    """
    Подключается к удаленному Windows ПК через PsExec и выполняет команду.

    :param host: Имя или IP удаленного компьютера
    :param command: Команда для выполнения
    :return: Вывод команды или ошибка
    """
    try:
        print(f"🚀 Выполняю команду на {host}: {command}")

        client = Client(host, encrypt=False)  # Отключаем шифрование для скорости
        client.connect()
        client.create_service()
        stdout, stderr, exit_code = client.run_executable("cmd.exe", arguments=f'/c {command}')
        client.remove_service()
        client.disconnect()

        if exit_code == 0:
            result = stdout.decode("cp866").strip()
            print(f"✅ Успешно выполнено: {result}")
            return result
        else:
            error_message = stderr.decode("cp866").strip()
            print(f"❌ Ошибка выполнения команды: {error_message}")
            return f"Ошибка: {error_message}"

    except Exception as e:
        print(f"❌ Ошибка подключения: {str(e)}")
        return f"Ошибка: {str(e)}"


def enable_rdp(host: str):
    """Включает RDP и открывает порт в брандмауэре."""
    print("\n🔹 Включаем RDP...")
    run_psexec_command(host,
                       'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f')
    run_psexec_command(host, 'powershell -Command "Enable-NetFirewallRule -DisplayName \'Remote Desktop*\'"')


def disable_rdp(host: str):
    """Отключает RDP и закрывает порт в брандмауэре."""
    print("\n🔹 Выключаем RDP...")
    run_psexec_command(host,
                       'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 1 /f')
    run_psexec_command(host, 'powershell -Command "Disable-NetFirewallRule -DisplayName \'Remote Desktop*\'"')


def change_rdp_port(host: str, port: int):
    """Меняет порт RDP."""
    print(f"\n🔹 Меняем порт RDP на {port}...")
    run_psexec_command(host,
                       f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v PortNumber /t REG_DWORD /d {port} /f')
    run_psexec_command(host,
                       f'powershell -Command "Set-NetFirewallRule -DisplayName \'Remote Desktop*\' -LocalPort {port}"')


def add_rdp_user(host: str, username: str):
    """Добавляет пользователя в группу RDP."""
    print(f"\n🔹 Добавляем пользователя {username} в RDP...")
    run_psexec_command(host, f'net localgroup "Пользователи удаленного рабочего стола" {username} /add')


def remove_rdp_user(host: str, username: str):
    """Удаляет пользователя из группы RDP."""
    print(f"\n🔹 Удаляем пользователя {username} из RDP...")
    run_psexec_command(host, f'net localgroup "Remote Desktop Users" {username} /delete')


if __name__ == "__main__":
    remote_host = "VLG-STP-012"

    # Тестируем команды
    enable_rdp(remote_host)
    change_rdp_port(remote_host, 3390)
    add_rdp_user(remote_host, "ncc\\ya.afanaseva")

    input("\n⏸️ Проверь изменения и нажми Enter для обратных действий...")

    remove_rdp_user(remote_host, "ncc\\ya.afanaseva")
    change_rdp_port(remote_host, 3389)
    disable_rdp(remote_host)
