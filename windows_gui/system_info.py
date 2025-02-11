import logging
import json
from typing import Optional, Dict, Any
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan

logger = logging.getLogger(__name__)


class SystemInfo:
    def __init__(self, hostname: str) -> None:
        self.hostname = hostname

    def _init_ps_session(self) -> Optional[RunspacePool]:
        """
        Инициализирует сессию PowerShell через WinRM.

        :return: Экземпляр RunspacePool при успешном подключении или None при ошибке.
        """
        try:
            wsman = WSMan(
                server=self.hostname,
                auth="negotiate",
                ssl=False,
                encryption="auto",
                cert_validation=False,
                connection_timeout=15
            )
            pool = RunspacePool(wsman)
            pool.open()
            return pool
        except Exception as e:
            logger.error(f"Ошибка подключения к {self.hostname}: {e}")
            return None

    def get_system_info(self) -> Dict[str, Any]:
        """
        Получает системную информацию с удалённого компьютера через PowerShell.

        :return: Словарь с данными системы или с ключом "error" в случае ошибки.
        """
        session = self._init_ps_session()
        if not session:
            return {"error": "WinRM connection failed"}

        ps_script = r"""
$ErrorActionPreference = "Stop"
try {
    # Информация о процессоре
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    $cpu_model = $cpu.Name
    $cpu_load = if ($cpu.LoadPercentage) { $cpu.LoadPercentage } else { $null }

    # Информация о памяти
    $os = Get-CimInstance Win32_OperatingSystem
    $ram_total = if ($os.TotalVisibleMemorySize) { [math]::Round($os.TotalVisibleMemorySize/1MB, 2) } else { 0 }
    $ram_free = if ($os.FreePhysicalMemory) { [math]::Round($os.FreePhysicalMemory/1MB, 2) } else { 0 }

    # Информация о дисках
    $disks = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
        $total = if ($_.Size) { [math]::Round($_.Size/1GB, 2) } else { 0 }
        $free = if ($_.FreeSpace) { [math]::Round($_.FreeSpace/1GB, 2) } else { 0 }
        [PSCustomObject]@{
            Letter      = $_.DeviceID
            TotalGB     = $total
            FreeGB      = $free
            UsedGB      = [math]::Round($total - $free, 2)
            UsedPercent = if ($total -gt 0) { [math]::Round(($total - $free)/$total*100, 2) } else { 0 }
        }
    }

    # Информация о материнской плате
    $motherboard = Get-CimInstance Win32_BaseBoard | Select-Object -ExpandProperty Product

    # Время работы системы
    $uptime_raw = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    $uptime_span = (Get-Date) - $uptime_raw
    $uptime = "{0} д. {1} ч. {2} мин." -f $uptime_span.Days, $uptime_span.Hours, $uptime_span.Minutes

    # MAC-адреса
    $macs = Get-CimInstance Win32_NetworkAdapterConfiguration |
            Where-Object { $_.IPEnabled -eq $true } |
            Select-Object -ExpandProperty MACAddress
    $mac = ($macs -join ", ")

    # Подготовка результата
    [PSCustomObject]@{
        CPU = @{
            Model = $cpu_model
            Load  = $cpu_load
            Cores = $cpu.NumberOfLogicalProcessors
        }
        RAM = @{
            TotalGB     = $ram_total
            FreeGB      = $ram_free
            UsedGB      = [math]::Round($ram_total - $ram_free, 2)
            UsedPercent = if ($ram_total -gt 0) { [math]::Round(($ram_total - $ram_free)/$ram_total*100, 2) } else { 0 }
        }
        Disks       = $disks
        Motherboard = $motherboard
        Uptime      = $uptime
        MAC_Address = $mac
    } | ConvertTo-Json -Depth 3 -Compress
}
catch {
    [PSCustomObject]@{
        Error   = $_.Exception.Message
        Details = $_.ScriptStackTrace
    } | ConvertTo-Json -Compress
}
"""
        json_str = ""
        try:
            ps = PowerShell(session)
            ps.add_script(ps_script)
            output = ps.invoke()

            if ps.streams.error:
                errors = "\n".join(str(e) for e in ps.streams.error)
                return {"error": f"PowerShell errors: {errors}"}

            json_str = "".join(str(o) for o in output)
            data = json.loads(json_str)

            if "Error" in data:
                return {"error": data.get("Error"), "details": data.get("Details")}

            return data

        except json.JSONDecodeError as e:
            error_msg = f"Ошибка разбора JSON: {e}. Сырой вывод: {json_str}"
            logger.error(error_msg)
            return {"error": error_msg}

        except Exception as e:
            logger.error(f"Ошибка выполнения PowerShell-скрипта: {e}")
            return {"error": str(e)}

        finally:
            try:
                session.close()
            except Exception as e:
                logger.warning(f"Ошибка закрытия сессии: {e}")
