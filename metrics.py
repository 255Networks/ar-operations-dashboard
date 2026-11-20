"""Replay an invented receivables event log into weekly operational metrics."""
from collections import Counter
from datetime import datetime, time, timedelta
from statistics import median


def moment(value):
    return datetime.fromisoformat(value)


def business_hours(start, end):
    if end < start:
        raise ValueError("End precedes start")
    total = timedelta()
    day = start.date()
    while day <= end.date():
        if day.weekday() < 5:
            opened = max(start, datetime.combine(day, time(9)))
            closed = min(end, datetime.combine(day, time(17)))
            if closed > opened:
                total += closed - opened
        day += timedelta(days=1)
    return total.total_seconds() / 3600


def metrics(data):
    start, end = moment(data["start"]), moment(data["end"])
    if end <= start:
        raise ValueError("Reporting window must have positive duration")
    team = {name: {"hours": hours, "closures": 0, "open": 0} for name, hours in data["capacity_hours"].items()}
    if any(v["hours"] <= 0 for v in team.values()):
        raise ValueError("Capacity hours must be positive")
    opening = new = reopened = closures = 0
    waits, cycles, open_cases, balances = [], [], [], {}
    responses, automation = Counter(), Counter()
    ids = [t["id"] for t in data["tickets"]]
    if len(set(ids)) != len(ids):
        raise ValueError("Repeated ticket ID")
    amounts = {}
    for ticket in data["tickets"]:
        inv = ticket["invoice"]
        if inv in amounts and amounts[inv] != ticket["usd"]:
            raise ValueError("Conflicting amounts for a shared invoice")
        amounts[inv] = ticket["usd"]
        active = ever_opened = False
        owner = episode = created = response = hold = previous = None
        for stamp, action, value in ticket["events"]:
            at = moment(stamp)
            if previous is not None and at < previous:
                raise ValueError("Events must be chronological within a ticket")
            previous = at
            if at >= end:
                break
            inside = at >= start
            if action == "open":
                if ever_opened or value not in team:
                    raise ValueError("Invalid ticket opening or owner")
                active = ever_opened = True
                owner, created, episode = value, at, at
                if inside:
                    new += 1
                else:
                    opening += 1
                continue
            if action == "reopen":
                if active or not ever_opened:
                    raise ValueError("Only a closed ticket can reopen")
                active, episode = True, at
                if inside:
                    reopened += 1
                else:
                    opening += 1
                continue
            if not active:
                raise ValueError("Event requires an active ticket")
            if action == "assign":
                if value not in team:
                    raise ValueError("Unknown assigned owner")
                owner = value
            elif action == "reply":
                if response is None:
                    response = at
            elif action == "hold":
                if hold is not None:
                    raise ValueError("Duplicate hold")
                hold = at
            elif action == "resume":
                if hold is None:
                    raise ValueError("Resume requires a hold")
                if at > start:
                    waits.append(business_hours(max(hold, start), at))
                hold = None
            elif action == "close":
                if hold is not None:
                    raise ValueError("Resume before closure")
                active = False
                if inside:
                    closures += 1
                    team[owner]["closures"] += 1
                    cycles.append(business_hours(episode, at))
                else:
                    opening -= 1
            elif action in ("ai_confirm", "ai_override"):
                if inside:
                    automation[action] += 1
            else:
                raise ValueError(f"Unknown event {action}")
        if created and start <= created < end:
            if response:
                responses["met" if business_hours(created, response) <= 4 else "missed"] += 1
            elif business_hours(created, end) > 4:
                responses["missed"] += 1
            else:
                responses["pending"] += 1
        if active:
            if hold is not None:
                waits.append(business_hours(max(hold, start), end))
            team[owner]["open"] += 1
            balances[inv] = ticket["usd"]
            open_cases.append({"ticket":ticket["id"], "owner":owner, "invoice":inv, "usd":ticket["usd"],
                               "age":business_hours(episode, end)})
    if opening + new + reopened - closures != len(open_cases):
        raise ValueError("Backlog did not reconcile")
    return {"opening":opening, "new":new, "reopened":reopened, "closures":closures, "ending":len(open_cases),
            "median_cycle":median(cycles) if cycles else None, "waiting":sum(waits),
            "responses":dict(responses), "automation":dict(automation), "team":team,
            "open_cases":open_cases, "unique_exposure":sum(balances.values()), "invoices":len(balances)}
