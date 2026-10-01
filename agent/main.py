import time

from config.config import AGENT_VERSION, HEARTBEAT_INTERVAL
from system_info import get_system_information
from core.register import register_agent
from core.heartbeat import send_heartbeat
from core.api import post
from collectors.channels import WINDOWS_CHANNELS
from collectors.event_parser import parse_event
from collectors.fim import scan_and_send_fim
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

# FIM Directories to Monitor
MONITORED_DIRS = [
    r"C:\Windows\System32\drivers\etc"
]

while True:
    result = send_heartbeat(agent_id)
    if result:
        print(result)
    else:
        print("[Agent] Backend unreachable or timed out. Will retry in next loop...")

    # --- 1. Run File Integrity Scan (FIM) ---
    try:
        print("\n[FIM] Running file integrity check...")
        scan_and_send_fim(agent_id, MONITORED_DIRS)
    except Exception as e:
        print(f"[FIM Loop Error]: {e}")

    # --- 2. Read Windows Event Logs ---
    from collectors.windows_events import read_events

    for channel in WINDOWS_CHANNELS:
        try:
            events = read_events(channel)
            print(f"{channel}: {len(events)} new event(s)")

            for event in events:
                parsed_log = parse_event(
                    event,
                    agent_id,
                    channel
                )

                result = post(
                    "/logs/",
                    parsed_log
                )

                print(
                    f"{channel} Event {event.RecordNumber} sent:",
                    result
                )

        except Exception as e:
            print(f"{channel} Error: {e}")

    from state.state_manager import load_state
    print(load_state())

    time.sleep(10)