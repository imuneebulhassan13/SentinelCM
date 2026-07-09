from system_info import get_system_information

from register import register_agent

from config import AGENT_VERSION


system = get_system_information()

payload = {
    "hostname": system["hostname"],
    "ip_address": system["ip_address"],
    "operating_system": system["operating_system"],
    "agent_version": AGENT_VERSION
}

response = register_agent(payload)

print(response)