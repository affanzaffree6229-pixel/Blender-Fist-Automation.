"""
Fist Clench Rig — Universal Version
=====================================
Works on ANY armature regardless of bone naming conventions (MMD, Rigify, VRM, custom, etc.)

HOW IT WORKS
------------
Instead of hardcoded bone names, the script walks the children of whichever
bone you select as the "Hand" bone. Every child chain it finds is treated as
a finger, and rotation drivers are applied based on depth in the chain:
  - Depth 0 (Proximal)    → smaller curl
  - Depth 1 (Intermediate)→ medium curl
  - Depth 2+ (Distal+)    → tighter curl

HOW TO USE
----------
1. Select your Armature.
2. Enter Pose Mode and select the Hand/Wrist bone.
3. Open this script in Blender's Text Editor.
4. (Optional) Adjust ROTATION_BY_DEPTH below.
5. Press "Run Script".
"""

import bpy
import math

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

PROP_NAME = "Fist_Clench"

# Rotation angle (degrees) applied at Fist_Clench = 1, per chain depth level.
# depth 0 = first bone from hand (proximal), 1 = next (intermediate), etc.
# If a chain is longer than this list, the last value is reused.
# Negate all values if your rig curls the wrong direction.
ROTATION_BY_DEPTH = [
    70.0,   # proximal
    90.0,   # intermediate
    70.0,   # distal
    50.0,   # any extra bones beyond distal
]

# Which axis to rotate on. 0=X, 1=Y, 2=Z
ROTATION_AXIS = 0

# If True, skip finger chains that already have drivers on their bones.
# Set to False to overwrite/refresh existing drivers.
SKIP_IF_DRIVER_EXISTS = False

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def has_driver(arm_obj, bone_name, axis_index):
    anim = arm_obj.animation_data
    if not anim:
        return False
    path = f'pose.bones["{bone_name}"].rotation_euler'
    return anim.drivers.find(path, index=axis_index) is not None


def remove_driver(arm_obj, bone_name, axis_index):
    anim = arm_obj.animation_data
    if not anim:
        return
    path = f'pose.bones["{bone_name}"].rotation_euler'
    fc = anim.drivers.find(path, index=axis_index)
    if fc:
        anim.drivers.remove(fc)


def add_driver(arm_obj, pose_bone, hand_bone_name, prop_name, angle_deg, axis_index):
    """Attach a single driver to pose_bone's rotation_euler[axis_index]."""
    pose_bone.rotation_mode = 'XYZ'

    remove_driver(arm_obj, pose_bone.name, axis_index)

    fcurve = pose_bone.driver_add("rotation_euler", axis_index)
    drv = fcurve.driver
    drv.type = 'SCRIPTED'

    var = drv.variables.new()
    var.name = "clench"
    var.type = 'SINGLE_PROP'
    tgt = var.targets[0]
    tgt.id_type = 'OBJECT'
    tgt.id = arm_obj
    tgt.data_path = f'pose.bones["{hand_bone_name}"]["{prop_name}"]'

    angle_rad = math.radians(angle_deg)
    drv.expression = f"{angle_rad:.6f} * clench"

    for mod in fcurve.modifiers:
        fcurve.modifiers.remove(mod)


def get_angle_for_depth(depth):
    if depth < len(ROTATION_BY_DEPTH):
        return ROTATION_BY_DEPTH[depth]
    return ROTATION_BY_DEPTH[-1]


def walk_chain(arm_obj, root_bone, hand_bone_name, prop_name):
    """
    Walk a single finger chain starting from root_bone.
    root_bone is a direct child of the hand bone.
    Returns the number of bones driven.
    """
    driven = 0
    current = root_bone
    depth = 0

    while current:
        if SKIP_IF_DRIVER_EXISTS and has_driver(arm_obj, current.name, ROTATION_AXIS):
            print(f"      skipping (driver exists): {current.name}")
        else:
            angle = get_angle_for_depth(depth)
            add_driver(arm_obj, current, hand_bone_name, prop_name, angle, ROTATION_AXIS)
            print(f"      depth {depth} → {current.name}  ({angle}°)")
            driven += 1

        # Descend to first child only (single chain per finger)
        children = current.children
        current = children[0] if children else None
        depth += 1

    return driven


def add_custom_property(pose_bone, prop_name):
    pose_bone[prop_name] = 0.0
    ui = pose_bone.id_properties_ui(prop_name)
    ui.update(
        default=0.0,
        min=0.0, max=1.0,
        soft_min=0.0, soft_max=1.0,
        description="Curl all fingers into a fist (0 = open, 1 = closed)",
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  Fist Clench Rig — Universal Setup")
    print("=" * 60)

    # 1. Validate context
    arm_obj = bpy.context.active_object
    if arm_obj is None or arm_obj.type != 'ARMATURE':
        print("ERROR: Select an Armature object first.")
        return

    hand_bone = bpy.context.active_pose_bone
    if hand_bone is None:
        print("ERROR: Enter Pose Mode and select your Hand/Wrist bone first.")
        return

    print(f"\n  Armature : {arm_obj.name}")
    print(f"  Hand bone: {hand_bone.name}")

    # 2. Add custom property
    add_custom_property(hand_bone, PROP_NAME)
    print(f"\n  ✔ Custom property '{PROP_NAME}' added to '{hand_bone.name}'")

    # 3. Find finger chains (direct children of hand bone)
    finger_roots = hand_bone.children
    if not finger_roots:
        print(f"\n  WARNING: '{hand_bone.name}' has no children — no fingers found.")
        print("  Make sure you selected the correct hand/wrist bone.")
        return

    print(f"\n  Found {len(finger_roots)} finger chain(s) from '{hand_bone.name}':")

    total_driven = 0
    for i, root in enumerate(finger_roots):
        print(f"\n    Finger {i + 1}: starting from '{root.name}'")
        driven = walk_chain(arm_obj, root, hand_bone.name, PROP_NAME)
        total_driven += driven

    # 4. Refresh
    bpy.context.view_layer.update()

    print(f"\n{'=' * 60}")
    print(f"  ✔ Done! {total_driven} bone(s) driven across {len(finger_roots)} finger(s).")
    print(f"\n  → Select '{hand_bone.name}' in Pose Mode")
    print(f"  → N-panel > Item > Custom Properties")
    print(f"  → Slide '{PROP_NAME}' from 0 → 1")
    print("=" * 60 + "\n")


main()
