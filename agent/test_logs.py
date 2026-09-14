from collectors.windows_events import read_events
from collectors.channels import WINDOWS_CHANNELS

for channel in WINDOWS_CHANNELS:

    print(f"\n===== {channel} Logs =====")

    try:
        logs = read_events(channel)

        print(f"Total New Logs: {len(logs)}")

        for event in logs[:5]:
            print("-----------------------")
            print("Record :", event.RecordNumber)
            print("Event ID :", event.EventID)
            print("Source :", event.SourceName)
            print("Time :", event.TimeGenerated)

    except Exception as e:
        print(f"{channel} Error: {e}")