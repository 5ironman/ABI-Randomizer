import streamlit as st
import json
import random
import os
from github import Github, Auth
from github.GithubException import UnknownObjectException

# ----------------------
# CONFIG & FILE PATHS
# ----------------------
BUILD_CODES_FILE = "build_codes.json"

# ----------------------
# GITHUB SETUP
# ----------------------
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = st.secrets.get("REPO_NAME", None)

def get_github_repo():
    if not GITHUB_TOKEN or not REPO_NAME:
        st.warning("Missing GITHUB_TOKEN or REPO_NAME in Streamlit Secrets!")
        return None
    try:
        g = Github(auth=Auth.Token(GITHUB_TOKEN))  # ✅ fixed deprecation warning
        user = g.get_user()
        st.sidebar.success(f"Connected as: {user.login}")
        repo = g.get_repo(REPO_NAME)
        return repo
    except Exception as e:
        st.error(f"GitHub connection failed: {e}")
        return None

repo = get_github_repo()

# ----------------------
# SAVE & LOAD FUNCTIONS
# ----------------------
def load_build_codes_local():
    if os.path.exists(BUILD_CODES_FILE):
        try:
            with open(BUILD_CODES_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def load_build_codes_github():
    if repo is None:
        return {}
    try:
        file_content = repo.get_contents(BUILD_CODES_FILE)
        return json.loads(file_content.decoded_content.decode())
    except UnknownObjectException:
        return {}
    except Exception as e:
        st.warning(f"GitHub load failed: {e}")
        return {}

def save_build_codes_local(codes):
    with open(BUILD_CODES_FILE, "w") as f:
        json.dump(codes, f, indent=4)

def save_build_codes_github(codes, commit_message="Update build codes"):
    if repo is None:
        return
    try:
        try:
            file = repo.get_contents(BUILD_CODES_FILE)
            repo.update_file(
                BUILD_CODES_FILE,
                commit_message,
                json.dumps(codes, indent=4),
                file.sha
            )
        except UnknownObjectException:
            repo.create_file(
                BUILD_CODES_FILE,
                commit_message,
                json.dumps(codes, indent=4)
            )
    except Exception as e:
        st.error(f"GitHub save failed: {e}")

# ----------------------
# INITIALIZE SESSION STATE
# ----------------------
if "build_codes" not in st.session_state:
    if repo:
        codes = load_build_codes_github()
    else:
        codes = load_build_codes_local()
    st.session_state.build_codes = codes

# ----------------------
# DEFAULT WEAPONS
# ----------------------
DEFAULT_WEAPONS = ["HK416", "M4A1"]
for w in DEFAULT_WEAPONS:
    if w not in st.session_state.build_codes:
        st.session_state.build_codes[w] = []

# ----------------------
# FULL WEAPONS DATA
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

# Ensure all weapons exist in build_codes
for cat in WEAPONS_DATA.values():
    for weapon_name in cat.keys():
        if weapon_name not in st.session_state.build_codes:
            st.session_state.build_codes[weapon_name] = []

# ----------------------
# RANDOM LOADOUT FUNCTION (COMPLETELY RANDOM WEAPON)
# ----------------------
def generate_full_abi_loadout(lockdown=False, disable_shot_pistol=False, exclude_t1_t2=False, armored_rig_chance=0.25):
    weapons_data = WEAPONS_DATA

    # Flatten all weapons into a single list for uniform randomization
    all_weapons = []
    for cat, weapons in weapons_data.items():
        if disable_shot_pistol and cat in ("Shotguns", "Pistols", "Carbines"):
            continue
        for weapon_name, caliber in weapons.items():
            all_weapons.append((cat, weapon_name, caliber))

    if not all_weapons:
        st.warning("No weapons available with current filters.")
        return ""

    category, weapon, caliber = random.choice(all_weapons)

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

    ammo_display = f"{caliber} {random.choice(ammo_data.get(caliber, [caliber]))}"

    # Armor, helmets, backpacks (same as before)
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

    armored_rigs = {
        "Tier 2": ["M1955 Combat Vest"],
        "Tier 3": ["6B5 Armored Rig", "Sentry 3 Armored Chest", "926 Security Armored Rig"],
        "Tier 4": ["Sentry 305 Armored Rig", "TM1 Armored Rig", "TM2 Armored Rig"],
        "Tier 5": ["H-Tac A8 Armored Rig", "Warrior Heavy Armored Rig", "H-Tac A9 Armored Rig",
                   "Defender M4 Heavy Armored Rig"],
        "Tier 6": ["Spartan C Heavy Armored Rig", "AL Tactical Armored Rig", "AVS Heavy Armored Rig",
                   "AL Commander Armored Rig", "AL Assault Armored Rig"]
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
        "Sling Bag", "Lightweight Camping Backpack", "Medium Camping Backpack", "Simple Backpack", "Canvas Backpack",
        "Canvas Camping Backpack", "Sports Backpack", "Cowhide Backpack", "Outdoor Travel Backpack",
        "RUSH Tactical Backpack", "Large Camping Backpack", "XA4 Tactical Backpack", "Med Field Backpack",
        "Chapman Military Backpack", "AMP7 Assault Backpack", "Retro Marching Backpack", "LUC Expanded Tactical Backpack",
        "926 Field Backpack", "Field Camping Backpack", "RAL Heavy Military Backpack"
    ]

    armor_tiers = list(armors.keys())
    helmet_tiers = list(helmets.keys())
    if lockdown:
        armor_tiers = [t for t in armor_tiers if t != "Tier 6"]
        helmet_tiers = [t for t in helmet_tiers if t != "Tier 6"]
    if exclude_t1_t2:
        armor_tiers = [t for t in armor_tiers if t not in ("Tier 1", "Tier 2")]
        helmet_tiers = [t for t in helmet_tiers if t not in ("Tier 1", "Tier 2")]

    armor_tier = random.choice(armor_tiers)
    use_armored_rig = random.random() < armored_rig_chance and armored_rigs.get(armor_tier)
    if use_armored_rig:
        armor_piece = random.choice(armored_rigs[armor_tier])
        armor_is_rig = True
    else:
        armor_piece = random.choice(armors[armor_tier])
        armor_is_rig = False

    helmet_tier = random.choice(helmet_tiers)
    helmet_piece = random.choice(helmets[helmet_tier])
    backpack_choice = random.choice(Backpacks)

    build_code_choice = None
    codes = st.session_state.build_codes.get(weapon, [])
    if codes:
        build_code_choice = random.choice(codes)

    out_lines = [
        "--- ARENA BREAKOUT: INFINITE RANDOM LOADOUT ---",
        f"CLASS:    {category}",
        f"WEAPON:   {weapon}",
        f"AMMO:     {ammo_display}"
    ]
    if build_code_choice:
        out_lines.append(f"BUILD CODE: {build_code_choice}")
    out_lines.append(f"{'ARMORED RIG' if armor_is_rig else 'ARMOR'}: {armor_piece} ({armor_tier})")
    out_lines.append(f"HELMET:   {helmet_piece} ({helmet_tier})")
    out_lines.append(f"BACKPACK: {backpack_choice}")
    out_lines.append(f"MAP:      {random.choice(['Airport', 'Farm', 'Valley', 'TV', 'Northridge', 'Armory'])}")
    out_lines.append("-----------------------------------------------")

    return "\n".join(out_lines)

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("ABI Randomizer & Build Codes Editor")

# --- Generate Loadout ---
st.header("Generate Random Loadout")
col1, col2, col3 = st.columns(3)
with col1:
    lockdown = st.checkbox("Lockdown (exclude Tier 6)")
with col2:
    disable_shot_pistol = st.checkbox("Disable Shotguns, Pistols & Carbines")
with col3:
    exclude_t12 = st.checkbox("Exclude Tier 1 & 2 Armor/Helmets")

if st.button("Generate Loadout"):
    result = generate_full_abi_loadout(lockdown, disable_shot_pistol, exclude_t12)
    st.code(result)

# --- Edit Build Codes ---
st.header("Edit Build Codes")
weapon_choice = st.selectbox("Select Weapon", list(st.session_state.build_codes.keys()))
new_code = st.text_input("Enter New Build Code", key="new_code_input")

if st.button("Add Build Code"):
    if new_code and new_code not in st.session_state.build_codes[weapon_choice]:
        st.session_state.build_codes[weapon_choice].append(new_code)
        save_build_codes_local(st.session_state.build_codes)
        if repo:
            save_build_codes_github(
                st.session_state.build_codes,
                commit_message=f"Added build code {new_code} to {weapon_choice}"
            )
        st.success(f"Added build code {new_code} to {weapon_choice}")
        st.session_state.new_code_input = ""
        st.experimental_rerun()  # refresh UI

st.subheader("Current Build Codes")
st.json(st.session_state.build_codes)
