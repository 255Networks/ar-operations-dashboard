# AR Operations Dashboard
Malachi Pride · 255 Networks

**Open [dashboard.html](dashboard.html) locally** for the completed fictional operating review. The sample week begins with one open case and ends with three. One ticket closes twice after a reopening. Two of the three open tickets refer to the same invoice: the distinct open invoice balance is **USD 460**, compared with USD 860 if you sum the tickets.

## Reproduce the dashboard

With Python 3.10+ and no package installation, run `python3 build_dashboard.py` and `python3 -m unittest -v`. Edit `data.json` to explore another event sequence, then rebuild. If an event sequence is invalid, the compiler reports the problem.

## Metric definitions

| View | Basis |
| --- | --- |
| Weekly position | Opening backlog + first opens + reopens − closure events = ending backlog. A closure is counted once per close event. |
| Team | Closures belong to the owner at the instant of closure. Open workload uses the owner at period end. |
| Response and aging | First response is due within four business hours for tickets opened in the week. Pending cases are reported separately. Open age runs from the latest open or reopen. |
| Capacity | Closure events divided by available staffed hours. The small sample supports explanation of case mix and transfers. |
| Bottlenecks | Sum of marked hold time overlapping the report window, in weekday business hours. Cycle duration includes holds and is measured per completed open episode. |
| Financial exposure | Deduplicate USD face value by invoice reference across open cases. This operational exposure does not estimate collectability or losses. |
| Automation | Count reviewed AI suggestions recorded as confirmed or overridden. These are event counts, not model-accuracy labels. |

Times are UTC. Business time is 09:00–17:00 Monday–Friday, with no holiday calendar. The reporting interval includes the start and excludes the end. All case IDs, owners, balances, capacity and AI decisions were invented for this demo.
