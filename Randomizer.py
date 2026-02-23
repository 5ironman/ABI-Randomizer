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
        g = Github(auth=Auth.Token(GITHUB_TOKEN))
        user = g.get_user()
        st.sidebar.success(f"Connected as: {user.login}")
        return g.get_repo(REPO_NAME)
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
# SESSION STATE INIT
# ----------------------
if "build_codes" not in st.session_state:
    codes = load_build_codes_github() if repo else load_build_codes_local()
    st.session_state.build_codes = codes

if "new_code_input" not in st.session_state:
    st.session_state.new_code_input = ""
if "reset_build_code_input" not in st.session_state:
    st.session_state.reset_build_code_input = False

# ----------------------
# WEAPONS DATA
# ----------------------
WEAPONS_DATA = {
    "Assault Rifles": {"HK416": "5.56x45mm", "M4A1": "5.56x45mm"},
    "SMGs": {"P90": "5.7x28mm", "MP5": "9x19mm"},
    "Carbines": {"SKS": "7.62x39mm", "M16": "5.56x45mm"},
    "Marksman Rifles": {"M110": "7.62x51mm", "SVDS": "7.62x54mm"},
    "Sniper Rifles": {"M24": "7.62x51mm", "SJ16": ".338 Lapua"},
    "Shotguns": {"S12K": "12x70mm", "M870": "12x70mm"},
    "Pistols": {"G18C": "9x19mm", "M1911": ".45 ACP"}
}

# Ensure all weapons exist in build_codes
for cat in WEAPONS_DATA.values():
    for weapon_name in cat.keys():
        if weapon_name not in st.session_state.build_codes:
            st.session_state.build_codes[weapon_name] = []

# ----------------------
# ARMOR / HELMETS / BACKPACKS
# ----------------------
armors = {
    "Tier 1": ["Retro Sapper Vest"], "Tier 2": ["Security Body Armor"],
    "Tier 3": ["KN Regulation Armor"], "Tier 4": ["SEK Fortress Armor"],
    "Tier 5": ["H-LC Tactical Armor"], "Tier 6": ["Marshal Heavy Armor"]
}
helmets = {
    "Tier 1": ["Light Helmet"], "Tier 2": ["Retro Military Helmet"],
    "Tier 3": ["PAS2 Helmet"], "Tier 4": ["SH40 Helmet"],
    "Tier 5": ["SH Matzka 2 Helmet"], "Tier 6": ["6BNT Helmet"]
}
Backpacks = ["Sling Bag", "Medium Backpack", "RUSH Tactical Backpack"]

# ----------------------
# RANDOM LOADOUT FUNCTION
# ----------------------
def generate_full_abi_loadout(lockdown=False, disable_shot_pistol=False, exclude_t1_t2=False, armored_rig_chance=0.25):
    # Flatten weapons for equal probability
    all_weapons = []
    for cat, weapons in WEAPONS_DATA.items():
        if disable_shot_pistol and cat in ("Shotguns", "Pistols", "Carbines"):
            continue
        for weapon_name, caliber in weapons.items():
            all_weapons.append((cat, weapon_name, caliber))
    if not all_weapons:
        return "No weapons available with current filters."
    category, weapon, caliber = random.choice(all_weapons)

    # Ammo
    ammo_data = {
        "5.45x39mm": ["HP", "PS"], "5.56x45mm": ["M193", "M855"],
        "5.7x28mm": ["SS197SR"], "9x19mm": ["PSO"], "12x70mm": ["Type 5 buckshot"],
        ".338 Lapua": ["UPZ"], ".45 ACP": ["HS"], "7.62x51mm": ["M80"], "7.62x54mm": ["7N37"], "7.62x39mm": ["PS"]
    }
    ammo_display = f"{caliber} {random.choice(ammo_data.get(caliber, [caliber]))}"

    # Armor / Helmet / Backpack
    armor_tiers = list(armors.keys())
    helmet_tiers = list(helmets.keys())
    if lockdown:
        armor_tiers = [t for t in armor_tiers if t != "Tier 6"]
        helmet_tiers = [t for t in helmet_tiers if t != "Tier 6"]
    if exclude_t1_t2:
        armor_tiers = [t for t in armor_tiers if t not in ("Tier 1","Tier 2")]
        helmet_tiers = [t for t in helmet_tiers if t not in ("Tier 1","Tier 2")]

    armor_tier = random.choice(armor_tiers)
    helmet_tier = random.choice(helmet_tiers)
    armor_piece = random.choice(armors[armor_tier])
    helmet_piece = random.choice(helmets[helmet_tier])
    backpack_choice = random.choice(Backpacks)

    # Build code
    codes = st.session_state.build_codes.get(weapon, [])
    build_code_choice = random.choice(codes) if codes else None

    out_lines = [
        "--- RANDOM LOADOUT ---",
        f"CLASS: {category}",
        f"WEAPON: {weapon}",
        f"AMMO: {ammo_display}"
    ]
    if build_code_choice:
        out_lines.append(f"BUILD CODE: {build_code_choice}")
    out_lines.append(f"ARMOR: {armor_piece} ({armor_tier})")
    out_lines.append(f"HELMET: {helmet_piece} ({helmet_tier})")
    out_lines.append(f"BACKPACK: {backpack_choice}")
    out_lines.append(f"MAP: {random.choice(['Airport','Farm','Valley','TV','Northridge','Armory'])}")
    out_lines.append("--------------------")
    return "\n".join(out_lines)

# ----------------------
# STREAMLIT UI
# ----------------------
st.title("ABI Randomizer & Build Codes Editor")

# Generate Loadout
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

# Edit Build Codes
st.header("Edit Build Codes")
weapon_choice = st.selectbox("Select Weapon", list(st.session_state.build_codes.keys()))

new_code = st.text_input(
    "Enter New Build Code",
    value="" if st.session_state.reset_build_code_input else st.session_state.get("new_code_input", ""),
    key="new_code_input"
)

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
        st.session_state.reset_build_code_input = True
    else:
        st.warning("Enter a valid and unique build code.")

# Reset input safely
if st.session_state.reset_build_code_input:
    st.session_state.reset_build_code_input = False

st.subheader("Current Build Codes")
st.json(st.session_state.build_codes)
