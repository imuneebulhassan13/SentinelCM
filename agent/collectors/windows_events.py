import win32evtlog

from state.state_manager import (
    load_state,
    save_state,
)


def read_events(channel):

    state = load_state()

    last_record = state.get(channel, 0)

    server = "localhost"

    handle = win32evtlog.OpenEventLog(
        server,
        channel
    )

    flags = (
        win32evtlog.EVENTLOG_BACKWARDS_READ
        | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    )

    new_events = []

    highest_record = last_record

    while True:

        records = win32evtlog.ReadEventLog(
            handle,
            flags,
            0
        )

        if not records:
            break

        stop = False

        for event in records:

            record = event.RecordNumber

            if record <= last_record:
                stop = True
                break

            new_events.append(event)

            if record > highest_record:
                highest_record = record

        if stop:
            break

    win32evtlog.CloseEventLog(handle)

    if highest_record > last_record:
        save_state(
            channel,
            highest_record
        )

    new_events.reverse()

    return new_events