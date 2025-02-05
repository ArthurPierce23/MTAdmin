import logging
import json
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan

logger = logging.getLogger(__name__)

class SystemInfo:
    def __init__(self, hostname: str):
        self.hostname = hostname
        # Убираем создание сессии в конструкторе, чтобы не делиться объектом между потоками.
        # self.session = self._init_ps_session()

    def _init_ps_session(self) -> RunspacePool | None:
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
            logger.error(f"Connection Error: {str(e)}")
            return None

    def get_system_info(self) -> dict:
        # Создаем сессию непосредственно в этом методе.
        session = self._init_ps_session()
        if not session:
            return {"error": "WinRM connection failed"}

        ps_script = r"""
$ErrorActionPreference = "Stop"
try {
    # CPU Information
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    $cpu_load = if ($cpu.LoadPercentage) { $cpu.LoadPercentage } else { $null }

    # RAM Information
    $os = Get-CimInstance Win32_OperatingSystem
    $ram_total = if ($os.TotalVisibleMemorySize) { [math]::Round($os.TotalVisibleMemorySize/1MB, 2) } else { 0 }
    $ram_free = if ($os.FreePhysicalMemory) { [math]::Round($os.FreePhysicalMemory/1MB, 2) } else { 0 }

    # Disk Information
    $disks = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
        $total = if ($_.Size) { [math]::Round($_.Size/1GB, 2) } else { 0 }
        $free = if ($_.FreeSpace) { [math]::Round($_.FreeSpace/1GB, 2) } else { 0 }

        [PSCustomObject]@{
            Letter = $_.DeviceID
            TotalGB = $total
            FreeGB = $free
            UsedGB = [math]::Round($total - $free, 2)
            UsedPercent = if ($total -gt 0) { [math]::Round(($total - $free)/$total*100, 2) } else { 0 }
        }
    }

    # Prepare result
    [PSCustomObject]@{
        CPU = @{
            Load = $cpu_load
            Cores = $cpu.NumberOfLogicalProcessors
        }
        RAM = @{
            TotalGB = $ram_total
            FreeGB = $ram_free
            UsedGB = [math]::Round($ram_total - $ram_free, 2)
            UsedPercent = if ($ram_total -gt 0) { [math]::Round(($ram_total - $ram_free)/$ram_total*100, 2) } else { 0 }
        }
        Disks = $disks
    } | ConvertTo-Json -Depth 3 -Compress
}
catch {
    [PSCustomObject]@{
        Error = $_.Exception.Message
        Details = $_.ScriptStackTrace
    } | ConvertTo-Json -Compress
}
"""
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
            error_msg = f"JSON parsing error: {str(e)}\nRaw output: {json_str}"
            logger.error(error_msg)
            return {"error": error_msg}

        except Exception as e:
            logger.error(f"Execution Error: {str(e)}")
            return {"error": str(e)}
        finally:
            # Закрываем сессию, если она была успешно создана
            try:
                session.close()
            except Exception:
                pass
