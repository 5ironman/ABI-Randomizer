import streamlit as st
import random
import json
import os

# Module-level build codes so the GUI can view and edit them
build_codes = {
    "HK416": ["HK416-4634634", "HK416-8273645"],
    "M4A1": ["M4A1-4634634", "M4A1-9923410"],
}

BUILD_CODES_FILE = "build_codes.json"

def load_build_codes():
    global build_codes
    if os.path.exists(BUILD_CODES_FILE):
        try:
            with open(BUILD_CODES_FILE, "r") as f:
                build_codes = json.load(f)
        except:
            pass

def save_build_codes():
    with open(BUILD_CODES_FILE, "w") as f:
        json.dump(build_codes, f, indent=4)

# Full weapons data moved to module-level so other parts of the program can reuse it
WEAPONS_DATA = {
    "Assault Rifles": {
        "HK416": "5.56x45mm", "M4A1": "5.56x45mm", "AK-102": "5.56x45mm",
        "FAL": "7.62x51mm", "SCAR-L": "5.56x45mm", "AEK": "7.62x39mm",
        "AK-74N": "5.45x39mm", "AKM": "7.62x39mm", "F2000": "5.56x45mm",
        "ACE31": "7.62x39mm", "AR-57": "5.7x28mm", "AN-94": "5.45x39mm",
        "AUG": "5.56x45mm", "MDR": "5.56x45mm", "AKS-74U": "5.45x39mm",
        "T951": "5.8x42mm", "AK-12": "5.45x39mm", "MCX": "5.56x45mm",
        "T191": "5.8x42mm", "TO3": "5.8x42mm", "AMB-17": "9x39mm", "SG550": "5.56x45mm", "G3": "7.62x51mm", "PCC-9": "9x19mm", "ZC-807": "7.62x39mm", "RPK-16": "5.45x39mm"
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
        "Mosin-Nagant": "7.62x54mm", "M24": "7.62x51mm", "SJ16": ".338 Lapua",
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

# Ensure every weapon has an entry in build_codes (possibly empty)
for cat in WEAPONS_DATA.values():
    for weapon_name in cat.keys():
        if weapon_name not in build_codes:
            build_codes[weapon_name] = []
def generate_full_abi_loadout(lockdown=False, disable_shot_pistol=False, exclude_t1_t2=False, armored_rig_chance=0.25):
    weapons_data = WEAPONS_DATA


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
    "Tier 1": [
        "Retro Sapper Bulletproof Vest",
        "Retro Bulletproof Vest",
        "Old Security Body Armor"
    ],
    "Tier 2": [
        "Security Body Armor",
        "220 Body Armor",
        "Retro Infantry Bulletproof Vest"
    ],
    "Tier 3": [
        "KN Regulation Body Armor",
        "PCA350 Body Armor",
        "Standard SWAT Armor",
        "H-Tac SWAT Body Armor",
        "KN Assault Body Armor",
        "H-LC Lightweight Body Armor"
    ],
    "Tier 4": [
        "SEK Fortress Body Armor",
        "IND401 Body Armor",
        "6B13 Body Armor",
        "6B23 Body Armor",
        "Spartan B Body Armor"
    ],
    "Tier 5": [
        "H-LC Tactical Body Armor",
        "Defender M4 Heavy Body Armor (Black)",
        "Defender M4 Heavy Body Armor (Green)",
        "926 Composite Body Armor",
        "IMTV Samurai Assault Armor",
        "IMTV Samurai Standard Armor",
        "IMTV Samurai Full Protection",
        "BT6 Heavy Body Armor"
    ],
    "Tier 6": [
        "Marshal Heavy Body Armor",
        "6B45 Heavy Body Armor",
        "BT101 Tactical Body Armor",
        "KN Composite Body Armor"
    ]
}
    
    armored_rigs = {
    "Tier 2": [
        "M1955 Combat Vest"
    ],
    "Tier 3": [
        "6B5 Armored Rig",
        "Sentry 3 Armored Chest",
        "926 Security Armored Rig"
    ],
    "Tier 4": [
        "Sentry 305 Armored Rig",
        "TM1 Armored Rig",
        "TM2 Armored Rig"
    ],
    "Tier 5": [
        "H-Tac A8 Armored Rig",
        "Warrior Heavy Armored Rig",
        "H-Tac A9 Armored Rig",
        "Defender M4 Heavy Armored Rig"
    ],
    "Tier 6": [
        "Spartan C Heavy Armored Rig",
        "AL Tactical Armored Rig",
        "AVS Heavy Armored Rig",
        "AL Commander Armored Rig",
        "AL Assault Armored Rig"
    ]
}

    # build_codes moved to module-level so GUI can view/edit them

    helmets = {
    "Tier 1": [
        "Kelsey Fire Helmet",
        "Lightweight Safety Helmet",
        "Motorcycle Helmet",
        "Tanker Protective Cap"
    ],
    "Tier 2": [
        "Retro Military Helmet",
        "Retro Steel Helmet",
        "Security Helmet",
        "Aviator Helmet",
        "Security Riot Helmet",
        "PAS Standard Helmet"
    ],
    "Tier 3": [
        "PAS2 Helmet",
        "F70 Tactical Helmet",
        "SH12 Military Helmet",
        "6B4 Helmet",
        "6B4 Helmet (Squad S)",
        "6B5 Helmet"
    ],
    "Tier 4": [
        "SH40 Military Helmet",
        "IND Tactical Helmet",
        "IND Tactical Helmet (Variant)",
        "IND200 Helmet",
        "F80 Tactical Helmet",
        "SH18 Military Helmet",
        "KSS Tactical Helmet",
        "KSS2 Tactical Helmet",
        "56K Helicopter Helmet"
    ],
    "Tier 5": [
        "SH Matzka 2 Helmet",
        "SH60 Military Helmet",
        "SH50 Military Helmet",
        "FA Assault Tactical Helmet",
        "03 Heavy Tactical Helmet",
        "RSP Heavy Tactical Helmet",
        "AN95 Heavy Blast Helmet"
    ],
    "Tier 6": [
        "6BNT Helmet",
        "RST Special Forces Helmet",
        "HGB4 Offensive Helmet",
        "SH65 Military Helmet",
        "IND50 Heavy Tactical Helmet",
        "D009 Blast Helmet",
        "AS200 Heavy Tactical Helmet"
    ]
    }
    Backpacks ={
    "Sling Bag",
    "Lightweight Camping Backpack",
    "Medium Camping Backpack",
    "Simple Backpack",
    "Canvas Backpack",
    "Canvas Camping Backpack",
    "Sports Backpack",
    "Cowhide Backpack",
    "Outdoor Travel Backpack",
    "RUSH Tactical Backpack",
    "Large Camping Backpack",
    "XA4 Tactical Backpack",
    "Med Field Backpack",
    "Chapman Military Backpack",
    "AMP7 Assault Backpack",
    "Retro Marching Backpack",
    "LUC Expanded Tactical Backpack",
    "926 Field Backpack",
    "Field Camping Backpack",
    "RAL Heavy Military Backpack"
}

    available_categories = list(weapons_data.keys())
    if disable_shot_pistol:
        available_categories = [c for c in available_categories if c not in ("Shotguns", "Pistols", "Carbines")]
    if not available_categories:
        available_categories = list(weapons_data.keys())
    category = random.choice(available_categories)
    weapon, caliber = random.choice(list(weapons_data[category].items()))

    if caliber in ammo_data:
        ammo_choice = random.choice(ammo_data[caliber])
        ammo_display = f"{caliber} {ammo_choice}"
    else:
        ammo_display = f"{caliber} (Standard Loadout)"

    armor_tiers = list(armors.keys())
    helmet_tiers = list(helmets.keys())
    if lockdown:
        armor_tiers = [t for t in armor_tiers if t != "Tier 6"]
        helmet_tiers = [t for t in helmet_tiers if t != "Tier 6"]
    if exclude_t1_t2:
        armor_tiers = [t for t in armor_tiers if t not in ("Tier 1", "Tier 2")]
        helmet_tiers = [t for t in helmet_tiers if t not in ("Tier 1", "Tier 2")]
    if not armor_tiers:
        armor_tiers = list(armors.keys())
    if not helmet_tiers:
        helmet_tiers = list(helmets.keys())

    armor_tier = random.choice(armor_tiers)
    # Roll to determine whether to spawn an armored rig instead of normal armor
    use_armored_rig = random.random() < armored_rig_chance and armor_tier in armored_rigs and armored_rigs[armor_tier]
    if use_armored_rig:
        armor_piece = random.choice(armored_rigs[armor_tier])
        armor_is_rig = True
    else:
        armor_piece = random.choice(armors[armor_tier])
        armor_is_rig = False

    helmet_tier = random.choice(helmet_tiers)
    helmet_piece = random.choice(helmets[helmet_tier])

    # Select a random backpack from the available backpacks
    backpack_choice = random.choice(list(Backpacks))

    build_code_choice = None
    if weapon in build_codes:
        codes = build_codes[weapon]
        if isinstance(codes, list):
            if codes:
                build_code_choice = random.choice(codes)
            else:
                build_code_choice = None
        else:
            build_code_choice = codes

    out_lines = []
    out_lines.append("--- ARENA BREAKOUT: INFINITE RANDOM LOADOUT ---")
    out_lines.append(f"CLASS:    {category}")
    out_lines.append(f"WEAPON:   {weapon}")
    out_lines.append(f"AMMO:     {ammo_display}")
    if build_code_choice:
        out_lines.append(f"BUILD CODE: {build_code_choice}")
    if armor_is_rig:
        out_lines.append(f"ARMORED RIG:      {armor_piece} ({armor_tier})")
    else:
        out_lines.append(f"ARMOR:    {armor_piece} ({armor_tier})")
    out_lines.append(f"HELMET:   {helmet_piece} ({helmet_tier})")
    maps = ["Airport", "Farm", "Valley", "TV", "Northridge", "Armory"]
    out_lines.append(f"BACKPACK: {backpack_choice}")
    selected_map = random.choice(maps)
    out_lines.append(f"MAP:      {selected_map}")
    out_lines.append("-----------------------------------------------")

    output_str = "\n".join(out_lines)
    print(output_str)
    return output_str

load_build_codes()

st.title("ABI Randomizer")

col1, col2, col3 = st.columns(3)

with col1:
    lockdown = st.checkbox("Lockdown (exclude Tier 6)")

with col2:
    disable_shot_pistol = st.checkbox("Disable Shotguns, Pistols & Carbines")

with col3:
    exclude_t12 = st.checkbox("Exclude Tier 1 & 2 Armor/Helmets")

if st.button("Generate Loadout"):
    result = generate_full_abi_loadout(
        lockdown=lockdown,
        disable_shot_pistol=disable_shot_pistol,
        exclude_t1_t2=exclude_t12
    )
    st.code(result)

st.header("Edit Build Codes")

weapon_choice = st.selectbox("Select Weapon", list(build_codes.keys()))
new_code = st.text_input("Enter New Build Code")

if st.button("Add Build Code"):
    if new_code:
        build_codes[weapon_choice].append(new_code)
        save_build_codes()  # <-- save changes immediately
        st.success(f"Added build code {new_code} to {weapon_choice}")

st.subheader("Current Build Codes")
st.json(build_codes)