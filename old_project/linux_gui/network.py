from linux_gui.commands import SSHConnection

def get_network_info(ssh_connection: SSHConnection):
    """Получает сетевую информацию по SSH"""
    commands = {
        "IP Addresses": "ip -4 addr show | grep 'inet ' | awk '{print $2}'",
        "Interfaces": "ip -o link show | awk -F': ' '{print $2}'",
        "Active Connections": "ss -tuna | awk 'NR>1 {print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr"
    }

    results = {}

    for key, cmd in commands.items():
        output, error = ssh_connection.execute_command(cmd)
        results[key] = output.splitlines() if output else ["Нет данных"]

    return results
