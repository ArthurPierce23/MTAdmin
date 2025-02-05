# windows_gui/system_info.py
import json
import logging
import re
from pypsrp.powershell import PowerShell, RunspacePool

logger = logging.getLogger(__name__)


def execute_ps_script(session: RunspacePool, script: str) -> dict:
    """
    Выполняет PowerShell-скрипт через объект PowerShell с использованием RunspacePool
    и возвращает разобранный JSON. Если вывод пустой, возвращается пустой словарь.
    Если в выводе присутствует лишний текст, пытается извлечь корректный JSON.
    """
    try:
        ps = PowerShell(runspace_pool=session)
        ps.add_script(script)
        ps.begin_invoke()
        ps.poll_invoke()
        output = ps.end_invoke()

        std_out = "\n".join([str(o) for o in output])
        errors = "\n".join([str(e) for e in ps.streams.error])

        if ps.had_errors:
            raise Exception(f"PowerShell Error: {errors}")

        # Улучшенный парсинг JSON
        json_data = re.search(r'(\{.*\}|\[.*\])', std_out, re.DOTALL)
        return json.loads(json_data.group(0)) if json_data else {}

    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        return {"error": str(e)}

def get_system_info(session: RunspacePool) -> dict:
    """
    Получает информацию о системе (CPU, память, диски) посредством выполнения PowerShell-скрипта
    в переданной сессии (RunspacePool).
    """
    ps_script = r"""
$cpu = (Get-CimInstance -ClassName Win32_Processor | Select-Object -First 1).LoadPercentage
$os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $os) {
    $result.error = "Не удалось получить информацию об операционной системе"
    return $result | ConvertTo-Json -Depth 4
}

$total_memory = if ($os.TotalVisibleMemorySize) { [math]::Round($os.TotalVisibleMemorySize / 1024, 2) } else { 0 }
$free_memory = if ($os.FreePhysicalMemory) { [math]::Round($os.FreePhysicalMemory / 1024, 2) } else { 0 }
$used_memory = $total_memory - $free_memory
$memory_percent = if ($total_memory -gt 0) { [math]::Round(($used_memory / $total_memory * 100),1) } else { 0 }
$disks = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $size = if ($_.Size) { [math]::Round($_.Size / 1GB,2) } else { 0 }
    $free = if ($_.FreeSpace) { [math]::Round($_.FreeSpace / 1GB,2) } else { 0 }
    $used = if ($size - $free -gt 0) { [math]::Round($size - $free,2) } else { 0 }
    $percent = if ($size -gt 0) { [math]::Round(($used / $size * 100),1) } else { 0 }
    [PSCustomObject]@{
        mount = $_.DeviceID;
        filesystem = if ($_.FileSystem) { $_.FileSystem } else { "Unknown" };
        total = $size;
        used = $used;
        free = $free;
        percent_used = $percent
    }
}
$result = @{
    cpu_usage = $cpu;
    memory = @{
        total_mb = [math]::Round($total_memory,2);
        used_mb = [math]::Round($used_memory,2);
        percent_used = $memory_percent
    };
    disks = $disks;
    error = $null
}
$result | ConvertTo-Json -Depth 4
"""
    return execute_ps_script(session, ps_script)

# Пример использования (для тестирования):
if __name__ == "__main__":
    from old_project.windows_gui.session_manager import PowerShellSessionManager

    target_ip = "10.254.44.37"
    session_manager = PowerShellSessionManager(ip=target_ip)
    if session_manager.connect():
        try:
            system_info = get_system_info(session_manager.session)
            if system_info.get('error'):
                print("Error:", system_info['error'])
            else:
                print(f"CPU Usage: {system_info['cpu_usage']}%")
                mem = system_info['memory']
                print(f"Memory: {mem['used_mb']} MB used of {mem['total_mb']} MB ({mem['percent_used']}% used)")
                print("Disks:")
                for disk in system_info['disks']:
                    print(f"  {disk['mount']} ({disk['filesystem']}): {disk['percent_used']}% used")
        except Exception as e:
            print("Ошибка получения информации о системе:", e)
        finally:
            session_manager.close()
    else:
        print("Не удалось установить сессию.")
