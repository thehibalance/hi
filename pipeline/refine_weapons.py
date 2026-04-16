#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refine weapons records to use accurate WEAPONS revenue percentages.
Splits civilian/scientific work (e.g. Lockheed Space) from lethal-systems work.

Adds revenue_breakdown to each record showing the split with sources,
and updates primary_revenue_pct to reflect weapons-only share.
Penalty math (in weapons_penalty) already proportional to this number.
"""
import os, sys, shutil, tempfile

def atomic_write(path, content):
    dir_ = os.path.dirname(path) or '.'
    fd, tmppath = tempfile.mkstemp(dir=dir_, prefix='.tmp_', suffix='.py')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmppath, path)
    except Exception:
        if os.path.exists(tmppath):
            os.unlink(tmppath)
        raise

# Targeted replacement for each company — corrected weapons-only percentages
PATCHES = [
    # Lockheed Martin: Space (~17%) is civilian/scientific (Orion, GPS, weather sats).
    # Weapons-only revenue is roughly Aero (40%) + Missiles (17%) + RMS-weapons-portion (~21%) = ~78%
    ("Lockheed: split Space from weapons",
     '''    "LMT": {
        "company": "Lockheed Martin Corporation",
        "category": "weapons",
        "primary_revenue_pct": 95,  # ~95% defense
        "products": ["F-35 fighter", "Hellfire missile", "THAAD", "Trident SLBM", "PAC-3 Patriot"],''',
     '''    "LMT": {
        "company": "Lockheed Martin Corporation",
        "category": "weapons",
        "primary_revenue_pct": 78,  # weapons-only: Aero 40% + Missiles 17% + RMS weapons-portion ~21%
        "revenue_breakdown": {
            "weapons_pct": 78,
            "civilian_pct": 22,  # Space division: Orion crew capsule, GPS satellites, NOAA weather sats, planetary missions
            "civilian_notes": "Lockheed Martin Space (~17%) + Sikorsky civilian helicopters (~5%) — scientific/non-lethal work excluded from penalty"
        },
        "products": ["F-35 fighter", "Hellfire missile", "THAAD", "Trident SLBM", "PAC-3 Patriot"],
        "civilian_products": ["Orion crew capsule (NASA)", "GPS III satellites", "GOES weather satellites", "OSIRIS-APEX (NASA asteroid mission)"],'''),

    # Boeing: Defense + Space + Security is ~40% of revenue. Space portion is genuine civilian (CST-100, satellites)
    # Weapons-only is Defense ~30%
    ("Boeing: refine weapons-only share",
     '''    "BA": {
        "company": "The Boeing Company",
        "category": "weapons_partial",  # mixed civilian + military
        "primary_revenue_pct": 40,  # ~40% Boeing Defense, Space & Security
        "products": ["F-15EX fighter", "AH-64 Apache", "F/A-18 Super Hornet", "JDAM bombs", "GBU-39 SDB"],''',
     '''    "BA": {
        "company": "The Boeing Company",
        "category": "weapons_partial",
        "primary_revenue_pct": 30,  # Defense weapons portion only (BDS minus Space subsegment)
        "revenue_breakdown": {
            "weapons_pct": 30,
            "civilian_pct": 70,
            "civilian_notes": "Commercial Airplanes (~50%) + Boeing Space (~10%, CST-100 Starliner / ISS / commercial sats) + Global Services (~10%)"
        },
        "products": ["F-15EX fighter", "AH-64 Apache", "F/A-18 Super Hornet", "JDAM bombs", "GBU-39 SDB"],
        "civilian_products": ["737 / 787 / 777 commercial aircraft", "CST-100 Starliner", "ISS support"],'''),

    # General Dynamics: Marine Systems (subs) + Combat Systems (tanks) + Mission Systems = weapons
    # Aerospace (Gulfstream business jets ~25%) is genuine civilian
    ("General Dynamics: split Gulfstream civilian aviation",
     '''    "GD": {
        "company": "General Dynamics Corporation",
        "category": "weapons",
        "primary_revenue_pct": 75,
        "products": ["M1 Abrams tank", "Virginia-class submarine", "Stryker", "ammunition", "GAU-17 minigun"],''',
     '''    "GD": {
        "company": "General Dynamics Corporation",
        "category": "weapons",
        "primary_revenue_pct": 73,  # Marine Systems + Combat Systems + Mission Systems + Tech (defense IT)
        "revenue_breakdown": {
            "weapons_pct": 73,
            "civilian_pct": 27,
            "civilian_notes": "Gulfstream Aerospace (~27%) — civilian business jets G500/G650/G700"
        },
        "products": ["M1 Abrams tank", "Virginia-class submarine", "Stryker", "ammunition", "GAU-17 minigun"],
        "civilian_products": ["Gulfstream G500/G650/G700/G800 business jets"],'''),

    # Northrop Grumman: Aeronautics (B-2/B-21) + Defense Systems + Mission Systems + Space.
    # Space portion (~25%, missile defense + NASA James Webb support + commercial sats) is mixed.
    # Conservative weapons-only: ~70%
    ("Northrop Grumman: account for Space division",
     '''    "NOC": {
        "company": "Northrop Grumman Corporation",
        "category": "weapons",
        "primary_revenue_pct": 90,
        "products": ["B-2/B-21 stealth bomber", "ICBM (Sentinel)", "Global Hawk drone", "naval guns"],''',
     '''    "NOC": {
        "company": "Northrop Grumman Corporation",
        "category": "weapons",
        "primary_revenue_pct": 75,  # Aeronautics + Defense Systems + Mission Systems + space-weapons portion
        "revenue_breakdown": {
            "weapons_pct": 75,
            "civilian_pct": 25,
            "civilian_notes": "Space Systems portion: James Webb Space Telescope ops, civilian satellites, NASA Artemis support — though most space work is missile defense/Sentinel ICBM"
        },
        "products": ["B-2/B-21 stealth bomber", "Sentinel ICBM", "Global Hawk drone", "naval guns"],
        "civilian_products": ["James Webb Space Telescope (operations)", "civilian Earth-observation satellites"],'''),

    # RTX: Pratt & Whitney engines (~30%) include civilian airline engines.
    # Collins Aerospace (~30%) mixed civilian aviation systems + military. 
    # Raytheon (~30%) is pure weapons. So weapons-only is roughly Raytheon + military portion of others = ~50%
    ("RTX: separate Pratt civilian engines + Collins civilian avionics",
     '''    "RTX": {
        "company": "RTX Corporation (Raytheon Technologies)",
        "category": "weapons",
        "primary_revenue_pct": 65,
        "products": ["Tomahawk missile", "Patriot missile", "Stinger missile", "Javelin", "AIM-9 Sidewinder"],''',
     '''    "RTX": {
        "company": "RTX Corporation (Raytheon Technologies)",
        "category": "weapons",
        "primary_revenue_pct": 50,  # Raytheon segment + military portion of Pratt & Collins
        "revenue_breakdown": {
            "weapons_pct": 50,
            "civilian_pct": 50,
            "civilian_notes": "Pratt & Whitney commercial engines (~25%) — A320neo/A220/Embraer airliners. Collins Aerospace civilian avionics (~25%) — commercial airliner systems."
        },
        "products": ["Tomahawk missile", "Patriot missile", "Stinger missile", "Javelin", "AIM-9 Sidewinder"],
        "civilian_products": ["PW1100G GTF engines (A320neo)", "PW1500G (A220)", "Collins commercial cockpit systems"],'''),

    # L3Harris: Aerojet Rocketdyne portion is weapons (rocket motors for missiles/ICBMs)
    # Some Space & Airborne is civilian/dual-use
    ("L3Harris: refine for Space & Airborne dual-use",
     '''    "LHX": {
        "company": "L3Harris Technologies",
        "category": "weapons",
        "primary_revenue_pct": 75,
        "products": ["combat radios", "missile guidance", "tactical drones", "naval combat systems"],''',
     '''    "LHX": {
        "company": "L3Harris Technologies",
        "category": "weapons",
        "primary_revenue_pct": 70,
        "revenue_breakdown": {
            "weapons_pct": 70,
            "civilian_pct": 30,
            "civilian_notes": "Communication Systems portion (~20%) civilian comms infra + Space & Airborne portion (~10%) civilian satellites/weather/maritime"
        },
        "products": ["combat radios", "missile guidance", "tactical drones", "naval combat systems", "Aerojet Rocketdyne ICBM rocket motors"],
        "civilian_products": ["civilian aviation electronics", "weather satellites support"],'''),

    # Huntington Ingalls: Almost entirely Navy work — but Newport News also services civilian/research vessels
    # And Mission Technologies has IT services portion. Conservative weapons-only ~85%
    ("Huntington Ingalls: account for Mission Technologies services",
     '''    "HII": {
        "company": "Huntington Ingalls Industries",
        "category": "weapons",
        "primary_revenue_pct": 95,
        "products": ["aircraft carriers", "amphibious assault ships", "nuclear submarines"],''',
     '''    "HII": {
        "company": "Huntington Ingalls Industries",
        "category": "weapons",
        "primary_revenue_pct": 85,
        "revenue_breakdown": {
            "weapons_pct": 85,
            "civilian_pct": 15,
            "civilian_notes": "Mission Technologies (~15%) — defense/intel IT services, training simulators, unmanned underwater vehicles for research"
        },
        "products": ["Ford-class aircraft carriers", "Virginia-class submarines", "amphibious assault ships"],'''),

    # Textron: Bell military helicopters + AT-6 + Shadow drones is weapons.
    # Cessna/Beechcraft civilian aircraft + Bell commercial helicopters + Industrial = civilian
    # Weapons-only ~30%
    ("Textron: clarify civilian aviation majority",
     '''    "TXT": {
        "company": "Textron Inc",
        "category": "weapons",
        "primary_revenue_pct": 35,  # mixed: Bell military helicopters + civilian Cessna
        "products": ["Bell UH-1Y/AH-1Z military helicopters", "AT-6 Wolverine attack aircraft", "Shadow drone"],''',
     '''    "TXT": {
        "company": "Textron Inc",
        "category": "weapons_partial",
        "primary_revenue_pct": 30,  # Bell military + Systems (drones/munitions) — most revenue is civilian aviation
        "revenue_breakdown": {
            "weapons_pct": 30,
            "civilian_pct": 70,
            "civilian_notes": "Cessna Citation jets, Beechcraft, Bell commercial helicopters, Industrial (golf carts, vehicle products)"
        },
        "products": ["Bell UH-1Y/AH-1Z military helicopters", "AT-6 Wolverine attack aircraft", "Shadow drone"],
        "civilian_products": ["Cessna Citation business jets", "Beechcraft King Air", "Bell 407/429 commercial helicopters"],'''),

    # Vista Outdoor: Sporting Products (Federal/CCI/Speer ammo) + Outdoor Products (Camelbak/etc)
    # Outdoor portion (~40%) is genuine non-weapons. Weapons-only ammo portion ~60%
    # Already at 60 — actually correct as-is. Just add the breakdown for transparency.
    ("Vista Outdoor: add explicit civilian breakdown",
     '''    "VSTO": {
        "company": "Vista Outdoor",
        "category": "weapons",
        "primary_revenue_pct": 60,  # Sporting Products division (Federal, CCI, Speer ammo)
        "products": ["centerfire ammunition", "rimfire ammunition", "primers"],''',
     '''    "VSTO": {
        "company": "Vista Outdoor",
        "category": "weapons",
        "primary_revenue_pct": 60,
        "revenue_breakdown": {
            "weapons_pct": 60,
            "civilian_pct": 40,
            "civilian_notes": "Outdoor Products (~40%) — CamelBak, Bushnell optics, Bell helmets, Giro, BlackHawk gear"
        },
        "products": ["Federal/CCI/Speer ammunition", "primers", "powders"],
        "civilian_products": ["CamelBak hydration", "Bushnell binoculars", "Bell/Giro helmets"],'''),
]


def main():
    path = os.path.expanduser('~/Desktop/repo/pipeline/harm_documentation_pipeline.py')
    if not os.path.exists(path):
        print(f"Not found: {path}")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    original = src

    applied = 0
    skipped = 0
    not_found = 0
    for label, old, new in PATCHES:
        if old in src:
            src = src.replace(old, new)
            print(f"  ✓ {label}")
            applied += 1
        elif new in src:
            print(f"  ⊙ {label} (already applied)")
            skipped += 1
        else:
            print(f"  ✗ {label} (pattern not found)")
            not_found += 1

    if src != original:
        if not os.path.exists(path + '.refine.bak'):
            shutil.copy(path, path + '.refine.bak')
        atomic_write(path, src)
        print()
        print(f"Applied {applied}, skipped {skipped}, not found {not_found}")
        print()
        print("Test it:")
        print("  cd ~/Desktop/repo/pipeline")
        print("  python3 -c \"from harm_documentation_pipeline import compute_harm_penalty; r = compute_harm_penalty('LMT'); print('LMT M penalty:', r['penalties']['M'], '· flags:', r['flags'])\"")

if __name__ == '__main__':
    main()
