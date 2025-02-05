# windows_gui/rdp_management.py
import json
import logging
from typing import List

from old_project.windows_gui.system_info import execute_ps_script

logger = logging.getLogger(__name__)

# Константы
RDP_REGISTRY_PATH = r"HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server"
RDP_PORT_REGISTRY_PATH = r"HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"
RDP_GROUP = "Пользователи удаленного рабочего стола"
FIREWALL_RULE_NAME = "Удаленный рабочий стол - пользовательский режим (TCP-In)"


def is_rdp_enabled(session) -> bool:
    """Проверяет включен ли RDP с учетом реестра и брандмауэра"""
    ps_script = f'''
    $reg_status = (Get-ItemProperty -Path '{RDP_REGISTRY_PATH}').fDenyTSConnections -eq 0
    $port = (Get-ItemProperty -Path '{RDP_PORT_REGISTRY_PATH}').PortNumber
    $firewall = Get-NetFirewallRule -DisplayName "{FIREWALL_RULE_NAME}" |
                Where-Object {{ $_.Enabled -eq 'True' -and $_.LocalPort -eq $port }} |
                Measure-Object |
                Select-Object -ExpandProperty Count

    @{{ 
        Enabled = ($reg_status -and ($firewall -gt 0)) 
    }} | ConvertTo-Json
    '''

    try:
        result = execute_ps_script(session, ps_script)
        return result.get('Enabled', False)
    except Exception as e:
        logger.error(f"RDP check failed: {str(e)}")
        return False


def enable_rdp(session, enable: bool) -> None:
    """Включает/выключает RDP с автоматической настройкой брандмауэра"""
    state = 'enable' if enable else 'disable'
    logger.info(f"Attempting to {state} RDP...")

    ps_script = f'''
    $ErrorActionPreference = "Stop"

    # Обновление реестра
    Set-ItemProperty -Path '{RDP_REGISTRY_PATH}' -Name fDenyTSConnections -Value {int(not enable)}

    # Работа с портом
    $port = (Get-ItemProperty -Path '{RDP_PORT_REGISTRY_PATH}').PortNumber

    # Настройка брандмауэра
    $rule = Get-NetFirewallRule -DisplayName "{FIREWALL_RULE_NAME}" -ErrorAction SilentlyContinue

    if ({'$true' if enable else '$false'}) {{
        if (-not $rule) {{
            New-NetFirewallRule -DisplayName "{FIREWALL_RULE_NAME}" `
                -Direction Inbound `
                -Action Allow `
                -Protocol TCP `
                -LocalPort $port `
                -Enabled True
        }} else {{
            Set-NetFirewallRule -DisplayName "{FIREWALL_RULE_NAME}" `
                -Enabled True `
                -LocalPort $port
        }}
    }} else {{
        if ($rule) {{ Set-NetFirewallRule -DisplayName "{FIREWALL_RULE_NAME}" -Enabled False }}
    }}

    # Принудительное обновление
    gpupdate /force /wait:0 | Out-Null
    @{{ 'Success' = $true }} | ConvertTo-Json
    '''

    try:
        result = execute_ps_script(session, ps_script)
        if not result.get('Success', False):
            raise RuntimeError("Failed to apply RDP settings")
        logger.info(f"RDP {state}d successfully")
    except Exception as e:
        logger.error(f"RDP {state} failed: {str(e)}")
        raise RuntimeError(f"Не удалось {'включить' if enable else 'выключить'} RDP") from e


def get_rdp_port(session) -> int:
    """Возвращает текущий порт RDP"""
    ps_script = f'''
    (Get-ItemProperty -Path '{RDP_PORT_REGISTRY_PATH}').PortNumber | ConvertTo-Json
    '''

    try:
        result = execute_ps_script(session, ps_script)
        return int(result)
    except Exception as e:
        logger.error(f"Failed to get RDP port: {str(e)}")
        raise RuntimeError("Ошибка получения порта RDP") from e


def set_rdp_port(session, port: int) -> None:
    """Устанавливает новый порт для RDP"""
    if not 1 <= port <= 65535:
        raise ValueError("Некорректный номер порта")

    logger.info(f"Changing RDP port to {port}...")

    ps_script = f'''
    $ErrorActionPreference = "Stop"

    # Обновление порта в реестре
    Set-ItemProperty -Path '{RDP_PORT_REGISTRY_PATH}' -Name PortNumber -Value {port}

    # Обновление брандмауэра
    $rule = Get-NetFirewallRule -DisplayName "{FIREWALL_RULE_NAME}" -ErrorAction SilentlyContinue
    if ($rule) {{
        Set-NetFirewallRule -DisplayName "{FIREWALL_RULE_NAME}" -LocalPort {port}
    }} else {{
        New-NetFirewallRule -DisplayName "{FIREWALL_RULE_NAME}" `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalPort {port} `
            -Enabled True
    }}

    (Get-ItemProperty -Path '{RDP_PORT_REGISTRY_PATH}').PortNumber | ConvertTo-Json
    '''

    try:
        result = execute_ps_script(session, ps_script)
        if int(result) != port:
            raise RuntimeError("Port verification failed")
        logger.info(f"RDP port changed to {port} successfully")
    except Exception as e:
        logger.error(f"Port change failed: {str(e)}")
        raise RuntimeError("Ошибка изменения порта RDP") from e


def get_rdp_users(session) -> List[str]:
    """Возвращает список пользователей с доступом к RDP"""
    ps_script = f'''
    Get-LocalGroupMember -Group "{RDP_GROUP}" |
    Where-Object {{ 
        $_.ObjectClass -eq 'User' -and 
        $_.Name -notmatch '^(S-1-5-|NT AUTHORITY|BUILTIN)' 
    }} |
    ForEach-Object {{
        ($_.Name -split '\\\\')[-1].Trim()
    }} |
    Sort-Object -Unique |
    ConvertTo-Json -Compress
    '''

    try:
        result = execute_ps_script(session, ps_script)
        return json.loads(result) if isinstance(result, str) else result
    except Exception as e:
        logger.error(f"Failed to get RDP users: {str(e)}")
        return []


def add_rdp_user(session, username: str) -> None:
    """Добавляет пользователя в группу RDP"""
    logger.info(f"Adding user {username} to RDP group...")

    # Нормализация имени пользователя
    username = username.split('\\')[-1].strip()
    if not username:
        raise ValueError("Некорректное имя пользователя")

    ps_script = f'''
    $ErrorActionPreference = "Stop"

    # Проверка существования пользователя
    if (-not (Get-LocalUser -Name "{username}" -ErrorAction SilentlyContinue)) {{
        throw "Пользователь не существует"
    }}

    # Добавление в группу
    Add-LocalGroupMember -Group "{RDP_GROUP}" -Member "{username}" -ErrorAction Stop

    # Проверка результата
    Get-LocalGroupMember -Group "{RDP_GROUP}" |
    Where-Object {{ ($_.Name -split '\\\\')[-1] -eq "{username}" }} |
    Measure-Object |
    Select-Object -ExpandProperty Count |
    ConvertTo-Json
    '''

    try:
        result = execute_ps_script(session, ps_script)
        if int(result) < 1:
            raise RuntimeError("User not found after addition")
        logger.info(f"User {username} added successfully")
    except Exception as e:
        logger.error(f"Failed to add user: {str(e)}")
        raise RuntimeError(f"Ошибка добавления пользователя {username}") from e


def remove_rdp_user(session, username: str) -> None:
    """Удаляет пользователя из группы RDP"""
    logger.info(f"Removing user {username} from RDP group...")

    ps_script = f'''
    $ErrorActionPreference = "Stop"

    # Удаление из группы
    Remove-LocalGroupMember -Group "{RDP_GROUP}" -Member "{username}" -ErrorAction Stop

    # Проверка результата
    Get-LocalGroupMember -Group "{RDP_GROUP}" |
    Where-Object {{ ($_.Name -split '\\\\')[-1] -eq "{username}" }} |
    Measure-Object |
    Select-Object -ExpandProperty Count |
    ConvertTo-Json
    '''

    try:
        result = execute_ps_script(session, ps_script)
        if int(result) > 0:
            raise RuntimeError("User still exists in group")
        logger.info(f"User {username} removed successfully")
    except Exception as e:
        logger.error(f"Failed to remove user: {str(e)}")
        raise RuntimeError(f"Ошибка удаления пользователя {username}") from e