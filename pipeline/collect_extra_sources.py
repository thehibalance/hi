#!/usr/bin/env python3
"""HI. Extra Collectors — FEC, CPSC, FDA, USPTO + EPA ECHO + NHTSA. Fixed scoring."""
import json,os,sys,time,math,requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict
TIMEOUT=60; RATE=0.5

def collect_fec(output_dir):
    print("\n  🏛 FEC Political Donation Data")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    key=os.environ.get("DATAGOV_API_KEY","DEMO_KEY")
    if key=="DEMO_KEY":print("    Using DEMO_KEY (rate limited)")
    searches={"google":"GOOGLE","microsoft":"MICROSOFT","amazon":"AMAZON",
        "meta":"META","apple":"APPLE","walmart":"WALMART",
        "jpmorgan":"JPMORGAN","goldman":"GOLDMAN SACHS",
        "att":"AT&T","verizon":"VERIZON","comcast":"COMCAST",
        "disney":"DISNEY","nike":"NIKE","starbucks":"STARBUCKS",
        "costco":"COSTCO","tesla":"TESLA","uber":"UBER","unitedhealth":"UNITEDHEALTH"}
    results={}
    for cid,search in searches.items():
        try:
            # Get committee IDs first
            r=requests.get("https://api.open.fec.gov/v1/committees/",
                params={"api_key":key,"q":search,"per_page":5,"committee_type":["Q","W"]},timeout=TIMEOUT)
            data=r.json(); committees=data.get("results",[])
            if not committees:continue
            # Get totals for each committee
            total_spent=0; pac_count=len(committees)
            for comm in committees:
                cid_fec=comm.get("committee_id","")
                if cid_fec:
                    try:
                        tr=requests.get(f"https://api.open.fec.gov/v1/committee/{cid_fec}/totals/",
                            params={"api_key":key,"per_page":1},timeout=TIMEOUT)
                        tdata=tr.json()
                        for t in tdata.get("results",[]):
                            total_spent+=t.get("disbursements",0)or 0
                    except: pass
            # Score: political spending transparency
            if total_spent>0:
                activity=min(math.log10(max(total_spent,1))/8*100,100)
                fec_score=max(0,round(100-activity*0.6))
            else:
                fec_score=85  # No spending data = neutral, not perfect
            results[cid]={"company":cid,"pac_count":pac_count,"total_disbursements":total_spent,
                "fec_score":fec_score,"collected_at":datetime.now().isoformat(),
                "source":"api.open.fec.gov","maps_to":["M.2"]}
            print(f"    {cid}: {pac_count} PACs, ${total_spent:,.0f} spent → score {fec_score}")
            time.sleep(RATE)
        except Exception as e: print(f"    {cid}: error - {str(e)[:60]}")
    json.dump(results,open(Path(output_dir)/"fec_donations.json","w"),indent=2,default=str)
    print(f"\n    ✓ FEC: {len(results)} companies"); return results

def collect_cpsc(output_dir):
    print("\n  ⚠ CPSC Product Recall Data")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    searches={"apple":"Apple","samsung":"Samsung","amazon":"Amazon","tesla":"Tesla",
        "walmart":"Walmart","target":"Target","costco":"Costco","nike":"Nike",
        "ikea":"IKEA","johnson_johnson":"Johnson","pepsico":"PepsiCo",
        "cocacola":"Coca-Cola","disney":"Disney","google":"Google","microsoft":"Microsoft"}
    results={}
    for cid,search in searches.items():
        try:
            r=requests.get("https://www.saferproducts.gov/RestWebServices/Recall",
                params={"format":"json","Manufacturer":search},timeout=TIMEOUT)
            if r.status_code!=200:continue
            try: recalls=r.json()
            except: recalls=[]
            if not isinstance(recalls,list):recalls=[]
            recent=[rc for rc in recalls if any(str(y)in json.dumps(rc)for y in range(2020,2027))]
            count=len(recent)
            if count==0:cpsc_score=100
            elif count<=2:cpsc_score=85
            elif count<=5:cpsc_score=70
            elif count<=10:cpsc_score=50
            else:cpsc_score=max(0,100-count*3)
            results[cid]={"company":cid,"recent_recalls":count,"total_recalls":len(recalls),
                "cpsc_score":cpsc_score,"collected_at":datetime.now().isoformat(),
                "source":"saferproducts.gov","maps_to":["M.3"]}
            if count>0:print(f"    {cid}: {count} recent recalls → score {cpsc_score}")
            time.sleep(RATE)
        except Exception as e: print(f"    {cid}: error - {str(e)[:60]}")
    json.dump(results,open(Path(output_dir)/"cpsc_recalls.json","w"),indent=2,default=str)
    print(f"\n    ✓ CPSC: {len(results)} companies"); return results

def collect_fda(output_dir):
    print("\n  💊 FDA Enforcement Data (normalized)")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    # Use more specific search terms to avoid false positives
    searches={"johnson_johnson":"johnson+AND+johnson","pfizer":"pfizer","abbott":"abbott",
        "cocacola":"coca+cola","pepsico":"pepsico","walmart":"walmart+stores",
        "costco":"costco","target":"target+corporation","samsung":"samsung",
        "starbucks":"starbucks","mcdonalds":"mcdonalds","nestle":"nestle"}
    results={}
    for cid,search in searches.items():
        try:
            count=0
            for endpoint in["food/enforcement","drug/enforcement"]:
                r=requests.get(f"https://api.fda.gov/{endpoint}.json",
                    params={"search":f"recalling_firm:{search}","limit":5},timeout=TIMEOUT)
                if r.status_code==200:
                    data=r.json();count+=data.get("meta",{}).get("results",{}).get("total",0)
            if count==0:fda_score=100
            else:
                # Log scale: 1-10=good, 10-100=moderate, 100+=concerning
                fda_score=max(0,min(100,round(100-min(math.log10(max(count,1))*30,80))))
            results[cid]={"company":cid,"total_enforcement":count,"fda_score":fda_score,
                "collected_at":datetime.now().isoformat(),"source":"api.fda.gov","maps_to":["M.3"]}
            if count>0:print(f"    {cid}: {count} enforcement actions → score {fda_score}")
            time.sleep(RATE)
        except Exception as e: print(f"    {cid}: error - {str(e)[:60]}")
    json.dump(results,open(Path(output_dir)/"fda_enforcement.json","w"),indent=2,default=str)
    print(f"\n    ✓ FDA: {len(results)} companies"); return results

def collect_patents(output_dir):
    print("\n  📜 USPTO Patent Data")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    searches={"google":"Google","microsoft":"Microsoft","amazon":"Amazon",
        "meta":"Facebook","apple":"Apple","ibm":"IBM","intel":"Intel",
        "nvidia":"NVIDIA","tesla":"Tesla","oracle":"Oracle","adobe":"Adobe","samsung":"Samsung"}
    results={}
    for cid,search in searches.items():
        try:
            r=requests.get("https://search.patentsview.org/api/v1/patent/",
                params={"q":json.dumps({"_contains":{"assignees.assignee_organization":search}}),
                    "f":json.dumps(["patent_id","patent_title","patent_date"]),
                    "o":json.dumps({"per_page":100,"page":1}),
                    "s":json.dumps([{"patent_date":"desc"}])},timeout=TIMEOUT)
            if r.status_code!=200:continue
            data=r.json();patents=data.get("patents",[])
            total_count=data.get("total_patent_count",len(patents))
            ai_kw=["artificial intelligence","machine learning","neural network","deep learning",
                "natural language","autonomous","automated","robotic","generative"]
            ai_count=sum(1 for p in patents if any(k in(p.get("patent_title","")or"").lower()for k in ai_kw))
            sample=len(patents);ratio=ai_count/sample if sample>0 else 0
            patent_score=max(0,round(100-ratio*100))
            results[cid]={"company":cid,"total_patents":total_count,"ai_patents":ai_count,
                "ai_ratio":round(ratio,3),"patent_score":patent_score,
                "collected_at":datetime.now().isoformat(),"source":"patentsview.org","maps_to":["H.5"]}
            print(f"    {cid}: {total_count} patents, {ai_count}/{sample} AI ({ratio:.0%}) → score {patent_score}")
            time.sleep(RATE)
        except Exception as e: print(f"    {cid}: error - {str(e)[:60]}")
    json.dump(results,open(Path(output_dir)/"uspto_patents.json","w"),indent=2,default=str)
    print(f"\n    ✓ USPTO: {len(results)} companies"); return results

# ═══ SOURCE 41: EPA ECHO — Environmental Compliance ═══
def collect_epa(output_dir):
    print("\n  🌍 EPA ECHO Environmental Compliance")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    searches={"walmart":"walmart","amazon":"amazon","starbucks":"starbucks",
        "mcdonalds":"mcdonalds","target":"target","costco":"costco",
        "tesla":"tesla","boeing":"boeing","ford":"ford motor",
        "tyson":"tyson","pepsico":"pepsico","cocacola":"coca-cola",
        "johnson_johnson":"johnson & johnson","3m":"3m company",
        "exxonmobil":"exxonmobil","shell":"shell","bp":"bp",
        "intel":"intel","disney":"disney","nike":"nike"}
    results={}
    for cid,search in searches.items():
        try:
            r=requests.get("https://echo.epa.gov/api/dfr/facilities",
                params={"p_name":search,"output":"JSON","p_act":"Y"},timeout=TIMEOUT)
            if r.status_code!=200:continue
            data=r.json()
            # EPA returns facilities with compliance status
            results_list=data.get("Results",{}).get("Facilities",[])
            if not results_list:continue
            total=len(results_list)
            violations=sum(1 for f in results_list if f.get("CurrVioFlag","N")=="Y"or f.get("QtrsWithNC",0)>0)
            sig_violations=sum(1 for f in results_list if f.get("CurrSNC","N")=="Y")
            viol_rate=violations/total if total>0 else 0
            # Score: fewer violations relative to facilities = better
            epa_score=max(0,min(100,round(100-viol_rate*80-sig_violations*5)))
            results[cid]={"company":cid,"facilities":total,"violations":violations,
                "significant_violations":sig_violations,"violation_rate":round(viol_rate,3),
                "epa_score":epa_score,"collected_at":datetime.now().isoformat(),
                "source":"echo.epa.gov","maps_to":["A.3"]}
            print(f"    {cid}: {total} facilities, {violations} violations ({sig_violations} significant) → score {epa_score}")
            time.sleep(RATE)
        except Exception as e: print(f"    {cid}: error - {str(e)[:60]}")
    json.dump(results,open(Path(output_dir)/"epa_echo.json","w"),indent=2,default=str)
    print(f"\n    ✓ EPA: {len(results)} companies"); return results

# ═══ SOURCE 42: NHTSA — Vehicle Safety ═══
def collect_nhtsa(output_dir):
    print("\n  🚗 NHTSA Vehicle Safety Complaints")
    print("  "+"─"*40)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    searches={"tesla":"TESLA","ford":"FORD","toyota":"TOYOTA","gm":"GENERAL MOTORS",
        "bmw":"BMW","honda":"HONDA","nissan":"NISSAN","subaru":"SUBARU",
        "volkswagen":"VOLKSWAGEN","hyundai":"HYUNDAI"}
    results={}
    for cid,search in searches.items():
        try:
            r=requests.get(f"https://api.nhtsa.gov/complaints/complaintsByManufacturer",
                params={"manufacturer":search},timeout=TIMEOUT)
            if r.status_code!=200:continue
            data=r.json()
            complaints=data.get("results",[])
            count=data.get("count",len(complaints))
            if count==0:nhtsa_score=100
            else:
                nhtsa_score=max(0,min(100,round(100-min(math.log10(max(count,1))*20,80))))
            results[cid]={"company":cid,"total_complaints":count,
                "nhtsa_score":nhtsa_score,"collected_at":datetime.now().isoformat(),
                "source":"api.nhtsa.gov","maps_to":["M.3"]}
            print(f"    {cid}: {count:,} complaints → score {nhtsa_score}")
            time.sleep(RATE)
        except Exception as e: print(f"    {cid}: error - {str(e)[:60]}")
    json.dump(results,open(Path(output_dir)/"nhtsa_complaints.json","w"),indent=2,default=str)
    print(f"\n    ✓ NHTSA: {len(results)} companies"); return results

def integrate(fec,cpsc,fda,patents,epa,nhtsa,sub_dir):
    print("\n  🔗 Integrating all sources");Path(sub_dir).mkdir(parents=True,exist_ok=True);u=0
    for cid,d in(fec or{}).items():
        f=Path(sub_dir)/f"{cid}.json";e=json.load(open(f))if f.exists()else{}
        if"M"not in e:e["M"]={"scores":{},"sources":[]}
        e["M"]["scores"]["M.2"]=d["fec_score"]
        if"FEC"not in str(e["M"]["sources"]):e["M"]["sources"]+=["FEC"]
        json.dump(e,open(f,"w"),indent=2);u+=1
    for cid,d in(cpsc or{}).items():
        f=Path(sub_dir)/f"{cid}.json";e=json.load(open(f))if f.exists()else{}
        if"M"not in e:e["M"]={"scores":{},"sources":[]}
        e["M"]["scores"]["M.3"]=d["cpsc_score"]
        if"CPSC"not in str(e["M"]["sources"]):e["M"]["sources"]+=["CPSC"]
        json.dump(e,open(f,"w"),indent=2);u+=1
    for cid,d in(fda or{}).items():
        f=Path(sub_dir)/f"{cid}.json";e=json.load(open(f))if f.exists()else{}
        if"M"not in e:e["M"]={"scores":{},"sources":[]}
        existing=e["M"]["scores"].get("M.3")
        e["M"]["scores"]["M.3"]=round((existing+d["fda_score"])/2)if existing else d["fda_score"]
        if"FDA"not in str(e["M"]["sources"]):e["M"]["sources"]+=["FDA"]
        json.dump(e,open(f,"w"),indent=2);u+=1
    for cid,d in(patents or{}).items():
        f=Path(sub_dir)/f"{cid}.json";e=json.load(open(f))if f.exists()else{}
        if"H"not in e:e["H"]={"scores":{},"sources":[]}
        e["H"]["scores"]["H.5"]=d["patent_score"]
        if"USPTO"not in str(e["H"]["sources"]):e["H"]["sources"]+=["USPTO"]
        json.dump(e,open(f,"w"),indent=2);u+=1
    for cid,d in(epa or{}).items():
        f=Path(sub_dir)/f"{cid}.json";e=json.load(open(f))if f.exists()else{}
        if"A"not in e:e["A"]={"scores":{},"sources":[]}
        e["A"]["scores"]["A.3"]=d["epa_score"]
        if"EPA ECHO"not in str(e["A"]["sources"]):e["A"]["sources"]+=["EPA ECHO"]
        json.dump(e,open(f,"w"),indent=2);u+=1
    for cid,d in(nhtsa or{}).items():
        f=Path(sub_dir)/f"{cid}.json";e=json.load(open(f))if f.exists()else{}
        if"M"not in e:e["M"]={"scores":{},"sources":[]}
        existing=e["M"]["scores"].get("M.3")
        e["M"]["scores"]["M.3"]=round((existing+d["nhtsa_score"])/2)if existing else d["nhtsa_score"]
        if"NHTSA"not in str(e["M"]["sources"]):e["M"]["sources"]+=["NHTSA"]
        json.dump(e,open(f,"w"),indent=2);u+=1
    print(f"    ✓ {u} files updated")

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description="HI. Extra Sources (37-42)")
    p.add_argument("--output",default="data/gov");p.add_argument("--subsignals",default="data/subsignals")
    p.add_argument("--all",action="store_true")
    p.add_argument("--fec",action="store_true");p.add_argument("--cpsc",action="store_true")
    p.add_argument("--fda",action="store_true");p.add_argument("--patents",action="store_true")
    p.add_argument("--epa",action="store_true");p.add_argument("--nhtsa",action="store_true")
    a=p.parse_args()
    if a.all or not any([a.fec,a.cpsc,a.fda,a.patents,a.epa,a.nhtsa]):
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║  HI. — All Extra Sources (37-42)                       ║")
        print("║  The answer was always 42.                              ║")
        print("╚══════════════════════════════════════════════════════════╝")
        fec=collect_fec(a.output);cpsc=collect_cpsc(a.output);fda=collect_fda(a.output)
        patents=collect_patents(a.output);epa=collect_epa(a.output);nhtsa=collect_nhtsa(a.output)
        integrate(fec,cpsc,fda,patents,epa,nhtsa,a.subsignals)
        print(f"\n  🎯 42 data sources. The answer was always 42.")
    else:
        if a.fec:collect_fec(a.output)
        if a.cpsc:collect_cpsc(a.output)
        if a.fda:collect_fda(a.output)
        if a.patents:collect_patents(a.output)
        if a.epa:collect_epa(a.output)
        if a.nhtsa:collect_nhtsa(a.output)
