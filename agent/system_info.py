import socket
import platform


def get_system_information():

    hostname = socket.gethostname()

    ip_address = socket.gethostbyname(hostname)

    operating_system = (
        platform.system()
        + " "
        + platform.release()
    )

    return {
        "hostname": hostname,
        "ip_address": ip_address,
        "operating_system": operating_system,
    }