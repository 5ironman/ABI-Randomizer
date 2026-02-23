import streamlit as st
import json
import random
import os
from github import Github, Auth
from github.GithubException import UnknownObjectException
from filelock import FileLock
from datetime import datetime

# ----------------------
# CONFIG
# ----------------------
BUILD_CODES_FILE = "build_codes.json"
USER_ROLLS_FILE = "user_rolls.json"
LOCK_FILE = BUILD_CODES_FILE + ".lock"
USER_LOCK_FILE = USER_ROLLS_FILE + ".lock"
BUILD_CODES_PASSWORD = "ABI-RANDOM123"
ADMIN_PASSWORD = "5ironman17admin"

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
# LOAD / SAVE FUNCTIONS
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

# ----------------------
# SESSION STATE INIT
# ----------------------
st.session_state.setdefault("build_codes", load_build_codes_github() if repo else load_json_local(BUILD_CODES_FILE, LOCK_FILE))
st.session_state.setdefault("weapon_filters", {})
st.session_state.setdefault("armor_filters", {})
st.session_state.setdefault("helmet_filters", {})
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("admin_authenticated", False)
st.session_state.setdefault("username", "")
st.session_state.setdefault("user_rolls", load_user_rolls_github() if repo else load_json_local(USER_ROLLS_FILE, USER_LOCK_FILE))

# ----------------------
# GLOBAL USERNAME ENFORCEMENT (UPDATED, NO DEPRECATED FUNCTIONS)
# ----------------------
if not st.session_state.username.strip():
    st.warning("You must enter a username to access any part of the site.")

    # Use a form to enter username
    with st.form("username_form"):
        username_input = st.text_input("Enter your username to continue:")
        submitted = st.form_submit_button("Submit")

    if submitted:
        username_input = username_input.strip()
        if username_input:
            st.session_state.username = username_input
            st.success(f"Welcome, {username_input}!")
        else:
            st.error("Username cannot be empty.")

    # Stop execution until username is provided
    if not st.session_state.username.strip():
        st.stop()

# ----------------------
# DATA
# ----------------------
WEAPONS_DATA = {
    "Assault Rifles": {"HK416": "5.56x45mm", "M4A1": "5.56x45mm", "AK-102": "5.56x45mm"},
    "SMGs": {"P90": "5.7x28mm", "MP5": "9x19mm"},
    "Carbines": {"SKS": "7.62x39mm", "M16": "5.56x45mm"},
    "Marksman Rifles": {"M110": "7.62x51mm", "SVDS": "7.62x54mm"},
    "Sniper Rifles": {"Mosin-Nagant": "7.62x54mm", "M24": "7.62x51mm"},
    "Shotguns": {"S12K": "12x70mm", "M870": "12x70mm"},
    "Pistols": {"G18C": "9x19mm", "G17": "9x19mm"}
}

ammo_data = {
    "5.56x45mm": ["M193", "M855", "M995"],
    "5.7x28mm": ["SS197SR", "SS190"],
    "7.62x39mm": ["HP", "BP"],
    "7.62x51mm": ["M80", "M62"],
    "7.62x54mm": ["SNB", "7N37"],
    "9x19mm": ["PSO", "PST"],
    "12x70mm": ["Type 5 buckshot", "Type 7 buckshot"]
}

armors = {"Tier 1": ["Retro Sapper"], "Tier 2": ["Security Body Armor"]}
helmets = {"Tier 1": ["Kelsey Fire Helmet"], "Tier 2": ["Retro Military Helmet"]}
backpacks = ["Sling Bag", "Lightweight Camping Backpack"]

# Ensure all weapons have a build code list
for cat in WEAPONS_DATA.values():
    st.session_state.build_codes.update({w: [] for w in cat if w not in st.session_state.build_codes})

# Initialize filters
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
    code = random.choice([c["code"] for c in codes if isinstance(c, dict)]) if codes else None
    lines = [f"CLASS: {cat}", f"WEAPON: {weapon}", f"AMMO: {ammo}"]
    if code:
        lines.append(f"BUILD CODE: {code}")
    lines += [f"ARMOR: {armor_piece}", f"HELMET: {helmet_piece}", f"BACKPACK: {backpack}"]
    return "\n".join(lines)

# ----------------------
# BUILD CODE MANAGEMENT
# ----------------------
def add_build_code(weapon, new_code, username):
    new_code = new_code.strip()
    if not new_code:
        return
    if not username.strip():
        st.error("You must enter a username before adding a build code.")
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
# STREAMLIT UI WITH TABS
# ----------------------
tab1, tab2, tab3 = st.tabs(["Randomizer", "Build Codes", "Admin Panel"])

# ---------------------- RANDOMIZER TAB ----------------------
with tab1:
    st.subheader("Weapon Categories")
    for cat in WEAPONS_DATA:
        st.session_state.weapon_filters[cat] = st.checkbox(cat, value=st.session_state.weapon_filters[cat], key=f"weapon_{cat}")
    st.subheader("Armor Tiers")
    for tier in armors:
        st.session_state.armor_filters[tier] = st.checkbox(tier, value=st.session_state.armor_filters[tier], key=f"armor_{tier}")
    st.subheader("Helmet Tiers")
    for tier in helmets:
        st.session_state.helmet_filters[tier] = st.checkbox(tier, value=st.session_state.helmet_filters[tier], key=f"helmet_{tier}")

    st.header("Generate Loadout")
    if st.button("Generate Loadout"):
        loadout = generate_loadout()
        st.code(loadout)
        user = st.session_state.username
        st.session_state.user_rolls = load_user_rolls_github() if repo else load_json_local(USER_ROLLS_FILE, USER_LOCK_FILE)
        st.session_state.user_rolls.setdefault(user, []).append(loadout)
        save_json_local(USER_ROLLS_FILE, USER_LOCK_FILE, st.session_state.user_rolls)
        save_user_rolls_github(st.session_state.user_rolls)

# ---------------------- BUILD CODES TAB ----------------------
with tab2:
    st.subheader("Build Codes Management")
    username = st.session_state.username
    
    if not st.session_state.authenticated:
        pw = st.text_input("Enter password to edit build codes", type="password")
        if st.button("Submit Password"):
            if pw == BUILD_CODES_PASSWORD:
                st.session_state.authenticated = True
                st.success("Password correct!")
            else:
                st.error("Incorrect password")
    else:
        st.session_state.build_codes = load_build_codes_github() if repo else load_json_local(BUILD_CODES_FILE, LOCK_FILE)
        weapon_choice = st.selectbox("Select Weapon to Add Code", sorted(st.session_state.build_codes.keys()))
        new_code = st.text_input("Enter new build code")
        if st.button("Add Code"):
            add_build_code(weapon_choice, new_code, username)
        
        with st.expander("All Build Codes"):
            for weapon, codes in sorted(st.session_state.build_codes.items()):
                st.markdown(f"**{weapon}**")
                if codes:
                    for c in codes:
                        if isinstance(c, dict):
                            st.markdown(f"- {c['code']} (added by {c['added_by']} on {c['timestamp']})")
                        else:
                            st.markdown(f"- {c}")
                else:
                    st.markdown("- No codes yet")

# ---------------------- ADMIN PANEL TAB ----------------------
with tab3:
    if not st.session_state.admin_authenticated:
        admin_pw = st.text_input("Enter Admin Password", type="password")
        if admin_pw == ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            st.success("Admin access granted!")
        elif admin_pw != "":
            st.error("Incorrect password")

    if st.session_state.admin_authenticated:
        st.session_state.build_codes = load_build_codes_github() if repo else load_json_local(BUILD_CODES_FILE, LOCK_FILE)
        st.session_state.user_rolls = load_user_rolls_github() if repo else load_json_local(USER_ROLLS_FILE, USER_LOCK_FILE)

        # Show build codes
        with st.expander("All Weapon Build Codes"):
            for weapon, codes in sorted(st.session_state.build_codes.items()):
                st.markdown(f"**{weapon}**")
                if codes:
                    for c in codes:
                        if isinstance(c, dict):
                            st.markdown(f"- {c['code']} (added by {c['added_by']} on {c['timestamp']})")
                        else:
                            st.markdown(f"- {c}")
                else:
                    st.markdown("- No codes yet")

        # Show user roll history
        with st.expander("User Roll History"):
            search_query = st.text_input("Search Users")
            for user, rolls in st.session_state.user_rolls.items():
                if search_query.lower() in user.lower():
                    st.markdown(f"**{user}** ({len(rolls)} rolls)")
                    for r in rolls[-5:]:
                        st.markdown(f"- {r}")


