"""Dependency-free SVG dashboard and a short operational review."""
from html import escape


def write_report(root, s, daily, firmware, failures, cfg, quality):
    def txt(x,y,t,size=16,color="#c6d2e3",weight=400):
        return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{weight}">{escape(str(t))}</text>'
    def rect(x,y,w,h,color,rx=16):
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{color}"/>'
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1080" viewBox="0 0 1440 1080">',
           rect(0,0,1440,1080,"#0b1220",0),rect(42,38,6,84,"#58dfb3",3),
           txt(68,58,"SMARTSWITCH / HOME AUTOMATION ANALYTICS",14,"#58dfb3",700),
           txt(68,103,"Small switches. Measurable performance.",34,"#f4f7fb",700),
           txt(68,135,f'{s["period_start"]} to {s["period_end"]}  |  {s["homes"]} homes  |  {s["devices"]} switches  |  SYNTHETIC DEMO DATA',16)]
    cards=[("COMMAND SUCCESS",f'{s["command_success_rate"]:.2%}',f'{s["commands"]:,} command acknowledgements'),
           ("P95 ACK LATENCY",f'{s["p95_latency_ms"]:,.0f} ms',"Successful commands; nearest-rank P95"),
           ("HEARTBEAT DELIVERY",f'{s["heartbeat_delivery_rate"]:.2%}',"Connectivity proxy; 5-minute intervals"),
           ("ESTIMATED ENERGY",f'{s["estimated_kwh"]:,.1f} kWh',"Rated watts x modeled runtime")]
    for i,(label,value,note) in enumerate(cards):
        x=48+i*348
        svg += [rect(x,170,328,137,"#162236"),txt(x+20,200,label,12,"#94a8c6",700),
                txt(x+20,246,value,31,"#f4f7fb",700),txt(x+20,279,note,12)]
    svg += [rect(48,331,844,337,"#111e30"),txt(72,368,"Daily command success",21,"#f4f7fb",700),
            txt(72,393,"Pooled daily successes / commands; target 98%",13)]
    left,top,w,h=100,423,746,185
    minrate=min(0.90,min(r["command_success_rate"] for r in daily)-0.005)
    for level in [minrate,0.94,0.96,0.98,1.0]:
        if level < minrate: continue
        y=top+h*(1-(level-minrate)/(1-minrate))
        svg += [f'<line x1="{left}" y1="{y}" x2="{left+w}" y2="{y}" stroke="#2b3b51" stroke-dasharray="3 5"/>',
                txt(62,y+4,f'{level:.0%}',11)]
    points=" ".join(f'{left+i*w/max(len(daily)-1,1):.1f},{top+h*(1-(r["command_success_rate"]-minrate)/(1-minrate)):.1f}' for i,r in enumerate(daily))
    svg += [f'<polyline points="{points}" fill="none" stroke="#58dfb3" stroke-width="3"/>']
    for i in [0,30,60,len(daily)-1]:
        svg.append(txt(left+i*w/max(len(daily)-1,1)-20,637,daily[i]["date"][5:],11))
    svg += [rect(916,331,476,337,"#111e30"),txt(940,368,"Firmware health",21,"#f4f7fb",700),
            txt(940,393,"Descriptive cohorts; rollout periods differ",13)]
    for i,row in enumerate(firmware):
        y=428+i*69
        color="#f2b969" if row["firmware_version"]=="1.1.0" else "#58dfb3"
        svg += [txt(940,y,row["firmware_version"],16,"#f4f7fb",700),
                txt(1280,y,f'{row["success_rate"]:.2%}',16,color,700),
                rect(940,y+12,420,12,"#26364b",6),rect(940,y+12,420*row["success_rate"],12,color,6),
                txt(940,y+44,f'{row["commands"]:,} commands',11)]
    svg += [rect(48,692,650,270,"#111e30"),txt(72,731,"What drives failures?",21,"#f4f7fb",700)]
    maxf=max(r["failures"] for r in failures)
    for i,row in enumerate(failures):
        y=774+i*57
        svg += [txt(72,y,row["failure_reason"].replace("_"," ").title(),14),
                rect(260,y-15,310*row["failures"]/maxf,19,"#f2b969",4),txt(594,y,f'{row["failures"]:,}',14,"#f4f7fb",700)]
    svg += [rect(722,692,670,270,"#111e30"),txt(746,731,"Energy with an explicit baseline",21,"#f4f7fb",700),
            txt(746,774,"Assumed baseline",16),txt(1130,774,f'{s["assumed_baseline_kwh"]:,.1f} kWh',20,"#f4f7fb",700),
            txt(746,817,"Modeled consumption",16),txt(1130,817,f'{s["estimated_kwh"]:,.1f} kWh',20,"#f4f7fb",700),
            txt(746,860,"Modeled difference",16),txt(1130,860,f'{s["modeled_avoided_kwh"]:,.1f} kWh',20,"#58dfb3",700),
            txt(746,914,"Estimated from load ratings and runtime. No metered savings claim.",13),
            txt(48,1006,f'DATA QUALITY   {quality["duplicate_commands"]+quality["duplicate_telemetry"]} exact duplicates removed   /   {quality["rejected_commands"]+quality["rejected_telemetry"]} invalid rows quarantined   /   full device-hour coverage',14),
            txt(48,1041,"SQL + Python report preview. The repository also includes a native Power BI project and an Excel reporting workbook.",12,"#94a8c6"),"</svg>"]
    (root/"reports/dashboard.svg").write_text("\n".join(svg))
    worst=min(firmware,key=lambda x:x["success_rate"])
    patch=next((r for r in firmware if r["firmware_version"]=="1.1.1"),None)
    text=f'''# Operational findings

Synthetic demonstration, {s["period_start"]} to {s["period_end"]}. These are generated observations, not customer results.

| Measure | Result | Interpretation |
|---|---:|---|
| Devices / homes | {s["devices"]} / {s["homes"]} | Fixed demo fleet |
| Valid command requests | {s["commands"]:,} | One row per logical command |
| Command success | {s["command_success_rate"]:.2%} | Successful device acknowledgement, not proof of physical actuation |
| P95 acknowledgement | {s["p95_latency_ms"]:.1f} ms | Successful commands only, exact nearest-rank definition |
| Heartbeat delivery | {s["heartbeat_delivery_rate"]:.2%} | Received / expected, not measured uptime |
| Estimated consumption | {s["estimated_kwh"]:,.2f} kWh | Rated watts times estimated relay-on hours |
| Modeled avoided consumption | {s["modeled_avoided_kwh"]:,.2f} kWh | Assumed baseline minus estimated consumption |

## Findings and actions

1. Firmware {worst["firmware_version"]} has the lowest success rate: {worst["success_rate"]:.2%} across {worst["commands"]:,} commands. Investigate the simulated relay errors. Compare treated and control switches over matching dates using SQL Q8 before discussing causality.
2. {failures[0]["failure_reason"]} contributes {failures[0]["failures"]:,} of {s["failures"]:,} failures ({failures[0]["failures"]/s["failures"]:.1%}). Inspect daily home connectivity and weak signal cohorts.
3. Firmware 1.1.1 has {patch["success_rate"]:.2%} success in its observed period. This is a descriptive comparison with a different time window and device mix.
4. The energy baseline is {s["assumed_baseline_kwh"]:,.2f} kWh. The modeled difference of {s["modeled_avoided_kwh"]:,.2f} kWh would correspond to INR {s["modeled_cost_difference_inr"]:,.2f} at an assumed flat INR {cfg["tariff_inr_per_kwh"]:.2f}/kWh. This excludes slabs, taxes and fixed charges, and is not a realized bill saving.
5. {s["alert_device_days"]:,} device-days trigger at least one rule. This count is distinct flagged device-days, not incidents or notifications. Deduplication, ownership and suppression would be needed before operating alerts.

## Data quality

{quality["duplicate_commands"]+quality["duplicate_telemetry"]} exact re-deliveries removed. {quality["rejected_commands"]+quality["rejected_telemetry"]} bad rows quarantined with reasons in `rejected_rows.json`. Both raw-to-clean row reconciliations balance. The complete device-hour grid preserves the expected-heartbeat denominator.
'''
    (root/"reports/findings.md").write_text(text)
