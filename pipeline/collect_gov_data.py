#!/usr/bin/env python3
"""
HI. Data Collectors — OSHA (filtered!) + CFPB
Verified working endpoints March 2026.
OSHA uses filter_object for server-side company filtering.
"""
import json,os,sys,time,math,requests,urllib3
from pathlib import Path
from datetime import datetime,timedelta
from collections import defaultdict

urllib3.disable_warnings()
TIMEOUT=60; RATE=0.5

# ═══ OSHA — server-side filtered by company name ═══
def collect_osha(output_dir):
    print("\n  📋 OSHA Inspections (DOL API v4 — filtered)")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    key=os.environ.get("DOL_API_KEY","")
    if not key:
        print("    ⚠ No DOL_API_KEY. export DOL_API_KEY=xxx");return {}
    
    base="https://api.dol.gov/v4/get/OSHA/inspection/json"
    
    searches={
        "walmart":"WALMART","amazon":"AMAZON","starbucks":"STARBUCKS",
        "mcdonalds":"MCDONALD","target":"TARGET","costco":"COSTCO",
        "nike":"NIKE","disney":"DISNEY","tesla":"TESLA","ups":"UNITED PARCEL",
        "fedex":"FEDEX","boeing":"BOEING","ford":"FORD MOTOR",
        "home_depot":"HOME DEPOT","tyson":"TYSON","google":"GOOGLE",
        "microsoft":"MICROSOFT","apple":"APPLE","meta":"META",
        "jpmorgan":"JPMORGAN","comcast":"COMCAST","att":"AT&T",
        "verizon":"VERIZON","pepsico":"PEPSICO","cocacola":"COCA-COLA",
        "intel":"INTEL","ibm":"IBM","oracle":"ORACLE",
        "unitedhealth":"UNITEDHEALTH","johnson_johnson":"JOHNSON & JOHNSON",
    }
    
    results={}
    for cid,search in searches.items():
        try:
            filt=json.dumps({"field":"estab_name","operator":"like","value":search})
            r=requests.get(base,params={"X-API-KEY":key,"limit":200,"filter_object":filt,
                "sort":"desc","sort_by":"open_date"},timeout=TIMEOUT,verify=False)
            data=r.json()
            records=data.get("data",[])
            if not records:continue
            
            recent=[rec for rec in records if(rec.get("open_date","")or"")[:4]>="2020"]
            n=len(recent)
            if n==0:continue
            
            severe=sum(1 for i in recent if i.get("insp_type")in("A","M"))
            complaints=sum(1 for i in recent if i.get("insp_type")=="B")
            w=severe*15+complaints*5+(n-severe-complaints)
            score=max(0,100-min(w,100))
            
            results[cid]={"company":cid,"inspections":n,"severe":severe,"complaints":complaints,
                "osha_score":score,"collected_at":datetime.now().isoformat(),
                "source":"api.dol.gov OSHA (filtered)","maps_to":["M.3","A.3"]}
            print(f"    {cid}: {n} inspections since 2020 (severe:{severe}, complaints:{complaints}) → score {score}")
            time.sleep(RATE)
        except Exception as e:
            print(f"    {cid}: error - {str(e)[:60]}")
    
    json.dump(results,open(Path(output_dir)/"osha_violations.json","w"),indent=2,default=str)
    print(f"\n    ✓ OSHA: {len(results)} companies")
    return results

# ═══ CFPB — search_term parameter ═══
def collect_cfpb(output_dir):
    print("\n  📝 CFPB Consumer Complaints")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    base="https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
    
    terms=["jpmorgan","bank of america","wells fargo","citibank","capital one",
        "goldman sachs","american express","discover financial","synchrony",
        "unitedhealth","optum","apple","amazon","paypal",
        "comcast","at&t","verizon","t-mobile","tesla","walmart","target",
        "starbucks","nike","costco","uber","microsoft","meta","google"]
    
    results={};total=0
    for term in terms:
        try:
            r=requests.get(base,params={"search_term":term,"size":100,
                "date_received_min":"2024-01-01","sort":"created_date_desc"},timeout=TIMEOUT)
            data=r.json()
        except Exception as e:
            print(f"    {term}: error - {e}");continue
        
        hits=data.get("hits",{});tobj=hits.get("total",{})
        count=tobj.get("value",0)if isinstance(tobj,dict)else(tobj or 0)
        if count==0:continue
        recs=hits.get("hits",[])
        if not recs:continue
        
        s=len(recs)
        timely=sum(1 for c in recs if(c.get("_source",{}).get("timely","")or"").lower()=="yes")
        resolved=sum(1 for c in recs 
            if"closed"in(c.get("_source",{}).get("company_response","")or"").lower()
            and("relief"in(c.get("_source",{}).get("company_response","")or"").lower()
                or"explanation"in(c.get("_source",{}).get("company_response","")or"").lower()))
        
        tp=round(timely/s*100,1)if s else 0
        rp=round(resolved/s*100,1)if s else 0
        vp=min(math.log10(max(count,1))*15,60)
        score=max(0,min(100,round(100-vp+rp*0.2+tp*0.2)))
        
        key=term.lower().replace(" ","_").replace("&","and")
        results[key]={"company":term,"total_complaints":count,"sample_size":s,
            "timely_pct":tp,"resolution_pct":rp,"cfpb_score":score,
            "collected_at":datetime.now().isoformat(),"source":"consumerfinance.gov","maps_to":["U.1","U.2"]}
        total+=count
        print(f"    {term}: {count:,} complaints, {tp}% timely, {rp}% resolved → score {score}")
        time.sleep(RATE)
    
    json.dump(results,open(Path(output_dir)/"cfpb_complaints.json","w"),indent=2,default=str)
    print(f"\n    ✓ CFPB: {len(results)} companies, {total:,} total complaints")
    return results

# ═══ Integration ═══
def integrate(osha,cfpb,sub_dir):
    print("\n  🔗 Integrating into sub-signals")
    Path(sub_dir).mkdir(parents=True,exist_ok=True);u=0
    for cid,d in(osha or{}).items():
        f=Path(sub_dir)/f"{cid}.json"
        e=json.load(open(f))if f.exists()else{}
        for dim in["M","A"]:
            if dim not in e:e[dim]={"scores":{},"sources":[]}
            e[dim]["scores"][{"M":"M.3","A":"A.3"}[dim]]=d["osha_score"]
            if"OSHA"not in str(e[dim]["sources"]):e[dim]["sources"]+= ["OSHA via DOL"]
        json.dump(e,open(f,"w"),indent=2);u+=1
    for cid,d in(cfpb or{}).items():
        f=Path(sub_dir)/f"{cid}.json"
        e=json.load(open(f))if f.exists()else{}
        if"U"not in e:e["U"]={"scores":{},"sources":[]}
        e["U"]["scores"]["U.1"]=d["cfpb_score"];e["U"]["scores"]["U.2"]=min(100,d["cfpb_score"]+10)
        if"CFPB"not in str(e["U"]["sources"]):e["U"]["sources"]+=["CFPB"]
        json.dump(e,open(f,"w"),indent=2);u+=1
    print(f"    ✓ {u} files updated")

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description="HI. Gov Data")
    p.add_argument("--output",default="data/gov")
    p.add_argument("--subsignals",default="data/subsignals")
    p.add_argument("--all",action="store_true")
    p.add_argument("--osha",action="store_true")
    p.add_argument("--cfpb",action="store_true")
    a=p.parse_args()
    if a.all or(not a.osha and not a.cfpb):
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║  HI. — Government Data (OSHA + CFPB)                   ║")
        print("╚══════════════════════════════════════════════════════════╝")
        o=collect_osha(a.output);c=collect_cfpb(a.output);integrate(o,c,a.subsignals)
    else:
        if a.osha:collect_osha(a.output)
        if a.cfpb:collect_cfpb(a.output)
