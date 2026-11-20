"""Render a self-contained dashboard from local, fictional AR events."""
import html
import json
from pathlib import Path

from metrics import metrics

ROOT = Path(__file__).resolve().parent


def e(value):
    return html.escape(str(value), quote=True)


def table(headers, rows):
    cols = "".join(f"<th scope='col'>{e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{e(v)}</td>" for v in row) + "</tr>" for row in rows)
    return f"<div class='scroll'><table><thead><tr>{cols}</tr></thead><tbody>{body}</tbody></table></div>"


def panel(anchor, title, body):
    return f"<section id='{anchor}'><h2>{e(title)}</h2>{body}</section>"


def usd(amount):
    return f"${amount:,.2f}"


def build(data):
    m = metrics(data)
    navigation = [("position","Position"),("team","Team"),("response","Response"),("capacity","Capacity"),
                  ("delays","Bottlenecks"),("exposure","Exposure"),("automation","Automation")]
    nav = "".join(f"<a href='#{k}'>{label}</a>" for k,label in navigation)
    scorecards = [("Ending backlog",m["ending"],"open cases"),("Closure events",m["closures"],"in the window"),
                  ("Open invoice value",usd(m["unique_exposure"]),"distinct invoices in USD")]
    cards = "".join(f"<div><span>{a}</span><strong>{b}</strong><small>{c}</small></div>" for a,b,c in scorecards)
    sections = []
    sections.append(panel("position","Weekly position",f"<p class='formula'>{m['opening']} opening + {m['new']} new + {m['reopened']} reopened − {m['closures']} closed = <b>{m['ending']} ending</b></p>"))
    team = sorted(m["team"].items())
    sections.append(panel("team","Team workload",table(["Queue","Closures at time of close","Open at week end"],
                           [(k,v["closures"],v["open"]) for k,v in team])))
    resp = m["responses"]
    sections.append(panel("response","Response and aging",table(["First response outcome","New tickets"],
                           [(k.title(),resp.get(k,0)) for k in ("met","missed","pending")]) +
                           "<p>First response target: four business hours. Open case ages appear in the exposure view.</p>"))
    sections.append(panel("capacity","Staffed capacity",table(["Queue","Available hours","Closures per staffed hour"],
                          [(k,v["hours"],f"{v['closures']/v['hours']:.2f}") for k,v in team]) +
                          "<p>Use volume and case mix alongside this rate when interpreting a small sample.</p>"))
    cycle = "No completed episode" if m["median_cycle"] is None else f"{m['median_cycle']:g} business hours"
    sections.append(panel("delays","Process bottlenecks",table(["Measure","Observed"],
                          [("Marked hold time in window",f"{m['waiting']:g} business hours"),("Median closed episode duration",cycle)]) +
                          "<p>A ticket can have several episodes. Each reopen starts a new episode.</p>"))
    options = "".join(f"<option value='{e(k)}'>{e(k)}</option>" for k in m["team"])
    rows = "".join(f"<tr data-owner='{e(r['owner'])}' data-invoice='{e(r['invoice'])}' data-usd='{e(r['usd'])}'>" +
                   "".join(f"<td>{e(x)}</td>" for x in (r["ticket"],r["owner"],r["invoice"],usd(r["usd"]),f"{r['age']:g}"))+
                   "</tr>" for r in m["open_cases"])
    grid = "<div class='scroll'><table id='cases'><thead><tr>"+"".join(f"<th scope='col'>{x}</th>" for x in
           ["Open ticket","Owner","Invoice","USD face value","Age in business hours"])+"</tr></thead><tbody>"+rows+"</tbody></table></div>"
    sections.append(panel("exposure","Open financial exposure",f"<label>Queue <select id='queue'><option value=''>All queues</option>{options}</select></label>"+grid+
                          f"<p id='subtotal' aria-live='polite'>{m['ending']} tickets · {m['invoices']} distinct invoices · {usd(m['unique_exposure'])}</p>"))
    auto = m["automation"]
    sections.append(panel("automation","Automation decisions",table(["Recorded reviewer action","Suggestions"],
                          [("Confirmed",auto.get("ai_confirm",0)),("Overridden",auto.get("ai_override",0))]) +
                          "<p>The event log records the reviewer’s response. Independent QA would be required to measure decision accuracy.</p>"))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AR Operations Dashboard · 255 Networks</title><style>{STYLE}</style></head>
<body><main><header><p class="eyebrow">255 Networks · Finance operations</p><h1>Receivables review</h1>
<p>{e(data['start'])} to {e(data['end'])} UTC · Fictional operating data</p></header><div class="metrics">{cards}</div>
<nav aria-label="Dashboard views">{nav}</nav>{''.join(sections)}<footer>Malachi Pride · See README.md for period, attribution and calculation conventions.</footer></main>
<script>{SCRIPT}</script></body></html>"""


STYLE = """
:root{color-scheme:light;--ink:#182f33;--line:#c9d6cf;--teal:#185e55}
*{box-sizing:border-box}body{margin:0;background:#f6f6ef;color:var(--ink);font:16px/1.55 "DM Sans",system-ui,sans-serif}
main{max-width:1020px;margin:auto;padding:36px 25px 70px}header{padding:20px 0 24px}header p{margin:6px 0;color:#455e5a}
.eyebrow{font-weight:650;letter-spacing:.03em}h1,h2{font-family:"Instrument Serif",Georgia,serif;font-weight:normal}
h1{font-size:clamp(40px,7vw,72px);line-height:1;margin:15px 0}h2{margin:0 0 15px;font-size:32px;line-height:1.15}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);background:#184a46;color:white;border-radius:12px;overflow:hidden}
.metrics div{padding:20px;display:grid;border-right:1px solid #507773}.metrics strong{font-size:clamp(24px,5vw,42px);font-variant-numeric:tabular-nums}
.metrics small{color:#cee2d8}nav{padding:22px 0;display:flex;flex-wrap:wrap;gap:8px}nav a{color:var(--teal);background:#e3eae2;border-radius:5px;padding:5px 11px}
section{scroll-margin-top:18px;border-top:1px solid var(--line);padding:27px 0}section p,footer{color:#425a55}.formula{font-size:1.18rem}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{padding:9px 12px;border-bottom:1px solid #dbe2d9;text-align:left}th{background:#eaf0e7}
.scroll{overflow-x:auto}label{display:inline-block;margin-bottom:13px;font-weight:650}select{padding:6px;font:inherit}footer{margin-top:24px}
@media(max-width:600px){main{padding:20px 14px}.metrics{grid-template-columns:1fr}.metrics div{padding:11px 15px;border-bottom:1px solid #507773}.metrics strong{font-size:30px}th,td{min-width:88px}}
"""
SCRIPT = """
const queue = document.getElementById('queue');
queue.addEventListener('change', () => {
  const invoices = new Map();
  let tickets = 0;
  for (const row of document.querySelectorAll('#cases tbody tr')) {
    row.hidden = Boolean(queue.value && queue.value !== row.dataset.owner);
    if (!row.hidden) {
      tickets += 1;
      invoices.set(row.dataset.invoice, Number(row.dataset.usd));
    }
  }
  const total = Array.from(invoices.values()).reduce((sum, value) => sum + value, 0);
  const formatted = new Intl.NumberFormat('en-US', {style:'currency',currency:'USD'}).format(total);
  const ticketLabel = tickets === 1 ? ' ticket' : ' tickets';
  const invoiceLabel = invoices.size === 1 ? ' distinct invoice' : ' distinct invoices';
  document.getElementById('subtotal').textContent = tickets + ticketLabel + ' · ' + invoices.size + invoiceLabel + ' · ' + formatted;
});
"""

if __name__ == "__main__":
    data = json.loads((ROOT / "data.json").read_text())
    (ROOT / "dashboard.html").write_text(build(data),encoding="utf-8")
