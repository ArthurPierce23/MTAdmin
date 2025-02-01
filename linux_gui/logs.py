from linux_gui.commands import SSHConnection

def get_system_logs(ssh_connection: SSHConnection, lines: int = 50):
    """
    Получает последние строки системного журнала.
    Проверяет наличие нескольких возможных файлов журналов.
    """
    log_files = ["/var/log/syslog", "/var/log/messages", "/var/log/dmesg"]

    for log_file in log_files:
        command = f"test -f {log_file} && tail -n {lines} {log_file}"
        output, error = ssh_connection.execute_command(command)

        if output:  # Если удалось получить логи
            return output

    return "Не удалось найти доступные журналы."
