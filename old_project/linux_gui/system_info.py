import paramiko
from linux_gui.commands import SSHConnection


def get_system_info(ssh_connection: SSHConnection) -> dict:
    """Получает информацию о системе по активному SSH-соединению"""

    commands = {
        "OS": "cat /etc/os-release | grep PRETTY_NAME | cut -d '\"' -f2",
        "Kernel": "uname -r",
        "Architecture": "uname -m",
        "Uptime": "uptime -p",
        "CPU Load": "top -bn1 | grep 'load average' | awk '{print $(NF-2), $(NF-1), $NF}'",
        "RAM Usage": "free -m | awk 'NR==2{printf \"Used: %sMB / Total: %sMB\", $3, $2}'",
        "Disk Usage": "df -h / | awk 'NR==2{print \"Used: \" $3 \" / Total: \" $2}'",
        "Users Logged In": "who | awk '{print $1}' | sort | uniq | paste -sd ', ' -",
        "Local IP": "hostname -I | awk '{print $1}'"
    }

    results = {}

    for key, cmd in commands.items():
        output, error = ssh_connection.execute_command(cmd)
        results[key] = output if output else f"Ошибка: {error}" if error else "Нет данных"

    return results