from collectors.windows_events import read_application_logs

logs = read_application_logs()

print(f"Total Logs: {len(logs)}")

for log in logs:

    print("-----------------------")

    print(log.EventID)

    print(log.SourceName)

    print(log.TimeGenerated)