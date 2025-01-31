from pypsrp.client import Client, PowerShell
from pypsrp.wsman import WSMan
import json


def get_system_info(ip):
    """Получение системной информации с удаленного ПК используя текущие учетные данные"""
    try:
        # Настраиваем соединение с использованием текущих учетных данных
        wsman = WSMan(
            server=ip,
            ssl=False,
            auth="negotiate",  # Автоматический выбор аутентификации (Kerberos/NTLM)
            encryption="never"
        )

        with Client(wsman=wsman) as client:
            # Получаем информацию о процессоре
            cpu_script = """
            Get-CimInstance Win32_Processor | 
            Select-Object -First 1 LoadPercentage |
            ConvertTo-Json
            """
            cpu_result = client.execute_ps(cpu_script)
            cpu_data = json.loads(cpu_result)
            cpu_usage = float(cpu_data['LoadPercentage'])

            # Получаем информацию о памяти
            ram_script = """
            Get-CimInstance Win32_OperatingSystem | 
            Select-Object FreePhysicalMemory, TotalVisibleMemorySize |
            ConvertTo-Json
            """
            ram_result = client.execute_ps(ram_script)
            ram_data = json.loads(ram_result)

            ram_total = int(ram_data['TotalVisibleMemorySize']) / 1024 ** 2  # GB
            ram_free = int(ram_data['FreePhysicalMemory']) / 1024 ** 2  # GB
            ram_used = ram_total - ram_free
            ram_percent = (ram_used / ram_total) * 100

            # Получаем информацию о дисках
            disk_script = """
            Get-CimInstance Win32_LogicalDisk | 
            Where-Object { $_.DriveType -eq 3 } |
            Select-Object DeviceID, Size, FreeSpace, FileSystem |
            ConvertTo-Json
            """
            disk_result = client.execute_ps(disk_script)
            disks_data = json.loads(disk_result)

            disks = []
            for disk in disks_data:
                if disk['Size'] is None:
                    continue
                size_gb = int(disk['Size']) / 1024 ** 3
                free_gb = int(disk['FreeSpace']) / 1024 ** 3
                used_gb = size_gb - free_gb

                disks.append({
                    'mount': disk['DeviceID'],
                    'filesystem': disk['FileSystem'],
                    'total': round(size_gb, 2),
                    'used': round(used_gb, 2),
                    'free': round(free_gb, 2),
                    'percent_used': round((used_gb / size_gb) * 100, 1) if size_gb > 0 else 0
                })

            return {
                'cpu_usage': cpu_usage,
                'memory': {
                    'total_gb': round(ram_total, 2),
                    'used_gb': round(ram_used, 2),
                    'percent_used': round(ram_percent, 1)
                },
                'disks': disks,
                'error': None
            }

    except Exception as e:
        return {
            'error': f"Error: {str(e)}",
            'cpu_usage': None,
            'memory': None,
            'disks': None
        }


# Пример использования
if __name__ == "__main__":
    target_ip = "192.168.1.100"  # Замените на IP целевого компьютера
    system_info = get_system_info(target_ip)

    if system_info['error']:
        print("Error:", system_info['error'])
    else:
        print(f"CPU Usage: {system_info['cpu_usage']}%")
        print(f"Memory Usage: {system_info['memory']['percent_used']}%")
        print("Disks:")
        for disk in system_info['disks']:
            print(f"  {disk['mount']} ({disk['filesystem']}): {disk['percent_used']}% used")