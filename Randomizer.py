import streamlit as st
import json
import random
import time
import uuid
from collections import Counter
from github import Github
from github.GithubException import UnknownObjectException

# -----------------------------
# ADMIN PASSWORD & CONFIG
# -----------------------------
DATA_FILE = "site_data.json"
ADMIN_PASSWORD = "5ironman17admin"

GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")
REPO_NAME = st.secrets.get("REPO_NAME")

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

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
    st.session_state.username = f"Player-{st.session_state.user_id[:5]}"
    st.session_state.armor_filters = list(armors.keys())  # all tiers selected
    st.session_state.helmet_filters = list(helmets.keys())

if "roll_history" not in st.session_state:
    st.session_state.roll_history = {}  # per user

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# -----------------------------
# GITHUB HELPER FUNCTIONS
# -----------------------------
def get_github_repo():
    if not GITHUB_TOKEN or not REPO_NAME:
        return None
    try:
        g = Github(GITHUB_TOKEN)
        return g.get_repo(REPO_NAME)
    except Exception:
        return None

repo = get_github_repo()

def load_data():
    if repo:
        try:
            file_content = repo.get_contents(DATA_FILE)
            return json.loads(file_content.decoded_content.decode())
        except UnknownObjectException:
            return {}
    else:
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

def save_data(data):
    if repo:
        try:
            try:
                file = repo.get_contents(DATA_FILE)
                repo.update_file(DATA_FILE, "Update data", json.dumps(data, indent=4), file.sha)
            except UnknownObjectException:
                repo.create_file(DATA_FILE, "Create data", json.dumps(data, indent=4))
        except Exception as e:
            st.warning(f"GitHub save failed: {e}")
    else:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

site_data = load_data()
site_data.setdefault("roll_history", {})
site_data.setdefault("analytics", {"weapon": Counter(), "armor": Counter(), "helmet": Counter(), "backpack": Counter()})

# -----------------------------
# LOADOUT GENERATOR
# -----------------------------
def generate_loadout():
    # Weapon + Ammo
    category = random.choice(list(WEAPONS_DATA.keys()))
    weapon = random.choice(list(WEAPONS_DATA[category].keys()))
    caliber = WEAPONS_DATA[category][weapon]
    ammo = random.choice(ammo_data.get(caliber, [caliber]))

    # Armor + Helmet respecting filters
    armor_pool = [a for tier in st.session_state.armor_filters for a in armors.get(tier,[])]
    helmet_pool = [h for tier in st.session_state.helmet_filters for h in helmets.get(tier,[])]
    armor_choice = random.choice(armor_pool) if armor_pool else "No Armor"
    helmet_choice = random.choice(helmet_pool) if helmet_pool else "No Helmet"

    backpack_choice = random.choice(backpacks) if backpacks else "No Backpack"

    roll = {
        "weapon": weapon,
        "ammo": ammo,
        "armor": armor_choice,
        "helmet": helmet_choice,
        "backpack": backpack_choice
    }

    # Save to roll history
    user = st.session_state.username
    site_data["roll_history"].setdefault(user, [])
    site_data["roll_history"][user].append(roll)

    # Update analytics
    site_data["analytics"]["weapon"][weapon] += 1
    site_data["analytics"]["armor"][armor_choice] += 1
    site_data["analytics"]["helmet"][helmet_choice] += 1
    site_data["analytics"]["backpack"][backpack_choice] += 1

    save_data(site_data)
    return roll

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("ABI Randomizer")

tab1, tab2 = st.tabs(["Randomizer", "Admin Panel"])

# --- TAB 1: RANDOMIZER ---
with tab1:
    st.header("Select Armor and Helmet Tiers")
    armor_selected = st.multiselect("Armor Tiers", list(armors.keys()), default=st.session_state.armor_filters)
    helmet_selected = st.multiselect("Helmet Tiers", list(helmets.keys()), default=st.session_state.helmet_filters)
    st.session_state.armor_filters = armor_selected
    st.session_state.helmet_filters = helmet_selected

    st.header("Generate Loadout")
    if st.button("Generate Loadout"):
        roll = generate_loadout()
        st.write(f"**Weapon:** {roll['weapon']} ({roll['ammo']})")
        st.write(f"**Armor:** {roll['armor']}")
        st.write(f"**Helmet:** {roll['helmet']}")
        st.write(f"**Backpack:** {roll['backpack']}")

# --- TAB 2: ADMIN PANEL ---
with tab2:
    if not st.session_state.authenticated:
        pw = st.text_input("Enter admin password", type="password")
        if st.button("Login"):
            if pw == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.success("Admin access granted")
            else:
                st.error("Incorrect password")
        st.stop()

    st.header("Site Data JSON")
    st.json(site_data)

    st.header("Current Users and Roll History")
    for user, rolls in site_data["roll_history"].items():
        st.subheader(user)
        for r in rolls[-5:]:  # show last 5 rolls
            st.write(r)

    st.header("Analytics")
    st.write("Most rolled weapons:", site_data["analytics"]["weapon"].most_common(5))
    st.write("Most rolled armor:", site_data["analytics"]["armor"].most_common(5))
    st.write("Most rolled helmets:", site_data["analytics"]["helmet"].most_common(5))
    st.write("Most rolled backpacks:", site_data["analytics"]["backpack"].most_common(5))


