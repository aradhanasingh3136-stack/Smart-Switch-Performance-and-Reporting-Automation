"""Build source-controlled PBIP/PBIR assets. No Power BI installation required to author.

Use Power BI Desktop on Windows to refresh, check visuals, and save a PBIX.
This builder is for the supplied report and will overwrite its generated definition.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://developer.microsoft.com/json-schemas/fabric/item/"


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2)+"\n", encoding="utf-8")


def build():
    pbi=ROOT/"powerbi"
    modeldir=pbi/"SmartSwitch.SemanticModel"
    reportdir=pbi/"SmartSwitch.Report"
    dump(pbi/"SmartSwitch.pbip",{"$schema":BASE+"report/definition/pbip/1.0.0/schema.json",
         "version":"1.0","artifacts":[{"report":{"path":"SmartSwitch.Report"}}],"settings":{"enableAutoRecovery":True}})
    # PBIP root schema lives under powerbi/pbip, unlike report definition schemas.
    root=json.loads((pbi/"SmartSwitch.pbip").read_text())
    root["$schema"]="https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json"
    dump(pbi/"SmartSwitch.pbip",root)
    dump(reportdir/"definition.pbir",{"$schema":BASE+"report/definitionProperties/2.0.0/schema.json",
         "version":"4.0","datasetReference":{"byPath":{"path":"../SmartSwitch.SemanticModel"}}})
    dump(modeldir/"definition.pbism",{"$schema":BASE+"semanticModel/definitionProperties/1.0.0/schema.json",
         "version":"4.0","settings":{}})
    specs={
      "dim_device":[("device_id","string"),("home_id","string"),("room","string"),("load_type","string"),
                    ("rated_watts","double"),("baseline_daily_hours","double"),("installed_date","dateTime"),("model","string")],
      "dim_date":[("date","dateTime"),("month","string"),("weekday","string"),("is_weekend","int64")],
      "fact_command":[("command_id","string"),("device_id","string"),("event_time","dateTime"),("date","dateTime"),
                      ("firmware_version","string"),("source","string"),("action","string"),("status","string"),
                      ("failure_reason","string"),("latency_ms","double")],
      "fact_device_hour":[("device_id","string"),("hour_start","dateTime"),("date","dateTime"),("firmware_version","string"),
                          ("expected_heartbeats","int64"),("received_heartbeats","int64"),("wifi_rssi_dbm","double"),
                          ("on_hours","double"),("estimated_kwh","double")]
    }
    mtypes={"string":"type text","double":"type number","int64":"Int64.Type","dateTime":"type datetime"}
    tables=[]
    query_docs=[]
    for name,columns in specs.items():
        transforms=", ".join('{"'+n+'", '+('type date' if n in {"date","installed_date"} else mtypes[t])+'}' for n,t in columns)
        query=["let",f'    Source = Csv.Document(File.Contents(DataFolder & "/{name}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
               "    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
               '    MissingToNull = Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),',
               f'    Typed = Table.TransformColumnTypes(MissingToNull, {{{transforms}}}, "en-US")',"in","    Typed"]
        table={"name":name,"columns":[{"name":n,"dataType":t,"sourceColumn":n,"summarizeBy":"none",
                  **({"formatString":"yyyy-mm-dd"} if n in {"date","installed_date"} else {})} for n,t in columns],
               "partitions":[{"name":name,"mode":"import","source":{"type":"m","expression":query}}]}
        tables.append(table)
        query_docs += [f"// Query: {name}","\n".join(query),""]
    tables.append({"name":"dim_firmware","columns":[{"name":"firmware_version","dataType":"string","sourceColumn":"firmware_version","summarizeBy":"none"}],
                   "partitions":[{"name":"dim_firmware","mode":"import","source":{"type":"m","expression":
                   ['#table(type table [firmware_version = text], {{"1.0.2"}, {"1.1.0"}, {"1.1.1"}})']}}]})
    cfg=json.loads((ROOT/"config.json").read_text())
    measures=[
      ("Commands","COUNTROWS('fact_command')","#,0"),
      ("Successful Commands",'CALCULATE([Commands], KEEPFILTERS(\'fact_command\'[status] = "SUCCESS"))',"#,0"),
      ("Failed Commands",'CALCULATE([Commands], KEEPFILTERS(\'fact_command\'[status] <> "SUCCESS"))',"#,0"),
      ("Command Success %","DIVIDE([Successful Commands], [Commands])","0.00%"),
      ("Average Ack ms",'CALCULATE(AVERAGE(\'fact_command\'[latency_ms]), KEEPFILTERS(\'fact_command\'[status] = "SUCCESS"))',"0.0"),
      ("P95 Ack ms",'''VAR Good = FILTER('fact_command', 'fact_command'[status] = "SUCCESS" && NOT ISBLANK('fact_command'[latency_ms]))
VAR N = COUNTROWS(Good)
RETURN IF(N = 0, BLANK(), MAXX(TOPN(ROUNDUP(0.95 * N, 0), Good, 'fact_command'[latency_ms], ASC, 'fact_command'[command_id], ASC), 'fact_command'[latency_ms]))''',"0.0"),
      ("Heartbeat Delivery %","DIVIDE(SUM('fact_device_hour'[received_heartbeats]), SUM('fact_device_hour'[expected_heartbeats]))","0.00%"),
      ("Estimated kWh","SUM('fact_device_hour'[estimated_kwh])","#,0.0"),
      ("Assumed Baseline kWh","SUMX('fact_device_hour', RELATED('dim_device'[rated_watts]) * RELATED('dim_device'[baseline_daily_hours]) / 24000)","#,0.0"),
      ("Modeled Avoided kWh","[Assumed Baseline kWh] - [Estimated kWh]","#,0.0"),
      ("Modeled Cost Difference INR",f'[Modeled Avoided kWh] * {cfg["tariff_inr_per_kwh"]}',"#,0.00"),
      ("Reporting Devices","DISTINCTCOUNT('fact_device_hour'[device_id])","#,0"),
      ("Success 7D %","CALCULATE([Command Success %], DATESINPERIOD('dim_date'[date], MAX('dim_date'[date]), -7, DAY))","0.00%"),
      ("Slow Successful Commands",f'CALCULATE([Successful Commands], KEEPFILTERS(\'fact_command\'[latency_ms] > {cfg["slow_ack_threshold_ms"]}))',"#,0")
    ]
    tables[2]["measures"]=[{"name":n,"expression":e.splitlines(),"formatString":f,"displayFolder":"SmartSwitch KPIs"} for n,e,f in measures]
    rel=[]
    for fact in ["fact_command","fact_device_hour"]:
        for dim,key in [("dim_device","device_id"),("dim_date","date"),("dim_firmware","firmware_version")]:
            rel.append({"name":f'{fact}_{dim}',"fromTable":fact,"fromColumn":key,"toTable":dim,"toColumn":key,
                        "fromCardinality":"many","toCardinality":"one","crossFilteringBehavior":"oneDirection"})
    model={"name":"SmartSwitch","compatibilityLevel":1600,"model":{"culture":"en-US", "defaultPowerBIDataSourceVersion":"powerBI_V3",
           "expressions":[{"name":"DataFolder","kind":"m","expression":'"C:/CHANGE_ME/smartswitch-analytics/data/processed" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],
           "tables":tables,"relationships":rel,"annotations":[{"name":"PBI_TimeIntelligenceEnabled","value":"0"}]}}
    dump(modeldir/"model.bim",model)
    (pbi/"PowerQuery.m").write_text('// Create a Text parameter named DataFolder containing the absolute data/processed path.\n\n'+"\n".join(query_docs))
    (pbi/"Measures.dax").write_text("// Reference definitions: measures are already included in model.bim.\n\n"+"\n\n".join(f'{n} :=\n{e}' for n,e,f in measures)+"\n")
    theme={"name":"SmartSwitch","dataColors":["#1976B9","#249E79","#E5A442","#A46AB9","#D46767"],
           "background":"#F3F6FA","foreground":"#152C4A","tableAccent":"#1976B9"}
    dump(pbi/"theme.json",theme)
    definition=reportdir/"definition"
    dump(definition/"version.json",{"$schema":BASE+"report/definition/versionMetadata/1.0.0/schema.json","version":"4.0.0"})
    dump(definition/"report.json",{"$schema":BASE+"report/definition/report/1.0.0/schema.json","layoutOptimization":"None",
         "themeCollection":{"baseTheme":{"name":"CY24SU06","reportVersionAtImport":"5.55","type":"SharedResources"}}})
    pages=[("overview","Overview (synthetic data)"),("reliability","Reliability and firmware"),("energy","Estimated energy and usage")]
    dump(definition/"pages/pages.json",{"$schema":BASE+"report/definition/pagesMetadata/1.0.0/schema.json","pageOrder":[p[0] for p in pages],"activePageName":"overview"})
    def field(table,prop,measure=False):
        return {"Measure" if measure else "Column":{"Expression":{"SourceRef":{"Entity":table}},"Property":prop}}
    def proj(table,prop,measure=False):
        return {"field":field(table,prop,measure),"queryRef":table+"."+prop,"nativeQueryRef":prop}
    def visual(page,name,kind,x,y,w,h,title,roles):
        content={"$schema":BASE+"report/definition/visualContainer/2.1.0/schema.json","name":page+"_"+name,
                 "position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":y+x},
                 "visual":{"visualType":kind,"query":{"queryState":{k:{"projections":v} for k,v in roles.items()}},
                 "visualContainerObjects":{"title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},
                                          "text":{"expr":{"Literal":{"Value":"'"+title.replace("'","''")+"'"}}}}}],
                 "general":[{"properties":{"altText":{"expr":{"Literal":{"Value":"'Synthetic demo: "+title+"'"}}}}}]},
                 "drillFilterOtherVisuals":True}}
        dump(definition/f"pages/{page}/visuals/{page}_{name}/visual.json",content)
    def m(name): return proj("fact_command",name,True)
    for page,title in pages:
        dump(definition/f"pages/{page}/page.json",{"$schema":BASE+"report/definition/page/1.0.0/schema.json","name":page,"displayName":title,"displayOption":"FitToPage","width":1280,"height":720})
        visual(page,"home","slicer",24,8,250,70,"Home",{"Values":[proj("dim_device","home_id")]})
        visual(page,"date","slicer",294,8,430,70,"Reporting date",{"Values":[proj("dim_date","date")]})
    for i,measure in enumerate(["Commands","Command Success %","P95 Ack ms","Heartbeat Delivery %"]):
        visual("overview","kpi"+str(i),"card",24+i*312,94,294,110,measure,{"Values":[m(measure)]})
    visual("overview","trend","lineChart",24,224,760,455,"Command success over time",{"Category":[proj("dim_date","date")],"Y":[m("Command Success %")]})
    visual("overview","failures","clusteredBarChart",804,224,452,455,"Failures by reason",{"Category":[proj("fact_command","failure_reason")],"Y":[m("Failed Commands")]})
    visual("reliability","firmware","slicer",744,8,300,70,"Firmware",{"Values":[proj("dim_firmware","firmware_version")]})
    visual("reliability","success","clusteredColumnChart",24,105,600,270,"Success by firmware (observational)",{"Category":[proj("dim_firmware","firmware_version")],"Y":[m("Command Success %")]})
    visual("reliability","latency","clusteredColumnChart",648,105,608,270,"P95 acknowledgement by source",{"Category":[proj("fact_command","source")],"Y":[m("P95 Ack ms")]})
    visual("reliability","device","tableEx",24,405,1232,275,"Device reliability",{"Values":[proj("dim_device","device_id"),proj("dim_device","home_id"),m("Commands"),m("Command Success %"),m("Heartbeat Delivery %")]})
    for i,measure in enumerate(["Estimated kWh","Assumed Baseline kWh","Modeled Avoided kWh","Modeled Cost Difference INR"]):
        visual("energy","kpi"+str(i),"card",24+i*312,94,294,110,measure,{"Values":[m(measure)]})
    visual("energy","trend","lineChart",24,224,760,455,"Modeled energy vs assumed baseline",{"Category":[proj("dim_date","date")],"Y":[m("Estimated kWh"),m("Assumed Baseline kWh")]})
    visual("energy","loads","clusteredBarChart",804,224,452,455,"Estimated energy by load",{"Category":[proj("dim_device","load_type")],"Y":[m("Estimated kWh")]})
    print("Built native Power BI source project: powerbi/SmartSwitch.pbip")


if __name__=="__main__": build()
