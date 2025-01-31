import wmi


def get_active_users(ip):
    c = wmi.WMI(computer=ip)
    users = c.query('SELECT * FROM Win32_ComputerSystem')
    for user in users:
        print(f"User: {user.UserName}")


ip = "10.254.44.37"
get_active_users(ip)
