from linux_gui.commands import SSHConnection

def get_process_list(ssh_connection: SSHConnection):
    """Получает список процессов с сервера"""
    command = "ps aux --sort=-%cpu | awk 'NR<=10 {print $2, $11, $3}'"

    output, error = ssh_connection.execute_command(command)

    if error:
        return [("Ошибка", error, "")]

    process_list = []
    for line in output.strip().split("\n"):
        parts = line.split()
        if len(parts) >= 3:
            pid, name, cpu = parts[0], parts[1], parts[2]
            process_list.append((pid, name, cpu))

    return process_list
