# app.py
import streamlit as st
import json
import random
import os
from github import Github, Auth
from github.GithubException import UnknownObjectException
from filelock import FileLock
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
import bcrypt

# ----------------------
# CONFIG
# ----------------------
BUILD_CODES_FILE = "build_codes.json"
USER_ROLLS_FILE = "user_rolls.json"
USER_ACCOUNTS_FILE = "user_accounts.json"
LOCK_FILE = BUILD_CODES_FILE + ".lock"
USER_LOCK_FILE = USER_ROLLS_FILE + ".lock"
ACCOUNTS_LOCK_FILE = USER_ACCOUNTS_FILE + ".lock"

BUILD_CODES_PASSWORD = st.secrets.get("build_codes_password", "")
ADMIN_PASSWORD = st.secrets.get("admin_password", "")
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = st.secrets.get("REPO_NAME", None)

# ----------------------
# GITHUB REPO
# ----------------------
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
# LOCAL LOAD / SAVE
# ----------------------
def load_json_local(file_path, lock_file):
    with FileLock(lock_file):
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return {}

def save_json_local(file_path, lock_file, data):
    with FileLock(lock_file):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

# ----------------------
# GITHUB LOAD / SAVE
# ----------------------
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
        for weapon, code_list in codes.items():
            latest_codes.setdefault(weapon, [])
            for code in code_list:
                if isinstance(code, dict):
                    if not any(c.get("code") == code["code"] for c in latest_codes[weapon] if isinstance(c, dict)):
                        latest_codes[weapon].append(code)
                else:
                    if code not in latest_codes[weapon]:
                        latest_codes[weapon].append(code)
        content = json.dumps(latest_codes, indent=4)
        if file:
            repo.update_file(BUILD_CODES_FILE, "update build codes", content, sha=file.sha)
        else:
            repo.create_file(BUILD_CODES_FILE, "create build codes", content)
    except Exception as e:
        st.warning(f"GitHub save failed: {e}")

def load_user_rolls_github():
    if repo is None:
        return {}
    try:
        file_content = repo.get_contents(USER_ROLLS_FILE)
        return json.loads(file_content.decoded_content.decode())
    except Exception:
        return {}

def save_user_rolls_github(rolls):
    if repo is None:
        return
    try:
        try:
            file = repo.get_contents(USER_ROLLS_FILE)
            latest_rolls = json.loads(file.decoded_content.decode())
        except UnknownObjectException:
            file = None
            latest_rolls = {}
        for user, user_roll_list in rolls.items():
            latest_rolls.setdefault(user, [])
            for r in user_roll_list:
                if r not in latest_rolls[user]:
                    latest_rolls[user].append(r)
        content = json.dumps(latest_rolls, indent=4)
        if file:
            repo.update_file(USER_ROLLS_FILE, "update user rolls", content, sha=file.sha)
        else:
            repo.create_file(USER_ROLLS_FILE, "create user rolls", content)
    except Exception as e:
        st.warning(f"GitHub save failed: {e}")

def load_user_accounts_github():
    if repo is None:
        return {}
    try:
        file_content = repo.get_contents(USER_ACCOUNTS_FILE)
        return json.loads(file_content.decoded_content.decode())
    except Exception:
        return {}

def save_user_accounts_github(accounts_dict):
    if repo is None:
        return
    try:
        try:
            file = repo.get_contents(USER_ACCOUNTS_FILE)
            latest_accounts = json.loads(file.decoded_content.decode())
        except UnknownObjectException:
            file = None
            latest_accounts = {}
        latest_accounts.update(accounts_dict)
        content = json.dumps(latest_accounts, indent=4)
        if file:
            repo.update_file(USER_ACCOUNTS_FILE, "update user accounts", content, sha=file.sha)
        else:
            repo.create_file(USER_ACCOUNTS_FILE, "create user accounts", content)
    except Exception as e:
        st.warning(f"GitHub save failed: {e}")

# ----------------------
# COOKIE SETUP
# ----------------------
cookies = EncryptedCookieManager(prefix="abi_random_", ="YOUR_SECRET_KEY_HERE")
if not cookies.ready():
    st.stop()

# ----------------------
# SESSION STATE INIT
# ----------------------
st.session_state.setdefault("user_authenticated", False)
st.session_state.setdefault("username", "")
st.session_state.setdefault("user_accounts", load_json_local(USER_ACCOUNTS_FILE, ACCOUNTS_LOCK_FILE))
st.session_state.setdefault("build_codes", load_json_local(BUILD_CODES_FILE, LOCK_FILE))
st.session_state.setdefault("user_rolls", load_json_local(USER_ROLLS_FILE, USER_LOCK_FILE))
st.session_state.setdefault("weapon_filters", {})
st.session_state.setdefault("armor_filters", {})
st.session_state.setdefault("helmet_filters", {})
st.session_state.setdefault("admin_authenticated", False)
st.session_state.setdefault("build_codes_authenticated", False)

# Load accounts from GitHub
if repo:
    accounts_from_github = load_user_accounts_github()
    st.session_state.user_accounts.update(accounts_from_github)

accounts = st.session_state.user_accounts

# ----------------------
# PERSISTENT LOGIN
# ----------------------
username_cookie = cookies.get("username")
if username_cookie and username_cookie in accounts:
    st.session_state.username = username_cookie
    st.session_state.user_authenticated = True

# ----------------------
# LOGIN / REGISTER
# ----------------------
if not st.session_state.user_authenticated:
    st.subheader("Login / Register")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    # --- LOGIN ---
    with login_tab:
        login_user = st.text_input("Username", key="login_user")
        login_pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login (Press Twice)"):
            if login_user in accounts and bcrypt.checkpw(login_pw.encode(), accounts[login_user].encode()):
                st.session_state.username = login_user
                st.session_state.user_authenticated = True
                cookies["username"] = login_user
                cookies.save()
                st.success(f"Welcome back, {login_user}!")
                st.stop()
            else:
                st.error("Incorrect username or password.")

    # --- REGISTER ---
    with register_tab:
        reg_user = st.text_input("Choose Username", key="reg_user")
        reg_pw = st.text_input("Choose Password (Uses password hashing to save password)", type="password", key="reg_pw")
        if st.button("Register (Press Twice to Login)"):
            if not reg_user or not reg_pw:
                st.error("Cannot leave username/password empty.")
            elif reg_user in accounts:
                st.error("Username already exists.")
            else:
                hashed_pw = bcrypt.hashpw(reg_pw.encode(), bcrypt.gensalt()).decode()
                accounts[reg_user] = hashed_pw
                save_json_local(USER_ACCOUNTS_FILE, ACCOUNTS_LOCK_FILE, accounts)
                save_user_accounts_github(accounts)
                st.session_state.username = reg_user
                st.session_state.user_authenticated = True
                cookies["username"] = reg_user
                cookies.save()
                st.success(f"Account created! Logged in as {reg_user}.")
                st.stop()

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
        "T191": "5.8x42mm", "TO3": "5.8x42mm", "AMB-17": "9x39mm",
        "SG550": "5.56x45mm", "G3": "7.62x51mm", "PCC-9": "9x19mm",
        "ZC-807": "7.62x39mm", "RPK-16": "5.45x39mm"
    },
    "SMGs": {
        "P90": "5.7x28mm", "MP5": "9x19mm", "MPX": "9x19mm",
        "Vector .45": ".45 ACP", "Vector 9": "9x19mm", "UMP45": ".45 ACP",
        "UZI": "9x19mm", "MAC-10": ".45 ACP", "MP40": "9x19mm",
        "T85": "7.62x25mm", "T79": "7.62x25mm", "QC61": "7.62x25mm",
        "MPF45": ".45 ACP", "M3A1": ".45 ACP", "PP-19": "9x19mm"
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
    "Sling Bag", "Lightweight Camping Backpack", "Medium Camping Backpack", "Simple Backpack",
    "Canvas Backpack", "Canvas Camping Backpack", "Sports Backpack", "Cowhide Backpack", "Outdoor Travel Backpack",
    "RUSH Tactical Backpack", "Large Camping Backpack", "XA4 Tactical Backpack", "Med Field Backpack",
    "Chapman Military Backpack", "AMP7 Assault Backpack", "Retro Marching Backpack", "LUC Expanded Tactical Backpack",
    "926 Field Backpack", "Field Camping Backpack", "RAL Heavy Military Backpack"
]

MAPS = ["Armory", "Farm", "Valley", "Airport", "Northridge", "TV Station"]

# Initialize filters
for tier in armors:
    st.session_state.armor_filters.setdefault(tier, True)
for tier in helmets:
    st.session_state.helmet_filters.setdefault(tier, True)
for cat in WEAPONS_DATA:
    st.session_state.weapon_filters.setdefault(cat, True)

# ----------------------
# RANDOMIZER FUNCTION
# ----------------------
def generate_loadout():
    import random

    loadout_lines = []

    # Step 1: Collect all enabled weapons
    all_enabled_weapons = []
    for category, enabled in st.session_state.weapon_filters.items():
        if enabled:
            all_enabled_weapons.extend(list(WEAPONS_DATA.get(category, {}).keys()))

    if all_enabled_weapons:
        # Step 2: Pick ONE random weapon
        weapon = random.choice(all_enabled_weapons)
        # Find ammo type
        ammo_type = None
        for cat, weapons in WEAPONS_DATA.items():
            if weapon in weapons:
                ammo_type = weapons[weapon]
                break
        # Step 3: Pick ammo
        ammo_options = ammo_data.get(ammo_type, [ammo_type])
        chosen_ammo = random.choice(ammo_options)
        loadout_lines.append(f"Weapon: {weapon}\n  Ammo: {chosen_ammo}")

    # Armor
    armor_tiers = [tier for tier, enabled in st.session_state.armor_filters.items() if enabled]
    if armor_tiers:
        armor_tier = random.choice(armor_tiers)
        armor_item = random.choice(armors[armor_tier])
        loadout_lines.append(f"Armor ({armor_tier}): {armor_item}")

    # Helmet
    helmet_tiers = [tier for tier, enabled in st.session_state.helmet_filters.items() if enabled]
    if helmet_tiers:
        helmet_tier = random.choice(helmet_tiers)
        helmet_item = random.choice(helmets[helmet_tier])
        loadout_lines.append(f"Helmet ({helmet_tier}): {helmet_item}")

    # Backpack
    backpack_item = random.choice(backpacks)
    loadout_lines.append(f"Backpack: {backpack_item}")

    # Map
    map_choice = random.choice(MAPS)
    loadout_lines.append(f"Map: {map_choice}")

    return "\n".join(loadout_lines)

# ----------------------
# TAB FUNCTIONS
# ----------------------
def randomizer_tab(tab):
    # Weapon categories
    tab.subheader("Weapon Categories")
    col1w, col2w = tab.columns(2)
    for i, cat in enumerate(sorted(WEAPONS_DATA.keys())):
        key = f"weapon_cb_{cat}"
        col = col1w if i % 2 == 0 else col2w
        col.checkbox(cat, value=st.session_state.weapon_filters.get(cat, True), key=key,
                     on_change=lambda c=cat: st.session_state.weapon_filters.update({c: st.session_state[f"weapon_cb_{c}"]}))
    # Armor
    tab.subheader("Armor Tiers")
    col1a, col2a = tab.columns(2)
    for i, tier in enumerate(sorted(armors.keys())):
        key = f"armor_cb_{tier}"
        col = col1a if i % 2 == 0 else col2a
        col.checkbox(tier, value=st.session_state.armor_filters.get(tier, True), key=key,
                     on_change=lambda t=tier: st.session_state.armor_filters.update({t: st.session_state[f"armor_cb_{t}"]}))
    # Helmet
    tab.subheader("Helmet Tiers")
    col1h, col2h = tab.columns(2)
    for i, tier in enumerate(sorted(helmets.keys())):
        key = f"helmet_cb_{tier}"
        col = col1h if i % 2 == 0 else col2h
        col.checkbox(tier, value=st.session_state.helmet_filters.get(tier, True), key=key,
                     on_change=lambda t=tier: st.session_state.helmet_filters.update({t: st.session_state[f"helmet_cb_{t}"]}))
    # Generate Loadout
    tab.header("Generate Loadout")
    if tab.button("Generate Loadout"):  # <-- Use tab.button, NOT st.button
        loadout = generate_loadout()
        tab.code(loadout)
    
        # Save user roll
        user = st.session_state.username
        st.session_state.user_rolls.setdefault(user, []).append(loadout)
    
        # Keep only last 10 rolls
        st.session_state.user_rolls[user] = st.session_state.user_rolls[user][-10:]
    
        # Save locally and to GitHub
        save_json_local(USER_ROLLS_FILE, USER_LOCK_FILE, st.session_state.user_rolls)
        save_user_rolls_github(st.session_state.user_rolls)

# ----------------------
# BUILD CODES TAB
# ----------------------
def add_build_code(weapon, new_code, username):
    new_code = new_code.strip()
    if not new_code or not username.strip():
        st.error("Username and code cannot be empty.")
        return
    latest_codes = load_build_codes_github() if repo else load_json_local(BUILD_CODES_FILE, LOCK_FILE)
    latest_codes.setdefault(weapon, [])
    st.session_state.build_codes.setdefault(weapon, [])
    existing_codes = [c["code"] for c in latest_codes[weapon] if isinstance(c, dict)]
    if new_code not in existing_codes:
        entry = {"code": new_code, "added_by": username, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        latest_codes[weapon].append(entry)
        st.session_state.build_codes[weapon] = latest_codes[weapon]
        save_json_local(BUILD_CODES_FILE, LOCK_FILE, latest_codes)
        save_build_codes_github(latest_codes)
        st.success(f"Added '{new_code}' to {weapon} by {username}")
    else:
        st.warning(f"Code '{new_code}' already exists for {weapon}")

# ----------------------
# BUILD CODES TAB
# ----------------------
def build_codes_tab(tab):
    tab.subheader("Build Codes Management")
    username = st.session_state.username

    # Password check (inside the tab)
    if not st.session_state.build_codes_authenticated:
        pw_input = tab.text_input("Enter password to edit build codes", type="password")
        if tab.button("Submit Password (Press Twice)"):
            if pw_input == BUILD_CODES_PASSWORD:
                st.session_state.build_codes_authenticated = True
                tab.success("Password correct! You can now edit build codes.")
            else:
                tab.error("Incorrect password")
        return  # Exit until password correct

    # Load codes
    st.session_state.build_codes = load_build_codes_github() if repo else load_json_local(BUILD_CODES_FILE, LOCK_FILE)

    # --- Weapon dropdown ---
    if st.session_state.build_codes:
        weapon_choice = tab.selectbox("Select Weapon to Add Code", sorted(st.session_state.build_codes.keys()))
    else:
        tab.info("No weapons available to add codes.")
        return

    # --- Add new code ---
    new_code = tab.text_input("Enter new build code")
    if tab.button("Add Code"):
        add_build_code(weapon_choice, new_code, username)

    # --- Show codes for selected weapon only ---
    tab.subheader("All Build Codes")
    
    # Flatten all codes with weapon names
    all_codes_with_weapon = []
    for weapon, codes in st.session_state.build_codes.items():
        for c in codes:
            code_str = c["code"] if isinstance(c, dict) else c
            all_codes_with_weapon.append(f"{weapon}: {code_str}")
    
    if all_codes_with_weapon:
        selected_code = tab.selectbox("Select a build code", all_codes_with_weapon, key="all_codes_dropdown")
        if selected_code:
            tab.markdown(f"**Selected Build Code:**\n```\n{selected_code}\n```")
    else:
        tab.info("No build codes available")

    # --- Small footer info ---
    tab.markdown(
        "<sub>[DM me](https://discord.com/users/650717003270848533) to remove a build code. "
        "If you get a yellow error when adding a build, press the button again.</sub>",
        unsafe_allow_html=True
    )

# ----------------------
# ADMIN PANEL TAB
# ----------------------
def admin_panel_tab(tab):
    tab.header("Admin Panel")

    if not st.session_state.admin_authenticated:
        admin_pw_input = tab.text_input("Enter Admin Password", type="password")
        if tab.button("Submit Admin Password", key="admin_submit"):
            if admin_pw_input == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                tab.success("Admin access granted!")
            else:
                tab.error("Incorrect password")
        return  # exit until authenticated

    # Load latest data
    if repo:
        st.session_state.build_codes = load_build_codes_github()
        st.session_state.user_rolls = load_user_rolls_github()
    else:
        st.session_state.build_codes = load_json_local(BUILD_CODES_FILE, LOCK_FILE)
        st.session_state.user_rolls = load_json_local(USER_ROLLS_FILE, USER_LOCK_FILE)

    # ----------------------
    # All Build Codes Table
    # ----------------------
    tab.subheader("All Build Codes")
    rows = []
    for weapon, codes in st.session_state.build_codes.items():
        for entry in codes:
            if isinstance(entry, dict):
                rows.append({
                    "Weapon": weapon,
                    "Code": entry.get("code"),
                    "Added By": entry.get("added_by"),
                    "Timestamp": entry.get("timestamp")
                })
    if rows:
        tab.dataframe(rows, use_container_width=True)
    else:
        tab.info("No build codes available.")

    # ----------------------
    # User Rolls Last 5 Dropdown
    # ----------------------
    tab.subheader("User Roll History (Select a User)")
    all_users = list(st.session_state.user_rolls.keys())
    if all_users:
        selected_user = tab.selectbox("Select User", all_users, key="admin_select_user")
        user_rolls = st.session_state.user_rolls.get(selected_user, [])
        if user_rolls:
            last_5 = list(reversed(user_rolls[-5:]))  # Last 5 rolls
            tab.markdown(f"**Last 5 Rolls for {selected_user}:**")
            for i, roll in enumerate(last_5, 1):
                tab.code(roll, language=None)  # <-- Use st.code instead of markdown with backticks
        else:
            tab.info(f"{selected_user} has no rolls yet.")
    else:
        tab.info("No users found.")

# ----------------------
# MAIN APP TABS
# ----------------------
if st.session_state.user_authenticated:
    st.sidebar.write(f"Logged in as: {st.session_state.username}")
    tabs_list = ["Randomizer", "Build Codes"]
    if st.session_state.username.lower() == "5ironman":
        tabs_list.append("Admin Panel")
    tabs = st.tabs(tabs_list)
    randomizer_tab(tabs[0])
    build_codes_tab(tabs[1])
    if "Admin Panel" in tabs_list:
        admin_panel_tab(tabs[2])




































