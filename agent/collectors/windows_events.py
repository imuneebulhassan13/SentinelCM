import win32evtlog


def read_events(limit=10):

    server = "localhost"

    log_type = "System"

    hand = win32evtlog.OpenEventLog(server, log_type)

    flags = (
        win32evtlog.EVENTLOG_BACKWARDS_READ
        | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    )

    events = []

    total = 0

    while total < limit:

        records = win32evtlog.ReadEventLog(
            hand,
            flags,
            0
        )

        if not records:
            break

        for event in records:

            events.append(event)

            total += 1

            if total >= limit:
                break

    win32evtlog.CloseEventLog(hand)

    return events