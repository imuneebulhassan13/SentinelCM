import time
from config.config import AGENT_VERSION, HEARTBEAT_INTERVAL
from system_info import get_system_information
from core.register import register_agent
from core.heartbeat import send_heartbeat
from core.api import post
from collectors.channels import WINDOWS_CHANNELS
from collectors.event_parser import parse_event
from collectors.fim import scan_and_send_fim
from collectors.queue_manager import add_to_queue, flush_queue
from config.config_manager import config_exists, load_config, save_config

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
        "agent_version": AGENT_VERSION,
    }
    response = register_agent(payload)
    agent_id = response["agent_id"]
    save_config({"agent_id": agent_id})
    print("New Agent Registered")

MONITORED_DIRS = [r"C:\Windows\System32\drivers\etc"]

while True:
    # 1. First attempt to flush any offline buffered logs if backend is up
    flush_queue(post)

    result = send_heartbeat(agent_id)
    if result:
        print(result)
    else:
        print("[Agent] Backend unreachable. Logs will be queued locally...")

    # 2. Run File Integrity Check
    try:
        print("\n[FIM] Running file integrity check...")
        scan_and_send_fim(agent_id, MONITORED_DIRS)
    except Exception as e:
        print(f"[FIM Loop Error]: {e}")

    # 3. Read & Send Windows Event Logs
    from collectors.windows_events import read_events

    # Read & Send Windows Event Logs section inside agent/main.py
    for channel in WINDOWS_CHANNELS:
        try:
            events = read_events(channel)
            if len(events) > 0:
                print(f"{channel}: {len(events)} new event(s)")

            for event in events:
                parsed_log = parse_event(event, agent_id, channel)

                try:
                    res = post("/logs/", parsed_log)
                    if not res:
                        add_to_queue({"endpoint": "/logs/", "payload": parsed_log})
                    else:
                        print(f"{channel} Event {event.RecordNumber} sent successfully")
                except Exception:
                    # Direct Exception catch on network connection failure
                    add_to_queue({"endpoint": "/logs/", "payload": parsed_log})

        except Exception as e:
            print(f"{channel} Error: {e}")

    time.sleep(10)