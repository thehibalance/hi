#!/usr/bin/env python3
"""
HI. Data Collectors — OSHA + CFPB (using requests library)
Verified working endpoints March 2026.
"""
import json,os,sys,time,math,requests
from pathlib import Path
from datetime import datetime,timedelta
from collections import defaultdict

TIMEOUT=60; RATE=0.3

COMPANY_PATTERNS={
    "apple":["APPLE INC","APPLE COMPUTER"],"google":["ALPHABET","GOOGLE"],"microsoft":["MICROSOFT"],
    "amazon":["AMAZON"],"meta":["META PLATFORMS","FACEBOOK"],"tesla":["TESLA"],
    "walmart":["WAL-MART","WALMART"],"jpmorgan":["JPMORGAN","JP MORGAN","CHASE BANK"],
    "johnson_johnson":["JOHNSON & JOHNSON","JOHNSON AND JOHNSON"],
    "unitedhealth":["UNITEDHEALTH","UNITED HEALTH","OPTUM"],"starbucks":["STARBUCKS"],
    "nike":["NIKE"],"costco":["COSTCO"],"target":["TARGET CORP","TARGET STORES"],
    "att":["AT&T","ATT INC"],"verizon":["VERIZON"],"disney":["WALT DISNEY","DISNEY"],
    "pepsico":["PEPSICO","PEPSI","FRITO-LAY"],"cocacola":["COCA-COLA","COCA COLA"],
    "mcdonalds":["MCDONALD"],"uber":["UBER"],"netflix":["NETFLIX"],"adobe":["ADOBE"],
    "salesforce":["SALESFORCE"],"ibm":["IBM","INTERNATIONAL BUSINESS MACHINES"],
    "intel":["INTEL CORP","INTEL FAB"],"oracle":["ORACLE"],"accenture":["ACCENTURE"],"comcast":["COMCAST"],
}

def _match(name):
    u=(name or"").upper()
    for k,terms in COMPANY_PATTERNS.items():
        for t in terms:
            if t in u: return k
    return None

# ═══ OSHA ═══
def collect_osha(output_dir):
    print("\n  📋 OSHA Inspections (DOL API v4)")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    key=os.environ.get("DOL_API_KEY","")
    if not key:
        print("    ⚠ No DOL_API_KEY. export DOL_API_KEY=xxx");return {}
    
    matched=defaultdict(list);offset=0;scanned=0
    while offset<5000:
        try:
            r=requests.get("https://api.dol.gov/v4/get/OSHA/inspection/json",
                params={"X-API-KEY":key,"limit":200,"offset":offset},timeout=TIMEOUT,verify=False)
            data=r.json()
        except Exception as e:
            print(f"    Error at offset {offset}: {e}");break
        if not data or'data'not in data or not data['data']:break
        for rec in data['data']:
            od=rec.get("open_date","")
            if od and od[:4]>="2022":
                k=_match(rec.get("estab_name",""))
                if k:matched[k].append(rec)
        scanned+=len(data['data'])
        if len(data['data'])<200:break
        offset+=200
        time.sleep(RATE)
        if offset%1000==0:print(f"    ...{scanned} scanned, {sum(len(v)for v in matched.values())} matched")
    
    print(f"    Scanned {scanned}, matched {len(matched)} companies")
    results={}
    for k,insp in matched.items():
        n=len(insp)
        severe=sum(1 for i in insp if i.get("insp_type")in("A","M"))
        complaints=sum(1 for i in insp if i.get("insp_type")=="B")
        w=severe*15+complaints*5+(n-severe-complaints)
        score=max(0,100-min(w,100))
        results[k]={"company":k,"inspections":n,"severe":severe,"complaints":complaints,
            "osha_score":score,"collected_at":datetime.now().isoformat(),"source":"api.dol.gov OSHA","maps_to":["M.3","A.3"]}
        print(f"    {k}: {n} inspections (severe:{severe}) → score {score}")
    json.dump(results,open(Path(output_dir)/"osha_violations.json","w"),indent=2,default=str)
    print(f"\n    ✓ OSHA: {len(results)} companies")
    return results

# ═══ CFPB ═══
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
                "date_received_min":"2024-01-01","sort":"created_date_desc"},timeout=TIMEOUT,verify=False)
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
