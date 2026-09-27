# -*- coding: utf-8 -*-
"""Rozwija publiczny kalendarz Google „Nowa ramówka” (iCal) na wystąpienia: tydzień po tygodniu od pierwszego wpisu do dziś.
Wynik: wystapienia.json  [{"d": "2026-09-21", "wd": 0, "start": "07:07", "koniec": "09:00", "nazwa": ..., "uid": ..., "seria": true}]
    python rozwin.py ramowka_2026-09-27.ics"""
import datetime as dt
import json
import os
import sys

import icalendar
import recurring_ical_events
from zoneinfo import ZoneInfo

TU = os.path.dirname(os.path.abspath(__file__))
WAW = ZoneInfo("Europe/Warsaw")


def main():
    cal = icalendar.Calendar.from_ical(open(sys.argv[1], "rb").read())
    pierwszy = min(e.decoded("DTSTART") for e in cal.walk("VEVENT") if isinstance(e.decoded("DTSTART"), dt.datetime))
    od = pierwszy.astimezone(WAW).date() if pierwszy.tzinfo else pierwszy.date()
    do = dt.date(2026, 10, 5)
    out = []
    for e in recurring_ical_events.of(cal).between(od, do):
        s, k = e.decoded("DTSTART"), e.decoded("DTEND") if e.get("DTEND") else None
        if not isinstance(s, dt.datetime):
            continue                                    # wpisy całodniowe (notatki, święta) pomijamy
        s = s.astimezone(WAW) if s.tzinfo else s
        k = (k.astimezone(WAW) if k.tzinfo else k) if isinstance(k, dt.datetime) else s + dt.timedelta(hours=1)
        out.append({"d": s.date().isoformat(), "wd": s.weekday(), "start": s.strftime("%H:%M"), "koniec": k.strftime("%H:%M"),
                    "min": int((k - s).total_seconds() // 60), "nazwa": str(e.get("SUMMARY", "")).strip(), "uid": str(e.get("UID")),
                    "seria": bool(e.get("RRULE") or e.get("RECURRENCE-ID"))})
    out.sort(key=lambda x: (x["d"], x["start"]))
    json.dump(out, open(os.path.join(TU, "wystapienia.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(len(out), "wystąpień", od, "→", out[-1]["d"])


if __name__ == "__main__":
    main()
