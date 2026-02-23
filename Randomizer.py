import streamlit as st
import json
import random
import os
from github import Github, Auth
from github.GithubException import UnknownObjectException
from streamlit_autorefresh import st_autorefresh
from filelock import FileLock

# ----------------------
# CONFIG
# ----------------------
BUILD_CODES_FILE = "build_codes.json"
LOCK_FILE = BUILD_CODES_FILE + ".lock"
REFRESH_INTERVAL_MS = 5000
BUILD_CODES_PASSWORD = "ABI-RANDOM123"

# ----------------------
# AUTO REFRESH
# ----------------------
st_autorefresh(interval=REFRESH_INTERVAL_MS, key="auto_refresh")

# ----------------------
# GITHUB CONFIG
# ----------------------
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = st.secrets.get("REPO_NAME", None)

def get_github_repo():
    if not GITHUB_TOKEN or not REPO_NAME:
        return None
    try:
        g = Github(auth=Auth.Token(GITHUB_TOKEN))
        return g.get_repo(REPO_NAME)
    except Exception as e:
        st.warning(f"GitHub access failed: {e}")
        return None

repo = get_github_repo()

# ----------------------
# LOAD / SAVE FUNCTIONS WITH FILELOCK
# ----------------------
def load_build_codes_local():
    with FileLock(LOCK_FILE):
        if os.path.exists(BUILD_CODES_FILE):
            with open(BUILD_CODES_FILE, "r") as f:
                return json.load(f)
        return {}

def save_build_codes_local(codes):
    with FileLock(LOCK_FILE):
        with open(BUILD_CODES_FILE, "w") as f:
            json.dump(codes, f, indent=4)

def load_build_codes_github():
    if repo is None:
        return {}
    try:
        file_content = repo.get_contents(BUILD_CODES_FILE)
        return json.loads(file_content.decoded_content.decode())
    except Exception:
        return {}

def save_build_codes_github(codes):
    if repo is None:
        return
    try:
        try:
            file = repo.get_contents(BUILD_CODES_FILE)
            latest_codes = json.loads(file.decoded_content.decode())
        except UnknownObjectException:
            file = None
            latest_codes = {}

        # Merge new codes
        for weapon, code_list in codes.items():
            latest_codes.setdefault(weapon, [])
            for code in code_list:
                if code not in latest_codes[weapon]:
                    latest_codes[weapon].append(code)

        content = json.dumps(latest_codes, indent=4)

        if file:
            repo.update_file(
                path=BUILD_CODES_FILE,
                message="update build codes",
                content=content,
                sha=file.sha
            )
        else:
            repo.create_file(
                path=BUILD_CODES_FILE,
                message="create build codes",
                content=content
            )
    except Exception as e:
        st.warning(f"GitHub save failed: {e}")

# ----------------------
# SESSION STATE INIT
# ----------------------
st.session_state.setdefault("build_codes", load_build_codes_github() if repo else load_build_codes_local())
st.session_state.setdefault("weapon_filters", {})
st.session_state.setdefault("armor_filters", {})
st.session_state.setdefault("helmet_filters", {})
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("codes_to_remove", [])

# ----------------------
# WEAPONS DATA
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
# OTHER DATA
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
    "12x70mm": ["Type 5 buckshot", "Type 7 buckshot", "Type 8 buckshot",
                "Flechette Buckshot", "Dual Shell", "Led Slug", "Grizzly Slug",
                "RIP Slug", "GT Slug", "AP Slug"],
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

backpacks = [
    "Sling Bag", "Lightweight Camping Backpack", "Medium Camping Backpack", "Simple Backpack", "Canvas Backpack",
    "Canvas Camping Backpack", "Sports Backpack", "Cowhide Backpack", "Outdoor Travel Backpack",
    "RUSH Tactical Backpack", "Large Camping Backpack", "XA4 Tactical Backpack", "Med Field Backpack",
    "Chapman Military Backpack", "AMP7 Assault Backpack", "Retro Marching Backpack", "LUC Expanded Tactical Backpack",
    "926 Field Backpack", "Field Camping Backpack", "RAL Heavy Military Backpack"
]

# ----------------------
# ENSURE BUILD CODE KEYS
# ----------------------
for cat in WEAPONS_DATA.values():
    st.session_state.build_codes.update({w: [] for w in cat if w not in st.session_state.build_codes})

# ----------------------
# FILTER STATE
# ----------------------
st.session_state.weapon_filters = {cat: True for cat in WEAPONS_DATA}
st.session_state.armor_filters = {tier: True for tier in armors}
st.session_state.helmet_filters = {tier: True for tier in helmets}

# ----------------------
# RANDOMIZER FUNCTION
# ----------------------
def generate_loadout():
    weapons = [(cat, w, cal) for cat, items in WEAPONS_DATA.items()
               if st.session_state.weapon_filters.get(cat, True)
               for w, cal in items.items()]
    if not weapons:
        return "No weapons available."
    cat, weapon, cal = random.choice(weapons)
    ammo = f"{cal} {random.choice(ammo_data.get(cal,[cal]))}"
    armor_tiers = [t for t in armors if st.session_state.armor_filters[t]]
    helmet_tiers = [t for t in helmets if st.session_state.helmet_filters[t]]
    armor_piece = f"{random.choice(armors[random.choice(armor_tiers)])} ({random.choice(armor_tiers)})"
    helmet_piece = f"{random.choice(helmets[random.choice(helmet_tiers)])} ({random.choice(helmet_tiers)})"
    backpack = random.choice(backpacks)
    codes = st.session_state.build_codes.get(weapon, [])
    code = random.choice(codes) if codes else None
    lines = [f"CLASS: {cat}", f"WEAPON: {weapon}", f"AMMO: {ammo}"]
    if code:
        lines.append(f"BUILD CODE: {code}")
    lines += [f"ARMOR: {armor_piece}", f"HELMET: {helmet_piece}", f"BACKPACK: {backpack}"]
    return "\n".join(lines)

# ----------------------
# MULTI-USER SAFE ADD
# ----------------------
def add_build_code(weapon, new_code):
    new_code = new_code.strip()
    if not new_code:
        return
    latest_codes = load_build_codes_github() if repo else load_build_codes_local()
    latest_codes.setdefault(weapon, [])
    st.session_state.build_codes.setdefault(weapon, [])
    if new_code not in latest_codes[weapon]:
        latest_codes[weapon].append(new_code)
        st.session_state.build_codes[weapon] = latest_codes[weapon]
        save_build_codes_local(latest_codes)
        save_build_codes_github(latest_codes)
        st.success(f"Added '{new_code}' to {weapon}")
    else:
        st.warning(f"Code '{new_code}' already exists for {weapon}")

# ----------------------
# MULTI-USER SAFE REMOVE
# ----------------------
def remove_build_codes(weapon, codes_to_remove):
    if not codes_to_remove:
        return
    for code in codes_to_remove:
        if code in st.session_state.build_codes[weapon]:
            st.session_state.build_codes[weapon].remove(code)
    save_build_codes_local(st.session_state.build_codes)
    save_build_codes_github(st.session_state.build_codes)
    st.success(f"Removed selected codes from {weapon}")

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("ABI Randomizer & Build Codes")
tab1, tab2 = st.tabs(["Randomizer","Build Codes"])

# --- TAB 1 ---
with tab1:
    st.subheader("Weapon Categories")
    for cat in WEAPONS_DATA:
        st.session_state.weapon_filters[cat] = st.checkbox(
            cat, 
            value=st.session_state.weapon_filters[cat],
            key=f"weapon_{cat}"
        )

    st.subheader("Armor Tiers")
    for tier in armors:
        st.session_state.armor_filters[tier] = st.checkbox(
            tier, 
            value=st.session_state.armor_filters[tier],
            key=f"armor_{tier}"
        )

    st.subheader("Helmet Tiers")
    for tier in helmets:
        st.session_state.helmet_filters[tier] = st.checkbox(
            tier, 
            value=st.session_state.helmet_filters[tier],
            key=f"helmet_{tier}"
        )

    st.header("Generate Loadout")
    if st.button("Generate Loadout"):
        st.code(generate_loadout())

# --- TAB 2 ---
with tab2:
    st.header("Build Codes Management")

    if not st.session_state.authenticated:
        pw = st.text_input("Enter password to edit build codes", type="password")
        if st.button("Submit Password"):
            if pw == BUILD_CODES_PASSWORD:
                st.session_state.authenticated = True
                st.success("Password correct!")
            else:
                st.error("Incorrect password")
        st.stop()

    weapon_choice = st.selectbox("Select Weapon", sorted(st.session_state.build_codes.keys()))

    # ADD
    st.subheader("Add Build Code")
    new_code = st.text_input("Enter new build code")
    if st.button("Add Code"):
        add_build_code(weapon_choice, new_code)

    # REMOVE
    st.subheader("Remove Build Codes")
    current_codes = st.session_state.build_codes.get(weapon_choice, [])
    if current_codes:
        st.session_state.codes_to_remove = st.multiselect(
            f"Select codes to remove from {weapon_choice}",
            current_codes,
            default=st.session_state.codes_to_remove,
            key="remove_multiselect"
        )
        if st.button("Remove Selected Codes"):
            remove_build_codes(weapon_choice, st.session_state.codes_to_remove)
            st.session_state.codes_to_remove = []
            st.experimental_rerun()
    else:
        st.info(f"No build codes for {weapon_choice}")

    # DEBUG
    st.subheader("Current Codes (DEBUG)")
    st.write(st.session_state.build_codes.get(weapon_choice, []))


