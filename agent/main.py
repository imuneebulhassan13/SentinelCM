import time

from config.config import AGENT_VERSION, HEARTBEAT_INTERVAL

from system_info import get_system_information

from core.register import register_agent

from core.heartbeat import send_heartbeat

from core.api import post

from collectors.channels import WINDOWS_CHANNELS

from config.config_manager import (
    config_exists,
    load_config,
    save_config
)


if config_exists():

    config = load_config()

    agent_id = config["agent_id"]

    print(f"Existing Agent: {agent_id}")

else:

    system = get_system_information()

    payload = {
        "hostname": system["hostname"],
        "ip_address": system["ip_address"],
        "operating_system": system["operating_system"],
        "agent_version": AGENT_VERSION
    }

    response = register_agent(payload)

    agent_id = response["agent_id"]

    save_config(
        {
            "agent_id": agent_id
        }
    )

    print("New Agent Registered")


while True:

    result = send_heartbeat(agent_id)

    print(result)

    time.sleep(HEARTBEAT_INTERVAL)

    
#test   
    from collectors.windows_events import read_events


    for channel in WINDOWS_CHANNELS:

        try:
            events = read_events(channel)

            print(f"{channel}: {len(events)} new event(s)")

            for event in events:
                print("-" * 60)
                print("Channel :", channel)
                print("Record :", event.RecordNumber)

        except Exception as e:
            print(f"{channel} Error: {e}")

    from state.state_manager import load_state

    print(load_state())