import streamlit as st
import json
import random
import os
from github import Github, Auth
from github.GithubException import UnknownObjectException

# ----------------------
# CONFIG
# ----------------------
BUILD_CODES_FILE = "build_codes.json"

# ----------------------
# GITHUB
# ----------------------
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = st.secrets.get("REPO_NAME", None)

def get_github_repo():
    if not GITHUB_TOKEN or not REPO_NAME:
        return None
    try:
        g = Github(auth=Auth.Token(GITHUB_TOKEN))
        return g.get_repo(REPO_NAME)
    except:
        return None

repo = get_github_repo()

# ----------------------
# LOAD / SAVE
# ----------------------
def load_build_codes_local():
    if os.path.exists(BUILD_CODES_FILE):
        with open(BUILD_CODES_FILE, "r") as f:
            return json.load(f)
    return {}

def load_build_codes_github():
    if repo is None:
        return {}
    try:
        file_content = repo.get_contents(BUILD_CODES_FILE)
        return json.loads(file_content.decoded_content.decode())
    except:
        return {}

def save_build_codes_local(codes):
    with open(BUILD_CODES_FILE, "w") as f:
        json.dump(codes, f, indent=4)

def save_build_codes_github(codes):
    if repo is None:
        return
    try:
        try:
            file = repo.get_contents(BUILD_CODES_FILE)
            repo.update_file(BUILD_CODES_FILE,"update",json.dumps(codes,indent=4),file.sha)
        except UnknownObjectException:
            repo.create_file(BUILD_CODES_FILE,"create",json.dumps(codes,indent=4))
    except:
        pass

# ----------------------
# SESSION STATE
# ----------------------
if "build_codes" not in st.session_state:
    codes = load_build_codes_github() if repo else load_build_codes_local()
    st.session_state.build_codes = codes

# ----------------------
# WEAPONS DATA (UNCHANGED)
# ----------------------
WEAPONS_DATA = {
    "Assault Rifles": {
        "HK416": "5.56x45mm", "M4A1": "5.56x45mm", "AK-102": "5.56x45mm",
        "FAL": "7.62x51mm", "SCAR-L": "5.56x45mm", "AEK": "7.62x39mm",
        "AK-74N": "5.45x39mm", "AKM": "7.62x39mm", "F2000": "5.56x45mm",
        "ACE31": "7.62x39mm", "AR-57": "5.7x28mm", "AN-94": "5.45x39mm",
        "AUG": "5.56x45mm", "MDR": "5.56x45mm", "AKS-74U": "5.45x39mm",
        "T951": "5.8x42mm", "AK-12": "5.45x39mm", "MCX": "5.56x45mm",
        "T191": "5.8x42mm", "TO3": "5.8x42mm", "AMB-17": "9x39mm", "SG550": "5.56x45mm",
        "G3": "7.62x51mm", "PCC-9": "9x19mm", "ZC-807": "7.62x39mm", "RPK-16": "5.45x39mm"
    },
    "SMGs": {
        "P90": "5.7x28mm", "MP5": "9x19mm", "MPX": "9x19mm",
        "Vector .45": ".45 ACP", "Vector 9": "9x19mm", "UMP45": ".45 ACP",
        "UZI": "9x19mm", "MAC-10": ".45 ACP",
        "MP40": "9x19mm", "T85": "7.62x25mm", "T79": "7.62x25mm",
        "QC61": "7.62x25mm", "MPF45": ".45 ACP", "M3A1": ".45 ACP", "PP-19": "9x19mm"
    },
    "Carbines": {
        "SKS": "7.62x39mm", "M16": "5.56x45mm", "Mini14": "5.56x45mm",
        "SVTU": "7.62x54mm", "BM59": "7.62x51mm", "M14": "7.62x51mm",
        "SA85M": "7.62x39mm", "M96": "5.56x45mm"
    },
    "Marksman Rifles": {
        "M110": "7.62x51mm", "SVDS": "7.62x54mm", "VSS": "9x39mm",
        "MK14": "7.62x51mm", "U191": "5.8x42mm", "ML Lever-Action": ".44 Cal"
    },
    "Sniper Rifles": {
        "Mosin-Nagant": "7.62x54mm", "M24": "7.62x51mm", "SJ16": ".338 Lapua"
    },
    "Shotguns": {
        "S12K": "12x70mm", "M870": "12x70mm", "MP-133": "12x70mm",
        "USAS-12": "12x70mm", "SPR310": "12x70mm", "TOZ-34": "12x70mm"
    },
    "Pistols": {
        "G18C": "9x19mm", "G17": "9x19mm", "Desert Eagle": ".44 Cal",
        "Gold Deagle": ".44 Cal", "M1911": ".45 ACP", "T54": "7.62x25mm",
        "M9A3": "9x19mm", "F57": "5.7x28mm", "CZ52": "7.62x25mm",
        "M45A1": ".45 ACP", "T05": "9x19mm", "MP9": "9x19mm"
    }
}

# ----------------------
# OTHER DATA (UNCHANGED)
# ----------------------
ammo_data = {
    "5.45x39mm": ["HP", "PS", "BP", "BS", "PP", "PRS"],
    "5.56x45mm": ["HP Hunting", "FMJ Hunting", "M193", "M855", "M855A1", "M995"],
    "5.8x42mm": ["DBP87", "DVP88", "DVC12"],
    "7.62x39mm": ["HP", "LP", "US", "T45M", "PS", "BP", "AP"],
    "7.62x51mm": ["UN", "BPZ", "M80", "M62", "M61"],
    "7.62x54mm": ["LPS", "T46M", "7BT1", "SNB", "7N37"],
    ".338 Lapua": ["UPZ", "FMJ", "AP"],
    ".44 Cal": ["LFNP", "SJHP", "JSP"],
    ".45 ACP": ["HS", "FMJ", "AP"],
    "7.62x25mm": ["PT", "PST", "LRN", "AKBS", "PS"],
    "9x19mm": ["PSO", "PST", "AP6.3", "DumDum", "7N31"],
    "12x70mm": ["Type 5 buckshot", "Type 7 buckshot", "Type 8 buckshot", "Flechette Buckshot", "Dual Shell", "Led Slug", "Grizzly Slug", "RIP Slug", "GT Slug", "AP Slug"],
    "5.7x28mm": ["SS197SR", "SS190", "R37.X", "L191", "SS198"],
    "9x39mm": ["SP5", "SP6", "7N9", "7N12"]
}

armors = {
    "Tier 1": ["Retro Sapper Bulletproof Vest", "Retro Bulletproof Vest", "Old Security Body Armor"],
    "Tier 2": ["Security Body Armor", "220 Body Armor", "Retro Infantry Bulletproof Vest"],
    "Tier 3": ["KN Regulation Body Armor", "PCA350 Body Armor", "Standard SWAT Armor",
               "H-Tac SWAT Body Armor", "KN Assault Body Armor", "H-LC Lightweight Body Armor"],
    "Tier 4": ["SEK Fortress Body Armor", "IND401 Body Armor", "6B13 Body Armor",
               "6B23 Body Armor", "Spartan B Body Armor"],
    "Tier 5": ["H-LC Tactical Body Armor", "Defender M4 Heavy Body Armor (Black)",
               "Defender M4 Heavy Body Armor (Green)", "926 Composite Body Armor",
               "IMTV Samurai Assault Armor", "IMTV Samurai Standard Armor", "IMTV Samurai Full Protection",
               "BT6 Heavy Body Armor"],
    "Tier 6": ["Marshal Heavy Body Armor", "6B45 Heavy Body Armor", "BT101 Tactical Body Armor",
               "KN Composite Body Armor"]
}

helmets = {
    "Tier 1": ["Kelsey Fire Helmet", "Lightweight Safety Helmet", "Motorcycle Helmet", "Tanker Protective Cap"],
    "Tier 2": ["Retro Military Helmet", "Retro Steel Helmet", "Security Helmet", "Aviator Helmet",
               "Security Riot Helmet", "PAS Standard Helmet"],
    "Tier 3": ["PAS2 Helmet", "F70 Tactical Helmet", "SH12 Military Helmet", "6B4 Helmet",
               "6B4 Helmet (Squad S)", "6B5 Helmet"],
    "Tier 4": ["SH40 Military Helmet", "IND Tactical Helmet", "IND Tactical Helmet (Variant)", "IND200 Helmet",
               "F80 Tactical Helmet", "SH18 Military Helmet", "KSS Tactical Helmet", "KSS2 Tactical Helmet",
               "56K Helicopter Helmet"],
    "Tier 5": ["SH Matzka 2 Helmet", "SH60 Military Helmet", "SH50 Military Helmet", "FA Assault Tactical Helmet",
               "03 Heavy Tactical Helmet", "RSP Heavy Tactical Helmet", "AN95 Heavy Blast Helmet"],
    "Tier 6": ["6BNT Helmet", "RST Special Forces Helmet", "HGB4 Offensive Helmet", "SH65 Military Helmet",
               "IND50 Heavy Tactical Helmet", "D009 Blast Helmet", "AS200 Heavy Tactical Helmet"]
}

Backpacks = [
    "Sling Bag","Lightweight Camping Backpack","Medium Camping Backpack","Simple Backpack","Canvas Backpack",
    "Canvas Camping Backpack","Sports Backpack","Cowhide Backpack","Outdoor Travel Backpack",
    "RUSH Tactical Backpack","Large Camping Backpack","XA4 Tactical Backpack","Med Field Backpack",
    "Chapman Military Backpack","AMP7 Assault Backpack","Retro Marching Backpack","LUC Expanded Tactical Backpack",
    "926 Field Backpack","Field Camping Backpack","RAL Heavy Military Backpack"
]


# ----------------------
# ENSURE BUILD CODES
# ----------------------
for cat in WEAPONS_DATA.values():
    for weapon in cat:
        st.session_state.build_codes.setdefault(weapon, [])

# ----------------------
# FILTER STATE
# ----------------------
if "weapon_filters" not in st.session_state:
    st.session_state.weapon_filters = {cat: True for cat in WEAPONS_DATA}

if "armor_filters" not in st.session_state:
    st.session_state.armor_filters = {tier: True for tier in armors}

if "helmet_filters" not in st.session_state:
    st.session_state.helmet_filters = {tier: True for tier in helmets}

# ----------------------
# UI
# ----------------------
st.title("ABI Randomizer & Build Codes")

# Weapon Categories Buttons
st.subheader("Weapon Categories")
cols = st.columns(len(WEAPONS_DATA))
for i, cat in enumerate(WEAPONS_DATA):
    if cols[i].button(
        f"{'🟢' if st.session_state.weapon_filters[cat] else '🔴'} {cat}",
        key=f"weapon_{cat}"
    ):
        st.session_state.weapon_filters[cat] = not st.session_state.weapon_filters[cat]

# Armor Tiers Buttons
st.subheader("Armor Tiers")
cols = st.columns(len(armors))
for i, tier in enumerate(armors):
    if cols[i].button(
        f"{'🟢' if st.session_state.armor_filters[tier] else '🔴'} {tier}",
        key=f"armor_{tier}"
    ):
        st.session_state.armor_filters[tier] = not st.session_state.armor_filters[tier]

# Helmet Tiers Buttons
st.subheader("Helmet Tiers")
cols = st.columns(len(helmets))
for i, tier in enumerate(helmets):
    if cols[i].button(
        f"{'🟢' if st.session_state.helmet_filters[tier] else '🔴'} {tier}",
        key=f"helmet_{tier}"
    ):
        st.session_state.helmet_filters[tier] = not st.session_state.helmet_filters[tier]

# ----------------------
# GENERATOR UI
# ----------------------
st.header("Generate Loadout")

if st.button("Generate Loadout"):
    st.code(generate_loadout(lockdown=False, disable=False, exclude=False))
# ----------------------
# RANDOMIZER
# ----------------------
def generate_loadout(lockdown, disable, exclude):

    weapons = []

    for cat, items in WEAPONS_DATA.items():

        if not st.session_state.weapon_filters[cat]:
            continue

        if disable and cat in ("Shotguns","Pistols","Carbines"):
            continue

        for w, cal in items.items():
            weapons.append((cat,w,cal))

    if not weapons:
        return "No weapons available."

    category, weapon, caliber = random.choice(weapons)

    ammo = f"{caliber} {random.choice(ammo_data.get(caliber,[caliber]))}"

    armor_tiers = [t for t in armors if st.session_state.armor_filters[t]]
    helmet_tiers = [t for t in helmets if st.session_state.helmet_filters[t]]

    if lockdown:
        armor_tiers = [t for t in armor_tiers if t != "Tier 6"]
        helmet_tiers = [t for t in helmet_tiers if t != "Tier 6"]

    if exclude:
        armor_tiers = [t for t in armor_tiers if t not in ("Tier 1","Tier 2")]
        helmet_tiers = [t for t in helmet_tiers if t not in ("Tier 1","Tier 2")]

    armor_tier = random.choice(armor_tiers)
    helmet_tier = random.choice(helmet_tiers)

    armor_piece = random.choice(armors[armor_tier])
    helmet_piece = random.choice(helmets[helmet_tier])
    backpack = random.choice(Backpacks)

    codes = st.session_state.build_codes.get(weapon,[])
    code = random.choice(codes) if codes else None

    lines = [
        "--- RANDOM LOADOUT ---",
        f"CLASS: {category}",
        f"WEAPON: {weapon}",
        f"AMMO: {ammo}"
    ]

    if code:
        lines.append(f"BUILD CODE: {code}")

    lines.append(f"ARMOR: {armor_piece} ({armor_tier})")
    lines.append(f"HELMET: {helmet_piece} ({helmet_tier})")
    lines.append(f"BACKPACK: {backpack}")
    lines.append(f"MAP: {random.choice(['Airport','Farm','Valley','TV','Northridge','Armory'])}")
    lines.append("----------------------")

    return "\n".join(lines)

# ----------------------
# GENERATOR UI
# ----------------------
st.header("Generate Loadout")

c1,c2,c3 = st.columns(3)

with c1:
    lockdown = st.checkbox("Lockdown (No Tier 6)")

with c2:
    disable = st.checkbox("Disable Shotguns/Pistols/Carbines")

with c3:
    exclude = st.checkbox("Exclude Tier 1 & 2")

if st.button("Generate Loadout"):
    st.code(generate_loadout(lockdown,disable,exclude))

# ----------------------
# BUILD CODE EDITOR
# ----------------------
st.header("Build Codes")

weapon_choice = st.selectbox("Weapon", list(st.session_state.build_codes.keys()))

new_code = st.text_input("New Build Code")

if st.button("Add Code"):

    if new_code and new_code not in st.session_state.build_codes[weapon_choice]:

        st.session_state.build_codes[weapon_choice].append(new_code)

        save_build_codes_local(st.session_state.build_codes)
        save_build_codes_github(st.session_state.build_codes)

        st.success("Build code added")

st.json(st.session_state.build_codes)

