#!/usr/bin/env python3
"""HI. Data Collector — OSHA inspections, normalized by company size.

CFPB was collected here too until v1.9.2, by fuzzy `search_term` matching with its
rates estimated from a 100-record sample and U.2 set to the complaint score plus ten.
None of it was ever read by the scoring path. CFPB complaints are collected by
cfpb_pipeline.py, matched to the names CFPB itself registers.
"""
import json,os,sys,time,math,requests,urllib3
from pathlib import Path
from datetime import datetime,timedelta
from collections import defaultdict
urllib3.disable_warnings()
TIMEOUT=60; RATE=0.5

EMPLOYEE_COUNTS = {
    "walmart":2100,"amazon":1500,"starbucks":380,"mcdonalds":150,"target":440,
    "costco":310,"nike":80,"disney":220,"tesla":130,"ups":540,"fedex":500,
    "boeing":170,"ford":177,"home_depot":475,"tyson":140,"google":180,
    "microsoft":220,"apple":164,"meta":67,"jpmorgan":310,"comcast":186,
    "att":150,"verizon":105,"pepsico":315,"cocacola":80,"intel":125,
    "ibm":280,"oracle":165,"unitedhealth":400,"johnson_johnson":130,
}

def collect_osha(output_dir):
    print("\n  📋 OSHA Inspections (normalized by company size)")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    key=os.environ.get("DOL_API_KEY","")
    if not key: print("    ⚠ No DOL_API_KEY");return {}
    base="https://api.dol.gov/v4/get/OSHA/inspection/json"
    searches={"walmart":"WALMART","amazon":"AMAZON","starbucks":"STARBUCKS",
        "mcdonalds":"MCDONALD","target":"TARGET","costco":"COSTCO",
        "nike":"NIKE","disney":"DISNEY","tesla":"TESLA","ups":"UNITED PARCEL",
        "fedex":"FEDEX","boeing":"BOEING","ford":"FORD MOTOR",
        "home_depot":"HOME DEPOT","tyson":"TYSON","google":"GOOGLE",
        "microsoft":"MICROSOFT","apple":"APPLE","meta":"META",
        "jpmorgan":"JPMORGAN","comcast":"COMCAST","att":"AT&T",
        "verizon":"VERIZON","pepsico":"PEPSICO","cocacola":"COCA-COLA",
        "intel":"INTEL","ibm":"IBM","oracle":"ORACLE",
        "unitedhealth":"UNITEDHEALTH","johnson_johnson":"JOHNSON & JOHNSON"}
    results={}
    for cid,search in searches.items():
        try:
            filt=json.dumps({"field":"estab_name","operator":"like","value":search})
            r=requests.get(base,params={"X-API-KEY":key,"limit":200,"filter_object":filt,
                "sort":"desc","sort_by":"open_date"},timeout=TIMEOUT,verify=False)
            data=r.json(); records=data.get("data",[])
            if not records:
                results[cid]={"company":cid,"inspections":0,"osha_score":100,
                    "collected_at":datetime.now().isoformat(),"source":"api.dol.gov OSHA","maps_to":["M.3","A.3"]}
                continue
            recent=[rec for rec in records if(rec.get("open_date","")or"")[:4]>="2020"]
            n=len(recent)
            severe=sum(1 for i in recent if i.get("insp_type")in("A","M"))
            complaints=sum(1 for i in recent if i.get("insp_type")=="B")
            routine=n-severe-complaints
            emp_k=EMPLOYEE_COUNTS.get(cid,50); emp_10k=emp_k/10.0
            weighted_rate=(severe*5+complaints*2+routine)/emp_10k if emp_10k>0 else n
            score=max(0,min(100,round(100-weighted_rate*8)))
            results[cid]={"company":cid,"inspections":n,"severe":severe,"complaints":complaints,
                "rate_per_10k":round(n/emp_10k,2),"employees_k":emp_k,"osha_score":score,
                "collected_at":datetime.now().isoformat(),"source":"api.dol.gov OSHA","maps_to":["M.3","A.3"]}
            print(f"    {cid}: {n} inspections / {emp_k}K emp = {n/emp_10k:.1f}/10K → score {score}")
            time.sleep(RATE)
        except Exception as e: print(f"    {cid}: error - {str(e)[:60]}")
    json.dump(results,open(Path(output_dir)/"osha_violations.json","w"),indent=2,default=str)
    print(f"\n    ✓ OSHA: {len(results)} companies"); return results

def integrate(osha,sub_dir):
    print("\n  🔗 Integrating");Path(sub_dir).mkdir(parents=True,exist_ok=True);u=0
    for cid,d in(osha or{}).items():
        f=Path(sub_dir)/f"{cid}.json";e=json.load(open(f))if f.exists()else{}
        for dim in["M","A"]:
            if dim not in e:e[dim]={"scores":{},"sources":[]}
            e[dim]["scores"][{"M":"M.3","A":"A.3"}[dim]]=d["osha_score"]
            if"OSHA"not in str(e[dim]["sources"]):e[dim]["sources"]+=["OSHA via DOL"]
        json.dump(e,open(f,"w"),indent=2);u+=1
    print(f"    ✓ {u} files updated")

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="data/gov");p.add_argument("--subsignals",default="data/gov/by_company")
    p.add_argument("--all",action="store_true");p.add_argument("--osha",action="store_true")
    a=p.parse_args()
    if a.all or not a.osha:
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║  HI. — Government Data (OSHA)                          ║")
        print("╚══════════════════════════════════════════════════════════╝")
        o=collect_osha(a.output);integrate(o,a.subsignals)
    else:
        if a.osha:collect_osha(a.output)
