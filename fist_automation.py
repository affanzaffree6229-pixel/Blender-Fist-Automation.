import bpy

class VIEW3D_PT_fist_controller(bpy.types.Panel):
    bl_label = "Fist Controller"
    bl_idname = "VIEW3D_PT_fist_controller"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Fist'

    def draw(self, context):
        layout = self.layout
        bone = context.active_pose_bone
        if bone and "Fist" in bone:
            layout.prop(bone, '["Fist"]', slider=True, text="Fist Clench")
        else:
            layout.label(text="Select Hand Bone", icon='BONE_DATA')

def setup_fist_drivers():
    obj = bpy.context.active_object
    hand_bone = bpy.context.active_pose_bone

    if not hand_bone or obj.type != 'ARMATURE':
        return

    if "Fist" not in hand_bone:
        hand_bone["Fist"] = 0.0
        hand_bone.id_properties_ui("Fist").update(min=0.0, max=1.0)
    
    for finger_base in hand_bone.children:
        current_bone = finger_base
        while current_bone:
            current_bone.rotation_mode = 'XYZ'
            fcurve = current_bone.driver_add("rotation_euler", 0) 
            drv = fcurve.driver
            drv.type = 'AVERAGE'
            
            var = drv.variables.new()
            var.name = "fist_val"
            var.type = 'SINGLE_PROP'
            var.targets[0].id = obj
            var.targets[0].data_path = f'pose.bones["{hand_bone.name}"]["Fist"]'
            
            # This is the "Flat on Palm" math
            if "Thumb" in current_bone.name:
                drv.expression = "fist_val * 1.5"
            else:
                drv.expression = "fist_val * 2.5"
            
            # Get the next bone in the chain
            if len(current_bone.children) > 0:
                current_bone = current_bone.children[0]
            else:
                current_bone = None

try:
    bpy.utils.register_class(VIEW3D_PT_fist_controller)
except:
    pass

setup_fist_drivers()
