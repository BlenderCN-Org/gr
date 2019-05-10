# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any laTter version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


##########################################################################################################
##########################################################################################################

import bpy
from bpy.types import Panel, Operator, AddonPreferences
from bpy.props import *
from mathutils import Matrix, Vector, Euler
from math import sqrt, pi, radians
from mathutils.bvhtree import BVHTree


def vis_point(loc):
    v = bpy.data.objects.new('fwd', None)
    v.empty_display_size = .2
    v.location = loc
    bpy.context.scene.collection.objects.link(v)


def popup (lines, icon, title):
    def draw(self, context):
        for line in lines:
            self.layout.label(line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    

def report (self, item, error_or_info):
    self.report({error_or_info}, item)
    

def mean (A, B):
    mp = ( A + B ) / 2
    return mp


def get_distance (A, B):
    return sqrt(((B[0]-A[0])**2)+((B[1]-A[1])**2)+((B[2]-A[2])**2))


def link_collection (collection_name, path):
    # path to the blend
    filepath = path
    # link or append
    link = True
    
    with bpy.data.libraries.load (filepath, link=link) as (data_from, data_to):
        data_to.collections = [name for name in data_from.collections if name.endswith (collection_name)]
                   

def set_cursor_location (location):
    bpy.context.scene.cursor.location = location

def set_pivot_mode (mode):
    bpy.context.scene.tool_settings.transform_pivot_point = mode
    
def set_transform_orientation (mode):
    bpy.context.scene.transform_orientation_slots[0].type = mode
    

##############################################################
# THESE WORK IN ARMATURE SSSEDIT MODE
##############################################################

def translate_ebone_local(ebone, vector):
    
    mat = ebone.matrix
    mat.invert()

    vec = Vector(vector) @ mat

    ebone.head += vec
    ebone.tail += vec   


def bone_radius_check_points(ebone, num, dist):

    mat = ebone.matrix
    mat.invert()
    
    results = []
     
    for n in range(num):
        v = Vector ((0, 0, dist))
        rot_mat = Matrix.Rotation(radians((360 / num) * n), 4, 'Y') @ mat
        v = v @ rot_mat
        v += (ebone.head + ebone.tail) * 0.5
        
        results.append(v)

    return results


# angle: degrees, axis: 'X', 'Y', 'Z'
def rotate_ebone_local(ebone, angle, axis):
    
    saved_roll = ebone.roll
    saved_pos = ebone.head.copy()
    
    mat = ebone.matrix
    eul = mat.to_euler()
    eul.rotate_axis(axis, radians(angle))
    mat = eul.to_matrix().to_4x4()
    mat.translation = saved_pos[0], saved_pos[1], saved_pos[2]
    ebone.matrix = mat
    
    ebone.roll = saved_roll


##############################################################
##############################################################

class Op_GYAZ_GameRig_GenerateRig (bpy.types.Operator):
       
    bl_idname = "object.gyaz_game_rigger_generate_rig"  
    bl_label = "GYAZ Game Rigger: Generate Rig"
    bl_description = ""
    
    generate__facial_rig: EnumProperty (
    name='Facial Rig',
    items=(
        ('NONE', 'NONE', ''),
        ('EYES', 'EYES', ''),
        ('EYES+JAW', 'EYES+JAW', ''),
        ('FULL', 'FULL', '')
        ),
    default='FULL')

    generate__fingers: BoolProperty (default=True, name='Fingers')
    
    generate__spring_belly: BoolProperty (default=True, name='Spring Belly')
    
    generate__spring_bottom: BoolProperty (default=True, name='Spring Bottom')
    
    generate__spring_chest: BoolProperty (default=True, name='Spring Chest')
    
    generate__twist_upperarm_count: EnumProperty (name='Twist Upperarm', items=(('0', '0', ''), ('1', '1', ''), ('2', '2', ''), ('3', '3', '')), default='3')
        
    generate__twist_forearm_count: EnumProperty (name='Twist Forearm', items=(('0', '0', ''), ('1', '1', ''), ('2', '2', ''), ('3', '3', '')), default='3')
        
    generate__twist_thigh_count: EnumProperty (name='Twist Thigh', items=(('0', '0', ''), ('1', '1', ''), ('2', '2', ''), ('3', '3', '')), default='3')
        
    generate__twist_shin_count: EnumProperty (name='Twist Shin', items=(('0', '0', ''), ('1', '1', ''), ('2', '2', ''), ('3', '3', '')), default='1')    
        
    generate__twist_neck: BoolProperty (default=True, name='Twist Neck')
    
    def draw (self, context):
        lay = self.layout
        lay.prop (self, 'generate__fingers')
        lay.label (text='Twist Bones:')
        row = lay.row (align=True)
        row.label (text='Upperarm:')
        row.prop (self, 'generate__twist_upperarm_count', expand=True)
        row = lay.row (align=True)
        row.label (text='Forearm:')
        row.prop (self, 'generate__twist_forearm_count', expand=True)
        row = lay.row (align=True)
        row.label (text='Thigh:')
        row.prop (self, 'generate__twist_thigh_count', expand=True)
        row = lay.row (align=True)
        row.label (text='Shin:')
        row.prop (self, 'generate__twist_shin_count', expand=True)
        lay.prop (self, 'generate__twist_neck')
        lay.label (text='Spring Bones:')
        lay.prop (self, 'generate__spring_belly')
        lay.prop (self, 'generate__spring_bottom')
        lay.prop (self, 'generate__spring_chest')
        lay.label (text='Facial Rig:')
        lay.prop (self, 'generate__facial_rig', expand=True)
        lay.separator ()
    
    def invoke (self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    #operator function
    def execute(self, context):
        
        def main ():
            
            generate__facial_rig = self.generate__facial_rig
            
            if generate__facial_rig == 'NONE':
                generate__face_eyes = False
                generate__face_jaw = False
                generate__face_detail = False
                
            elif generate__facial_rig == 'EYES':
                generate__face_eyes = True
                generate__face_jaw = False
                generate__face_detail = False
                
            elif generate__facial_rig == 'EYES+JAW':
                generate__face_eyes = True
                generate__face_jaw = True
                generate__face_detail = False
                
            elif generate__facial_rig == 'FULL':
                generate__face_eyes = True
                generate__face_jaw = True
                generate__face_detail = True
                
            generate__fingers = self.generate__fingers
            generate__spring_belly = self.generate__spring_belly
            generate__spring_bottom = self.generate__spring_bottom
            generate__spring_chest = self.generate__spring_chest
            generate__twist_upperarm_count = int( self.generate__twist_upperarm_count)
            generate__twist_forearm_count = int( self.generate__twist_forearm_count)
            generate__twist_thigh_count = int( self.generate__twist_thigh_count)
            generate__twist_shin_count = int( self.generate__twist_shin_count)
            generate__twist_neck = self.generate__twist_neck
            

            #MUST HAVE AT LEAST ONE MESH PARENTED TO THE SKELETON

            #SETTINGS-SETTINGS-SETTINGS-SETTINGS:
            auto_bone_shape_scale_offset = 0.05
            auto_bone_shape_scale_offset_limb = 0.02
            target_shape_size = 0.05
            general_bone_size = 0.05
            pole_target_distance = 0.5
            finger_shape_size = 0.01
            face_shape_size = 0.005
            look_target_size = face_shape_size * 5
            look_target_offset = 0.5
            chest_target_distance = 1
            chest_target_size = 0.25
            
            import os
            source_path = os.path.dirname(__file__) + "/source_shapes.blend"


            #BIPED:
            #root
            root_size = 0.25
            root_extract_size = 0.15

            #TWIST BONES:
            neck_twist_rotate_back = 0.5
            neck_twist_min_y = -20
            neck_twist_track_to_head = 1

            twist_target_distance = -0.4

            #upperarm
            upperarm_twists = [
            [0.75],
            [0.75, 0.5],
            [0.75, 0.5, 0.25]
            ]

            #forearm
            forearm_twists = [
            [1],
            [1, 0.5],
            [1, 0.5, 0.25]
            ]

            #thigh
            thigh_twists = [
            [0.75],
            [0.75, 0.5],
            [0.75, 0.5, 0.25]
            ]

            #shin
            shin_twists = [
            [0.75],
            [1, 0.5],
            [1, 0.5, 0.25]
            ]

            #SPRING BONES (left):
            spring_bottom__thigh_bend_fwd_to_scale__thigh_rot = 45
            spring_bottom__thigh_bend_fwd_to_scale__scale = 1.4
            spring_bottom__thigh_bend_fwd_to_rot__thigh_rot = 90
            spring_bottom__thigh_bend_fwd_to_rot__rot = 60

            spring_bottom__thigh_bend_bwd_to_scale__thigh_rot = -30
            spring_bottom__thigh_bend_bwd_to_scale__scale = 1.4
            spring_bottom__thigh_bend_bwd_to_rot__thigh_rot = -30
            spring_bottom__thigh_bend_bwd_to_rot__rot = -10

            spring_belly__waist_lower_rot_to_scale__waist_lower_rot = 30
            spring_belly__waist_lower_rot_to_scale__scale = 2

            spring_chest__shoulder_up__shoulder_rot = 60
            spring_chest__shoulder_up__rot = 30
            spring_chest__shoulder_down__shoulder_rot = -20
            spring_chest__shoulder_down__rot = -5

            #FACIAL BONES
            teeth_lower_copy_jaw_rot = 0.7
            lowerlip_copy_jaw_rot = 0.5
            upperlid_copy_eye_rot = 0.25
            lowerlid_copy_eye_rot = 0.1

            #CTRL FINGERS (left):
            ctrl_finger_scale__to_finger_2_3_bend_fwd__scale = 0.5
            ctrl_finger_scale__to_finger_2_3_bend_fwd__rot = -90
            ctrl_finger_scale__to_finger_2_3_bend_bwd__scale = 1.25
            ctrl_finger_scale__to_finger_2_3_bend_bwd__rot = 10

            ctrl_finger_scale__to_thumb_2_bend_fwd__rot = -75
            ctrl_finger_scale__to_thumb_2_bend_bwd__rot = 30

            #CTRL SPINE
            ctrl_waist__copy__ctrl_chest = 1.0
            ctrl_waist__copy__ctrl_hips = 0.6

            ik_spine_2__copy__ctrl_waist = 0.6
            ik_spine_2__copy__ctrl_waist = 0.5

            fixate_ctrl_neck = 0.3
            fixate_ctrl_head = 0.5

            #MISC
            sides = ['_l', '_r']
            fk_prefix = 'fk_'
            ik_prefix = 'ik_'

            #LAYERS
            #game bones
            base_layer = 0
            twist_layer = 1
            spring_layer = 2
            fix_layer = 3
            face_layer = 4
            face_extra_layer = 5
            ik_prop_layer = 6

            root_layer = 16

            misc_layer = 24
            twist_target_layer = 25
            fk_extra_layer = 26
            ctrl_ik_extra_layer = 27
            module_prop_layer = 28

            fk_layer = 8
            ctrl_ik_layer = 9
            touch_layer = 10
            
            target_layer = 11

            #GROUPS
            base_group = 'base'
            fk_group = 'fk'
            central_ik_group = 'ik_c'
            left_ik_group = 'ik_l'
            right_ik_group = 'ik_r'
            twist_group = 'twist'
            spring_group = 'spring'
            ik_prop_group = 'ik_prop'
            face_group = 'face'
            target_group = 'target'

            #inactive
            #extra_root_layer = 17
            #ik_foot_root_size = 0.3
            #ik_hand_root_size = 0.45

            #END OF SETTINGS
            
            ########################################################################################################
            ########################################################################################################


            scene = bpy.context.scene
            rig = bpy.context.object


            def cast_ray_from_bone (start_bone, head_tail, ebone_pbone, direction, distance):        
                #set ray start and direction
                if ebone_pbone == 'ebone':    
                    bpy.ops.object.mode_set (mode='EDIT')
                    if head_tail == 'head':
                        ray_start = rig.data.edit_bones[start_bone].head
                    elif head_tail == 'tail':
                        ray_start = rig.data.edit_bones[start_bone].tail
                elif ebone_pbone == 'pbone':
                    bpy.ops.object.mode_set (mode='POSE')
                    if head_tail == 'head':
                        ray_start = rig.pose.bones[start_bone].head
                    elif head_tail == 'tail':
                        ray_start = rig.pose.bones[start_bone].tail
                ray_direction = direction
                ray_distance = 10
                
                #cast ray
                hit_loc, hit_nor, hit_index, hit_dist = my_tree.ray_cast (ray_start, ray_direction, ray_distance)
                
                return (hit_loc, hit_nor, hit_index, hit_dist)


            ########################################################################################################
            ########################################################################################################

            def set_bone_only_layer (bone_name, layer_index):
                
                #create layers tuple
                layers_raw = []
                for n in range (0, layer_index):
                    layers_raw.append (False)
                layers_raw.append (True)
                for n in range (layer_index+1, 32):
                    layers_raw.append (False)
                layers = tuple (layers_raw)
                
                #set bone layer
                bpy.ops.object.mode_set (mode='OBJECT')
                rig.data.bones[bone_name].layers = layers

                
            def set_bone_group (bone_name, group_name):
                
                bpy.ops.object.mode_set (mode='POSE')
                if group_name != None:
                    rig.pose.bones[bone_name].bone_group = rig.pose.bone_groups[group_name]

                    
            def set_bone_deform (bone_name, use_deform):
                bpy.ops.object.mode_set (mode='EDIT')
                ebone = rig.data.edit_bones[bone_name].use_deform = use_deform   

                
            def set_bone_transform_locks (bone_name, location, rotation, scale):
                bpy.ops.object.mode_set (mode='POSE')
                for n in range (0, 3):
                    if location == True:
                        rig.pose.bones[bone_name].lock_location[n] = True
                    else:
                        rig.pose.bones[bone_name].lock_location[n] = False
                    if rotation == True:
                        rig.pose.bones[bone_name].lock_rotation[n] = True
                    else:
                        rig.pose.bones[bone_name].lock_rotation[n] = False
                    if scale == True:
                        rig.pose.bones[bone_name].lock_scale[n] = True
                    else:
                        rig.pose.bones[bone_name].lock_scale[n] = False
                        
            def set_bone_type (name, type):
                if type != None:
                    bpy.ops.object.mode_set (mode='POSE')
                    rig.pose.bones[name]['bone_type'] = type


            def bone_settings (name, layer, group, deform, lock_loc, lock_rot, lock_scale, type):
                set_bone_only_layer (name, layer)
                set_bone_group (name, group)
                set_bone_deform (name, deform)
                set_bone_transform_locks (name, location=lock_loc, rotation=lock_rot, scale=lock_scale)
                set_bone_type (name, type)


            def duplicate_bone (source_name, new_name, parent_name, roll_override, length_override):
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                
                #transform
                ebone = ebones.new (name = new_name)
                ebone.use_connect = False
                ebone.head = ebones[source_name].head
                ebone.tail = ebones[source_name].tail
                if roll_override == False:
                    ebone.roll = ebones[source_name].roll
                else:
                    ebone.roll = roll_override
                
                #parent
                if parent_name == None:
                    ebone.parent = None        
                elif parent_name == 'SOURCE_PARENT':
                    ebone.parent = ebones[source_name].parent        
                else:
                    ebone.parent = ebones[parent_name]
                    
                #make it half long
                if length_override == 'HALF':
                    midpoint = mean (ebone.head, ebone.tail)
                    ebone.tail = midpoint
                    ebone.roll = ebones[source_name].roll
                
                return ebone.name


            def mirror_bone_to_point (bone_name, point):
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ebone = ebones[bone_name]
                
                new_head = ( point - ebone.head ) + point
                new_tail = ( point - ebone.tail ) + point
                
                ebone.head = new_head
                ebone.tail = new_tail
                

            def nth_point (A, B, alpha):
                
                x = ( (B - A) * alpha ) + A
                
                return x


            def set_ik_group (side):
                #set group
                if side == sides[0]:
                    ik_group = left_ik_group
                elif side == sides[1]:
                    ik_group = right_ik_group
                elif side == '_c':
                    ik_group = central_ik_group
                return ik_group


            ########################################################################################################
            ########################################################################################################

            def create_no_twist_bone (source_bone):
                #used with twist_targets
                no_twist_name = 'no_twist_'+source_bone
                if rig.data.bones.get (no_twist_name) == None:
                    duplicate_bone (source_name=source_bone, new_name=no_twist_name, parent_name='SOURCE_PARENT', roll_override=False, length_override='HALF')
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[no_twist_name]
                c = pbone.constraints.new ('DAMPED_TRACK')
                c.target = rig
                c.subtarget = source_bone
                c.head_tail = 1
                bone_settings (name=no_twist_name, layer=misc_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                return no_twist_name
                

            def create_twist_bones (source_bone, count, upper_or_lower_limb, twist_target_distance, twist_target_parent, lock_xz_rot, end_affector, source_bone_bend_axis):
                    
                twist_bones = []

                bpy.ops.object.mode_set (mode='EDIT')
                bpy.ops.armature.select_all (action='DESELECT')
                
                source_ebone = rig.data.edit_bones [source_bone]
                
                parent = source_ebone
                
                #create twist source bone
                twist_source = 'twist_'+source_bone
                twist_ebone_source = rig.data.edit_bones.new (name = twist_source)
                twist_ebone_source.head = source_ebone.head
                twist_ebone_source.tail = source_ebone.tail
                twist_ebone_source.roll = source_ebone.roll
                twist_ebone_source.parent = source_ebone.parent
                
                twist_ebone_source.select = True
                twist_ebone_source.select_head = True
                twist_ebone_source.select_tail = True
                
                #cut twist source bone to multiple twist bones
                if count > 1:
                    bpy.ops.armature.subdivide (number_cuts=count-1)
                
                #rename twist bones and set parents
                if upper_or_lower_limb == 'upper':
                    ebones = rig.data.edit_bones
                    new_name = 'twist_1_'+source_bone
                    ebones['twist_'+source_bone].name = new_name
                    ebones[new_name].use_connect = False
                    ebones[new_name].parent = parent
                    twist_bones.append(new_name)
                    if count > 1:
                        for n in range (1, count):
                            new_name = 'twist_'+str(count-(n-1))+'_'+source_bone
                            ebones['twist_'+source_bone+'.00'+str(n)].name = new_name
                            ebones[new_name].use_connect = False
                            ebones[new_name].parent = parent
                            
                            twist_bones.append(new_name)                    
                            
                elif upper_or_lower_limb == 'lower':
                    ebones = rig.data.edit_bones
                    new_name = 'twist_'+str(count)+'_'+source_bone
                    ebones['twist_'+source_bone].name = new_name
                    ebones[new_name].use_connect = False
                    ebones[new_name].parent = parent
                    twist_bones.append(new_name)
                    if count > 1:
                        for n in range (1, count):
                            new_name = 'twist_'+str(n)+'_'+source_bone
                            ebones['twist_'+source_bone+'.00'+str(n)].name = new_name
                            ebones[new_name].use_connect = False
                            ebones[new_name].parent = parent
                            
                            twist_bones.append(new_name)                    
                            
                #twist target bones
                if upper_or_lower_limb == 'upper':  
                          
                    #create no-twist bone if it does not exist already       
                    no_twist_name = create_no_twist_bone (source_bone=source_bone)
                    
                    bpy.ops.object.mode_set (mode='EDIT')
                    #duplicate source bone
                    twist_target_name = 'twist_target_'+source_bone
                    tt_ebone = rig.data.edit_bones.new (name=twist_target_name)
                    ebones = rig.data.edit_bones
                    tt_ebone.head = ebones [source_ebone.name].head
                    tt_ebone.tail = ebones [source_ebone.name].tail
                    tt_ebone.roll = ebones [source_ebone.name].roll
                    tt_ebone.parent = ebones [no_twist_name]
                    #translate twist target bone
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    
                    if source_bone_bend_axis == '-X':
                        amount = -twist_target_distance
                        vector = 0, 0, amount
                    
                    translate_ebone_local (ebone=tt_ebone, vector=vector)
                    ebone = ebones [twist_target_name]
                    ebone.tail = ebone.head + Vector ((0, 0, general_bone_size))
                    bone_settings (name=twist_target_name, layer=twist_target_layer, group=twist_group, deform=False, lock_loc=False, lock_rot=True, lock_scale=True, type=None)
                    set_bone_shape (bone_name=twist_target_name, shape='twist_target', transform_bone=None, auto_scale_with_offset=None, manual_scale=target_shape_size, shape_bone=False, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)   
                     
                    #twist target line bones
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    tt_ebone = ebones [twist_target_name]
                    twist_target_line_name = 'twist_target_line_'+source_bone
                    ttl_ebone = ebones.new (name = twist_target_line_name)
                    ttl_ebone.head = ebones[source_bone].head
                    ttl_ebone.tail = tt_ebone.head        
                    ttl_ebone.parent = ebones[source_bone]
                    bpy.ops.object.mode_set (mode='OBJECT')
                    rig.data.bones[twist_target_line_name].hide_select = True
                    bone_settings (name=twist_target_line_name, layer=twist_target_layer, group=twist_group, deform=False, lock_loc=True, lock_rot=True, lock_scale=True, type=None)
                    set_bone_shape (bone_name=twist_target_line_name, shape='line', transform_bone=None, auto_scale_with_offset=None, manual_scale=1, shape_bone=False, keep_rot_when_radius_check=False, use_bone_size=True, shape_bone_parent_override=False)
                  
                elif upper_or_lower_limb == 'lower':
                    if end_affector != None:
                        twist_target_name = 'twist_target_'+source_bone
                        create_leaf_bone (source_bone=source_bone, name=twist_target_name, length=general_bone_size)
                        #clear parent
                        bpy.ops.object.mode_set (mode='EDIT')
                        rig.data.edit_bones[twist_target_name].parent = None
                        #child of parent it to end affector (hand or foot) - the use of constraint is needed for the twist constraints to work
                        bpy.ops.object.mode_set (mode='POSE')
                        pbone = rig.pose.bones[twist_target_name]
                        c = pbone.constraints.new ('CHILD_OF')
                        c.name = 'Copy End Affector'
                        c.target = rig
                        c.subtarget = end_affector                      
                        #set inverse matrix
                        rig.data.bones.active = rig.data.bones[twist_target_name]
                        context_copy = bpy.context.copy()
                        context_copy["constraint"] = pbone.constraints['Copy End Affector']
                        bpy.ops.constraint.childof_set_inverse(context_copy, constraint='Copy End Affector', owner='BONE')
                        
                        bone_settings (name=twist_target_name, layer=twist_target_layer, group=twist_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                        set_bone_shape (bone_name=twist_target_name, shape='twist_target', transform_bone=None, auto_scale_with_offset=None, manual_scale=target_shape_size, shape_bone=False, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)   

             
                #bone settings
                for name in twist_bones:
                    bone_settings (name, layer=twist_layer, group=twist_group, deform=True, lock_loc=True, lock_rot=False, lock_scale=True, type='twist')
                    if lock_xz_rot == True:
                        bpy.ops.object.mode_set (mode='POSE')
                        rig.pose.bones[name].lock_rotation[0] = True
                        rig.pose.bones[name].lock_rotation[2] = True
                            
                return twist_bones


            def remove_surplus_twist_bones (twist_bone_target_count, twist_bones_created, limb):
                removed_twist_bones = []
                bpy.ops.object.mode_set (mode='EDIT')
                if twist_bone_target_count < twist_bones_created:
                    for n in range (twist_bone_target_count+1, twist_bones_created+1):
                        removed_twist_bones.append ('twist_'+str(n)+'_'+limb)
                        rig.data.edit_bones.remove (rig.data.edit_bones ['twist_'+str(n)+'_'+limb])
                return removed_twist_bones


            def twist_constraints (upper_or_lower, source_bone, target_bone, twist_bone_count, influences, source_bone_bend_axis, is_thigh):
                
                bend_axis = source_bone_bend_axis
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones

                for n in range (1, twist_bone_count+1):
                    pbone = pbones ['twist_'+str(n)+'_'+source_bone]
                
                    if upper_or_lower == 'upper':       
                        c = pbone.constraints.new ('LOCKED_TRACK')
                        c.name = 'twist'
                        c.target = rig
                        c.subtarget = target_bone
                        c.head_tail = 0

                        if bend_axis == '-X':
                            c.track_axis = 'TRACK_NEGATIVE_Z'
                                        
                        c.lock_axis= 'LOCK_Y'
                        c.influence = influences[n-1]
                        
                    elif upper_or_lower == 'lower':
                        c = pbone.constraints.new ('TRACK_TO')
                        c.name = 'twist'
                        c.target = rig
                        c.subtarget = target_bone
                        c.head_tail = 0
                        c.track_axis = 'TRACK_Y'
                        c.up_axis = 'UP_Z'
                        c.use_target_z = True
                        c.target_space = 'WORLD'
                        c.owner_space = 'WORLD'
                        c.influence = influences[n-1]
                        
                        c = pbone.constraints.new ('LIMIT_ROTATION')
                        c.name = 'limit rotation'
                        c.owner_space = 'LOCAL'
                        c.influence = 1
                        c.use_limit_x = True
                        c.use_limit_y = False
                        c.use_limit_z = True
                        c.use_transform_limit = True
                        c.min_x = 0
                        c.max_x = 0
                        c.min_z = 0
                        c.max_z = 0

                    
                #twist target line
                if upper_or_lower == 'upper':
                    pbone = pbones ['twist_target_line_'+source_bone]
                    c = pbone.constraints.new ('STRETCH_TO')
                    c.name = 'twist target line'
                    c.target = rig
                    c.subtarget = 'twist_target_'+source_bone
                    c.head_tail = 0
                    c.bulge = 1
                    c.use_bulge_min = False
                    c.use_bulge_max = False
                    c.volume = 'VOLUME_XZX'
                    c.keep_axis = 'PLANE_X'
                    c.influence = 1
                    
                #twist target thigh
                if is_thigh == True:
                    pbone = pbones ['twist_target_'+source_bone]
                    c = pbone.constraints.new ('TRANSFORM')
                    c.name = 'thigh rotation to location'
                    c.use_motion_extrapolate = True
                    c.target = rig
                    c.subtarget = source_bone
                    c.map_from = 'ROTATION'
                    c.map_to = 'LOCATION'

                    if bend_axis == '-X':
                        c.map_to_x_from = 'X'
                        c.map_to_y_from = 'X'
                        c.map_to_z_from = 'X'
                        c.from_min_x_rot = radians(-180)
                        c.from_max_x_rot = radians(180)
                        
                    c.to_min_y = 1
                    c.to_max_y = -1
                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    c.influence = 1
                    
                    
            #CHEST OR HEAD TARGET
            def chain_target (fk_chain, ik_chain, chain_target_distance, chain_target_size, target_name, shape, use_copy_loc, copy_loc_target_bone, add_constraint_to_layer, module, prop_name):
                #target
                bpy.ops.object.mode_set (mode='EDIT')
                ebone = rig.data.edit_bones.new (name=target_name)
                ebone.head = rig.data.edit_bones[fk_chain[-1]].head + Vector ((0, -chain_target_distance, 0))
                ebone.tail = ebone.head + Vector ((0, 0, chain_target_size))
                ebone.roll = 0
                bone_settings (name=target_name, layer=target_layer, group=target_group, deform=False, lock_loc=False, lock_rot=True, lock_scale=True, type=None)     
                
                #servants
                def create_servants (layer, source_bones):
                    servants = []
                    for name in source_bones:
                        bpy.ops.object.mode_set (mode='EDIT')
                        servant = 'target_servant_'+name
                        duplicate_bone (source_name=name, new_name=servant, parent_name=None, roll_override=False, length_override='HALF')
                        ebones = rig.data.edit_bones
                        ebone = ebones[servant]
                        ebone.roll = 0
                        ebone.parent = ebones[target_name]
                        translate_ebone_local (ebone=ebone, vector=(0, 0, chain_target_distance))
                        bone_settings (name=servant, layer=layer, group=None, deform=False, lock_loc=True, lock_rot=True, lock_scale=True, type=None)
                        servants.append (servant)
                    return servants
                
                servants = create_servants (layer=fk_extra_layer, source_bones=fk_chain)     
                    
                #CONSTRAINT TO TARGET
                def constraint_to_target (servants, constraint_bones):
                    bpy.ops.object.mode_set (mode='POSE')
                    pbones = rig.pose.bones
                    for index, name in enumerate (constraint_bones):
                        c = pbones[name].constraints.new ('TRACK_TO')
                        c.target = rig
                        c.subtarget = servants[index]
                        c.up_axis = 'UP_Y'
                        c.track_axis = 'TRACK_Z'
                        c.influence = 0
                        c.name = target_name
                        
                        prop_to_drive_constraint (name, bone_name=name, constraint_name=c.name, prop_name=name+'_to_'+target_name, attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=0.0, description='', expression='v1')
                
                constraint_to_target (servants, constraint_bones=fk_chain)
                    
                if use_copy_loc:
                    bpy.ops.object.mode_set (mode='POSE')
                    pbones = rig.pose.bones
                    c = pbones[target_name].constraints.new ('COPY_LOCATION')
                    c.name = 'Copy ' + copy_loc_target_bone
                    c.target = rig
                    c.subtarget = copy_loc_target_bone
                    c.use_offset = True
                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    
                    prop_to_drive_constraint (target_name, bone_name=target_name, constraint_name=c.name, prop_name='stick_to_'+copy_loc_target_bone, attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=0.0, description='', expression='v1')

                set_bone_shape (bone_name=target_name, shape=shape, transform_bone=None, auto_scale_with_offset=None, manual_scale=chest_target_size/4, shape_bone=False, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                
                if add_constraint_to_layer:
                    prop_to_drive_layer (prop_bone='module_props__'+module, layer_index=target_layer, prop_name=prop_name, prop_min=0, prop_max=1, prop_default=0, description='', expression='v1')
                
                #CONSTRAINT CTRL RIG TO CHEST TARGET
                servants = create_servants (layer=ctrl_ik_extra_layer, source_bones=ik_chain)
                constraint_to_target (servants=servants, constraint_bones=ik_chain)                      
                
                
            ########################################################################################################
            ########################################################################################################

            #APPEND BONE SHAPES

            link_collection ('GYAZ_game_rigger_widgets', source_path)

            bpy.ops.object.mode_set (mode='OBJECT')
            bpy.ops.object.select_all (action='DESELECT')
            rig.select_set (True)
            bpy.context.view_layer.objects.active = rig

            shape_prefix = 'GYAZ_game_rigger_WIDGET__'


            ########################################################################################################
            ########################################################################################################

            #MESH FOR RAY CASTING:

            #create new object from character meshes and make a BVHTree from it
            bpy.ops.object.mode_set (mode='OBJECT')
            bpy.ops.object.select_all (action='DESELECT')
            for mesh in rig.children:
                if mesh.type == 'MESH':
                    mesh.hide_select = False
                    mesh.select_set (True)
            bpy.context.view_layer.objects.active = rig.children [0]
            bpy.ops.object.duplicate_move ()
            bpy.ops.object.join ()
            bpy.ops.object.transform_apply (location=True, rotation=True, scale=True)
            
            merged_character_mesh = bpy.context.active_object

            my_tree = BVHTree.FromObject(scene.objects[merged_character_mesh.name], bpy.context.depsgraph)

            bpy.ops.object.select_all (action='DESELECT')
            rig.select_set (True)
            bpy.context.view_layer.objects.active = rig


            #BONE SHAPE FUNCTION

            def get_radius (bone_name, number_of_checks, keep_rotation):
                
                #duplicate bone
                bpy.ops.object.mode_set (mode='EDIT')
                source_ebone = rig.data.edit_bones[bone_name]
                
                distance = 100
                start = (source_ebone.head + source_ebone.tail) * .5
                
                hit_distances = []
                check_points = bone_radius_check_points(ebone=source_ebone, num=number_of_checks, dist=distance)
                
                for check_point in check_points:
                    #cast ray
                    hit_loc, hit_nor, hit_index, hit_dist = my_tree.ray_cast (start, check_point - start, distance)
                    
                    if hit_dist is not None:
                        hit_distances.append (hit_dist)
                    else:
                        hit_distances.append (0.5)
                
                longest_hit_distance = max (hit_distances)
                
                return longest_hit_distance


            def create_leaf_bone (source_bone, name, length):
                bpy.ops.object.mode_set (mode='EDIT')
                source_ebone = rig.data.edit_bones[source_bone]
                target_pos = ( source_ebone.tail - source_ebone.head ) + source_ebone.tail
                leaf_ebone = rig.data.edit_bones.new (name = name)
                leaf_ebone.head = source_ebone.tail
                leaf_ebone.tail = target_pos
                leaf_ebone.roll = source_ebone.roll
                leaf_ebone.parent = source_ebone
                return leaf_ebone.name

                
            def set_bone_shape (bone_name, shape, transform_bone, auto_scale_with_offset, manual_scale, shape_bone, keep_rot_when_radius_check, use_bone_size, shape_bone_parent_override):
                
                #bone shape location
                if shape_bone == 'CENTER' or shape_bone == 'LEAF': 
                    bpy.ops.object.mode_set (mode='EDIT') 
                    shape_bone_name = 'shape_' + bone_name 
                
                    if shape_bone == 'LEAF':
                        ebones = rig.data.edit_bones
                        if transform_bone == None:
                            source_bone = bone_name
                        else:
                            source_bone = transform_bone
                            
                        create_leaf_bone (source_bone=source_bone, name=shape_bone_name, length=get_distance (ebones[bone_name].head, ebones[bone_name].tail))
                            

                    elif shape_bone == 'CENTER':
                        ebone = rig.data.edit_bones.new (name=shape_bone_name)
                        ebones = rig.data.edit_bones
                        if transform_bone == None:                        
                            ebone.head = mean (ebones[bone_name].head, ebones[bone_name].tail)
                            ebone.tail = ebones[bone_name].tail
                            ebone.roll = ebones[bone_name].roll
                            ebone.parent = ebones[bone_name]
                            
                        else:
                            ebone.head = mean (ebones[transform_bone].head, ebones[transform_bone].tail)
                            ebone.tail = ebones[transform_bone].tail
                            ebone.roll = ebones[transform_bone].roll
                            ebone.parent = ebones[transform_bone]
                                
                    set_bone_only_layer (shape_bone_name, 30)
                    set_bone_deform (shape_bone_name, False)
                    
                    transform_bone = shape_bone_name
                    
                elif shape_bone == '-X' or shape_bone == '-Z' or shape_bone == 'Z':
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones 
                    shape_bone_name = 'shape_' + bone_name
                    ebone = ebones.new (name=shape_bone_name)
                    ebone.head = ebones[bone_name].head
                    ebone.tail = ebones[bone_name].tail
                    ebone.roll = ebones[bone_name].roll
                    ebone.parent = ebones[bone_name]
                    ebone_name = ebone.name
                    
                    if shape_bone == '-X':
                        v1 = 0, 0, 1
                        v2 = 0, 0, -1
                        v3 = 0, 0, pole_target_distance
                    elif shape_bone == '-Z':
                        v1 = 1, 0, 0
                        v2 = -1, 0, 0
                        v3 = 0, 0, -pole_target_distance
                    elif shape_bone == 'Z':
                        v1 = -1, 0, 0
                        v2 = 1, 0, 0
                        v3 = pole_target_distance, 0, 0
                    
                    translate_ebone_local (ebone=ebone, vector=v1)
                    
                    hit_loc, hit_nor, hit_index, hit_dist = cast_ray_from_bone (start_bone=bone_name, head_tail='head', ebone_pbone='ebone', direction=ebone.head, distance=10)
                    
                    translate_ebone_local (ebone=ebone, vector=v2)
                    
                    if hit_dist != None:        
                        translate_ebone_local (ebone=ebone, vector=v3)
                        
                    set_bone_only_layer (shape_bone_name, 30)
                    set_bone_deform (shape_bone_name, False)
                    
                    transform_bone = shape_bone_name
                    
                elif shape_bone == 'UP' or shape_bone == 'FRONT':
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones 
                    shape_bone_name = 'shape_' + bone_name
                    ebone = ebones.new (name=shape_bone_name)
                    ebone.head = ebones[bone_name].head
                    if shape_bone == 'UP':
                        ebone.tail = ebone.head + Vector ((0, 0, general_bone_size))
                    elif shape_bone == 'FRONT':
                        ebone.tail = ebone.head + Vector ((0, - general_bone_size, 0))
                    ebone.roll = 0
                    ebone.parent = ebones[bone_name]
                    
                    set_bone_only_layer (shape_bone_name, 30)
                    set_bone_deform (shape_bone_name, False)
                    
                    transform_bone = shape_bone_name
                    

                #shape bone parent override (used for freezing shape in place while transforming bone)
                if shape_bone_parent_override != False:    
                    if shape_bone == False or shape_bone == None:
                        print ('...')
                    else: 
                        bpy.ops.object.mode_set (mode='EDIT')
                        ebones = rig.data.edit_bones
                        if ebones.get (shape_bone_name) != None:
                                ebones[shape_bone_name].parent = ebones[shape_bone_parent_override]
                                    
                
                #calculate shape scale
                if auto_scale_with_offset != None:
                    if transform_bone == None:
                        scale = get_radius (bone_name, number_of_checks=4, keep_rotation=keep_rot_when_radius_check)
                    else:
                        scale = get_radius (transform_bone, number_of_checks=4, keep_rotation=keep_rot_when_radius_check)
                    scale += auto_scale_with_offset
                else:
                    scale = manual_scale
                
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[bone_name]
                pbone.custom_shape = bpy.data.objects[shape_prefix+shape]
                pbone.use_custom_shape_bone_size = False
                pbone.custom_shape_scale = scale
                if transform_bone != None:
                    pbone.custom_shape_transform = rig.pose.bones[transform_bone]
                    
                pbone.use_custom_shape_bone_size = use_bone_size
                    
                #show wire
                bone = rig.data.bones[bone_name].show_wire = True


            ########################################################################################################
            ########################################################################################################

            def separate_relevant_bones (relevant_bones):
                #separate relevant bones into fk and no-fk groups
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                fk_bones = []
                non_fk_bones = []
                touch_bones = []
                for bone in relevant_bones:               
                    pbone = pbones[bone]
                    if 'bone_type' in pbone:
                        if pbone['bone_type'] == 'fk':
                            fk_bones.append (bone)
                        elif pbone['bone_type'] == 'ik' or pbone['bone_type'] == 'ctrl':
                            non_fk_bones.append (bone)
                        elif pbone['bone_type'] == 'touch':
                            touch_bones.append (bone)
                return fk_bones, non_fk_bones, touch_bones

            #fk, ik visibility
            def bone_visibility (prop_bone, module, relevant_bones, ik_ctrl):
                fk_bones, non_fk_bones, touch_bones= separate_relevant_bones (relevant_bones)
                for bone in fk_bones:
                    prop_to_drive_bone_attribute (prop_bone, bone_name=bone, bone_type='BONE', prop_name='visible_fk_'+module, attribute='hide', prop_min=0, prop_max=1, prop_default=1, description='', expression='1-v1')
                if ik_ctrl != None:           
                    for bone in non_fk_bones:
                        prop_to_drive_bone_attribute (prop_bone, bone_name=bone, bone_type='BONE', prop_name='visible_'+ik_ctrl+'_'+module, attribute='hide', prop_min=0, prop_max=1, prop_default=1, description='', expression='1-v1')
                if len (touch_bones) > 0:
                    for bone in touch_bones:
                            prop_to_drive_bone_attribute (prop_bone, bone_name=bone, bone_type='BONE', prop_name='visible_touch_'+module, attribute='hide', prop_min=0, prop_max=1, prop_default=1, description='', expression='1-v1')

                    
                
            def set_parent_chain (chain, first_parent):
                for index, name in enumerate(chain):
                    #set parents
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    if index == 0:
                        if first_parent != None:
                            parent = ebones[first_parent]
                    else:
                        parent = ebones[chain[index-1]]
                    ebones[name].use_connect = False
                    ebones[name].parent = parent


            def prop_to_drive_constraint (prop_bone, bone_name, constraint_name, prop_name, attribute, prop_min, prop_max, prop_default, description, expression):    
                #prop
                rig.pose.bones[prop_bone][prop_name] = prop_default
                
                #min, max soft_min, soft_max, description on properties
                if "_RNA_UI" not in rig.pose.bones[prop_bone]:
                    rig.pose.bones[prop_bone]["_RNA_UI"] = {}

                rig.pose.bones[prop_bone]["_RNA_UI"][prop_name] = {"min":prop_min, "max":prop_max, "soft_min":prop_min, "soft_max":prop_max, "description":description}
                #driver
                d = rig.driver_add( 'pose.bones["'+bone_name+'"].constraints["'+constraint_name+'"].'+attribute ).driver
                v1 = d.variables.new ()
                v1.name = 'v1'
                v1.type = 'SINGLE_PROP'
                t = v1.targets[0]
                t.id = rig
                t.data_path = 'pose.bones["'+prop_bone+'"]["'+prop_name+'"]'    
                d.expression = expression

                
            def prop_to_drive_layer (prop_bone, layer_index, prop_name, prop_min, prop_max, prop_default, description, expression):    
                #prop
                rig.pose.bones[prop_bone][prop_name] = prop_default
                
                #min, max soft_min, soft_max, description on properties
                if "_RNA_UI" not in rig.pose.bones[prop_bone]:
                    rig.pose.bones[prop_bone]["_RNA_UI"] = {}
                
                rig.pose.bones[prop_bone]["_RNA_UI"][prop_name] = {"min":prop_min, "max":prop_max, "soft_min":prop_min, "soft_max":prop_max, "description":description}
                #driver
                d = rig.data.driver_add( 'layers', layer_index ).driver
                v1 = d.variables.new ()
                v1.name = 'v1'
                v1.type = 'SINGLE_PROP'
                t = v1.targets[0]
                t.id = rig
                t.data_path = 'pose.bones["'+prop_bone+'"]["'+prop_name+'"]'     
                d.expression = expression
                

            def prop_to_drive_bone_attribute (prop_bone, bone_name, bone_type, prop_name, attribute, prop_min, prop_max, prop_default, description, expression):    
                #prop
                rig.pose.bones[prop_bone][prop_name] = prop_default
                
                #min, max soft_min, soft_max, description on properties
                if "_RNA_UI" not in rig.pose.bones[prop_bone]:
                    rig.pose.bones[prop_bone]["_RNA_UI"] = {}    
                
                rig.pose.bones[prop_bone]["_RNA_UI"][prop_name] = {"min":prop_min, "max":prop_max, "soft_min":prop_min, "soft_max":prop_max, "description":description}
                #driver
                if bone_type == 'PBONE':
                    d = rig.driver_add( 'pose.bones["'+bone_name+'"].'+attribute ).driver
                elif bone_type == 'BONE':
                    d = rig.data.driver_add( 'bones["'+bone_name+'"].'+attribute ).driver
                v1 = d.variables.new ()
                v1.name = 'v1'
                v1.type = 'SINGLE_PROP'
                t = v1.targets[0]
                t.id = rig
                t.data_path = 'pose.bones["'+prop_bone+'"]["'+prop_name+'"]'      
                d.expression = expression

                
            def prop_to_drive_pbone_attribute_with_array_index (prop_bone, bone_name, prop_name, attribute, array_index, prop_min, prop_max, prop_default, description, expression):    
                #prop
                rig.pose.bones[prop_bone][prop_name] = prop_default
                
                #min, max soft_min, soft_max, description on properties
                if "_RNA_UI" not in rig.pose.bones[prop_bone]:
                    rig.pose.bones[prop_bone]["_RNA_UI"] = {}
                
                rig.pose.bones[prop_bone]["_RNA_UI"][prop_name] = {"min":prop_min, "max":prop_max, "soft_min":prop_min, "soft_max":prop_max, "description":description}
                #driver
                d = rig.driver_add( 'pose.bones["'+bone_name+'"].'+attribute, array_index ).driver
                v1 = d.variables.new ()
                v1.name = 'v1'
                v1.type = 'SINGLE_PROP'
                t = v1.targets[0]
                t.id = rig
                t.data_path = 'pose.bones["'+prop_bone+'"]["'+prop_name+'"]'     
                d.expression = expression


            ########################################################################################################
            ########################################################################################################

            def create_mudule_prop_bone (module):
                bpy.ops.object.mode_set (mode='EDIT')
                name = 'module_props__' + module
                ebones = rig.data.edit_bones    
                #create module bone if it does not exist
                if ebones.get (name) == None:    
                    ebone = ebones.new (name=name)
                    ebone.head = Vector ((0, 0, 0))
                    ebone.tail = Vector ((0, 0, 0.5))
                    set_bone_only_layer (bone_name=name, layer_index=module_prop_layer)
                    set_bone_deform (bone_name=name, use_deform=False)        
                return name


            def set_module_on_relevant_bones (relevant_bones, module):
                #set module name on relevant bones (used by the 'N-panel' interface)
                bpy.ops.object.mode_set (mode='POSE')
                for bone in relevant_bones:
                    rig.pose.bones[bone]['module'] = module
                    

            #for registering modules for the 'Snap&Key' operator
            def snappable_module (module):
                if 'snappable_modules' not in rig.data:
                    rig.data['snappable_modules'] = []
                list = []
                for item in rig.data['snappable_modules']:
                    list.append (item)
                list.append (module)
                rig.data['snappable_modules'] = list
                
                rig.pose.bones['module_props__'+module]["snap_n_key__fk_ik"] = 1
                rig.pose.bones['module_props__'+module]["snap_n_key__should_snap"] = 1


            ########################################################################################################
            ########################################################################################################

            def signed_angle(vector_u, vector_v, normal):
                #normal specifies orientation
                angle = vector_u.angle(vector_v)
                if vector_u.cross(vector_v).angle(normal) < 1:
                    angle = -angle
                return angle

            def get_pole_angle(base_bone, ik_bone, pole_bone):
                pole_location = pole_bone.head
                pole_normal = (ik_bone.tail - base_bone.head).cross(pole_location - base_bone.head)
                projected_pole_axis = pole_normal.cross(base_bone.tail - base_bone.head)
                return signed_angle(base_bone.x_axis, projected_pole_axis, base_bone.tail - base_bone.head)


            def calculate_pole_target_location (b1, b2, b3, pole_target_distance):
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                
                midpoint = ( ebones[b1].head + ebones[b3].head ) / 2
                difference = ebones[b2].head - midpoint
                ###calculate multiplier for desired target distance
                current_distance = get_distance (Vector ((0, 0, 0)), difference)
                multiplier = pole_target_distance / current_distance
                ###
                pole_pos = difference * multiplier + ebones[b2].head
                
                return pole_pos

            def calculate_pole_target_location_2 (b1, b2, b3, pole_target_distance, b2_bend_axis):
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                
                set_cursor_location (location=ebones[b2].head)
                
                pole_bone = 'pole_pos_'+b2
                duplicate_bone (source_name=b2, new_name=pole_bone, parent_name=None, roll_override=False, length_override=None)
                
                if b2_bend_axis == 'X':
                    v = 0, 0, -pole_target_distance
                elif b2_bend_axis == '-X':
                    v = 0, 0, pole_target_distance
                    
                translate_ebone_local (ebone=ebones[pole_bone], vector=v)
                
                pole_pos = ebones[pole_bone].head
                rig.data['temp'] = pole_pos
                ebones.remove (ebones[pole_bone])
                
                return Vector((rig.data['temp']))


            ########################################################################################################
            ########################################################################################################

            #TWO-BONE IK FUNCTION

            def three_bone_limb (module, b1, b2, b3, pole_target, pt_distance, parent_pt_to_ik_target, b2_bend_axis, b2_bend_back, first_parent, fk_layer, ctrl_ik_layer, ik_group, keep_last_bone_rot_when_radius_check, ik_parent, pole_parent, b3_shape_bone):

                module = module
                b1 = b1
                b2 = b2
                b3 = b3
                pole_target_name = pole_target
                pole_target_distance = pt_distance
                parent_pole_target_to_ik_target = parent_pt_to_ik_target
                limit_ik_b2 = True
                b2_bend_axis = b2_bend_axis
                b2_max_bend_bwrd = b2_bend_back
                limit_fk_b2 = False
                inable_stretch = False
                chain_parent = first_parent
                ik_parent = ik_parent
                create_ik_twist_bones = False
                fk_layer = fk_layer
                ctrl_ik_layer = ctrl_ik_layer
                module_prop_layer = 30

                bone_names = [b1, b2, b3]

                #bones that should be used for animation
                relevant_bones = []

                #for module properties
                prop_bone = create_mudule_prop_bone (module=module)

                #AXIS LOCKS
                if b2_bend_axis == 'X' or '-X':    
                    axis_locks_string = ['y', 'z']
                    axis_locks_int = [1, 2]
                    
                #_____________________________________________________________________________________________________

                #LOW-LEVEL RIG
                for name in bone_names:
                    bone_settings (name=name, layer=base_layer, group='base', deform=True, lock_loc=True, lock_rot=False, lock_scale=True, type='base')
                    relevant_bones.append (name)


                #_____________________________________________________________________________________________________    

                #FK
                for index, name in enumerate(bone_names):
                    if index == 0:
                        parent_name = chain_parent
                    else:
                        parent_name = fk_prefix + bone_names[index-1]
                    duplicate_bone (source_name=name, new_name=fk_prefix+name, parent_name=parent_name, roll_override=False, length_override=None)
                    
                    bone_settings (name=fk_prefix+name, layer=fk_layer, group=fk_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type='fk')
                    
                    if index == 2:
                        shape_bone = b3_shape_bone
                        keep_rot = keep_last_bone_rot_when_radius_check
                        shape = 'sphere'           
                    else:
                        shape_bone = 'CENTER'
                        keep_rot = False
                        shape = 'inner_circle'
                    set_bone_shape (bone_name=fk_prefix+name, shape=shape, transform_bone=None, auto_scale_with_offset=auto_bone_shape_scale_offset_limb, manual_scale=1, shape_bone=shape_bone, keep_rot_when_radius_check=keep_rot, use_bone_size=False, shape_bone_parent_override=False)
                    
                    relevant_bones.append (fk_prefix+name)

                 
                #FK LIMITS:   
                #limit fk_b2 to single-axis rotation
                if limit_fk_b2 == True:
                    default = True
                else:
                    default = False

                for axis in axis_locks_int:           
                    prop_to_drive_pbone_attribute_with_array_index (fk_prefix+b2, bone_name=fk_prefix+b2, prop_name='limit_fk_'+module, attribute='lock_rotation', array_index=axis, prop_min=0, prop_max=1, prop_default=default, description='', expression='v1')
                    
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[fk_prefix+b2]
                c = pbone.constraints.new ('LIMIT_ROTATION')
                c.name = 'Limit rotation'
                c.owner_space = 'LOCAL'
                c.use_limit_x = True
                c.use_limit_y = True
                c.use_limit_z = True
                c.use_transform_limit = True
                if 0 in axis_locks_int:
                    c.min_x = 0
                    c.max_x = 0
                if 1 in axis_locks_int:
                    c.min_y = 0
                    c.max_y = 0
                if 2 in axis_locks_int:
                    c.min_z = 0
                    c.max_z = 0

                #limits
                if b2_bend_axis == 'X':
                    bend_axis = 'x'
                    b2_min = 0 - radians(b2_max_bend_bwrd)
                    b2_max = radians(180) - abs(b2_min)  
                elif b2_bend_axis == '-X':
                    bend_axis = 'x'
                    b2_max = 0 + radians(b2_max_bend_bwrd)
                    b2_min = abs(b2_max) - radians(180)                   
                
                if bend_axis == 'x':
                    axis = 0
                    c.min_x = b2_min
                    c.max_x = b2_max
                    
                prop_to_drive_constraint (fk_prefix+b2, bone_name=fk_prefix+b2, constraint_name='Limit rotation', prop_name='limit_fk_'+module, attribute='mute', prop_min=0, prop_max=1, prop_default=default, description='', expression='1-v1')     
                    
                #BIND RIG TO FK RIG constraints
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones

                for index, name in enumerate(bone_names):
                    c = pbones[name].constraints.new ('COPY_ROTATION')
                    c.name = 'bind_to_fk_1'
                    c.target = rig
                    c.subtarget = fk_prefix + name
                    c.mute = True
                    

                #_____________________________________________________________________________________________________
                      
                #IK
                for index, name in enumerate(bone_names):
                    if index == 0 or index == 2:
                        parent_name = chain_parent
                    else:
                        parent_name = ik_prefix + bone_names[index-1]
                    duplicate_bone (source_name=name, new_name=ik_prefix+name, parent_name=parent_name, roll_override=False, length_override=None)
                    
                    if index == 2:
                        layer=ctrl_ik_layer
                        lock_loc = False
                    else:
                        layer=ctrl_ik_extra_layer
                        lock_loc = True
                    bone_settings (name=ik_prefix+name, layer=layer, group=ik_group, deform=False, lock_loc=lock_loc, lock_rot=False, lock_scale=True, type='ik')
                
                set_bone_shape (bone_name=ik_prefix+b3, shape='cube', transform_bone=None, auto_scale_with_offset=auto_bone_shape_scale_offset_limb, manual_scale=1, shape_bone=b3_shape_bone, keep_rot_when_radius_check=keep_last_bone_rot_when_radius_check, use_bone_size=False, shape_bone_parent_override=False)

                relevant_bones.append (ik_prefix+b3)
                    
                #ik_twist
                if create_ik_twist_bones == True:
                    
                    twist_bones = [b1, b2]
                    
                    for name in twist_bones:
                        ik_twist_bone = ik_prefix + 'twist_' + name
                        duplicate_bone (source_name=name, new_name=ik_twist_bone, parent_name=ik_prefix+name, roll_override=False)
                        bone_settings (name=ik_twist_bone, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)

                        bpy.ops.object.mode_set (mode='POSE')
                        pbone = rig.pose.bones[ik_twist_bone]
                        pbone.lock_rotation[0] = True
                        pbone.lock_rotation[1] = False
                        pbone.lock_rotation[2] = True
                        
                        relevant_bones.append (ik_twist_bone)
                    
                #unparent ik handle
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ebone = ebones[ik_prefix+b3]
                ebone.parent = ebones[ik_parent]

                #pole target:
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones

                #pole_pos = calculate_pole_target_location (b1, b2, b3, pole_target_distance)
                pole_pos = calculate_pole_target_location_2 (b1, b2, b3, pole_target_distance, b2_bend_axis=b2_bend_axis)
                
                #create pole_target
                pole_target = 'target_' + pole_target_name
                ebone = ebones.new (name=pole_target)
                ebone.head = pole_pos
                ebone.tail = pole_pos + Vector ((0, 0, 0.1))

                relevant_bones.append (pole_target)

                #parent it to ik_target
                if parent_pole_target_to_ik_target == True:
                    ebone.parent = ebones[ik_prefix+b3]
                else:
                    ebone.parent = ebones[pole_parent]    

                bone_settings (name=ebone.name, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=False, lock_rot=False, lock_scale=True, type='ik')
                set_bone_shape (bone_name=pole_target, shape='sphere', transform_bone=None, auto_scale_with_offset=None, manual_scale=target_shape_size, shape_bone=None, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)

                
                #constraint
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones

                pole_angle = get_pole_angle (base_bone=ebones[b1], ik_bone=ebones[b2], pole_bone=ebones[pole_target])

                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones

                pbone = pbones[ik_prefix+b2]

                c = pbone.constraints.new ('IK')
                c.target = rig
                c.subtarget = ik_prefix+b3
                c.pole_target = rig
                c.pole_subtarget = pole_target
                c.pole_angle = pole_angle
                c.chain_count = 2
                c.use_stretch = inable_stretch


                #pole target line
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                pole_target_line = 'target' + '_line_' + pole_target_name

                ebone = ebones.new (name=pole_target_line)
                ebone.head = ebones[ik_prefix + b2].head
                ebone.tail = ebones[pole_target].head
                ebone.parent = ebones[ik_prefix + b2]
                bone_settings (name=pole_target_line, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=True, lock_rot=True, lock_scale=True, type='ik')

                bpy.ops.object.mode_set (mode='POSE')
                rig.data.bones[pole_target_line].hide_select = True

                pbone = rig.pose.bones[pole_target_line]
                c = pbone.constraints.new ('STRETCH_TO')
                c.target = rig
                c.subtarget = pole_target

                set_bone_shape (bone_name=pole_target_line, shape='line', transform_bone=None, auto_scale_with_offset=None, manual_scale=1, shape_bone=None, keep_rot_when_radius_check=False, use_bone_size=True, shape_bone_parent_override=False)
                
                relevant_bones.append (pole_target_line)
                
                #pole target snap position bone 
                #when snapping ik to fk, the pole target copies the location of this bone
                #this bone is parented to fk bone 2 (forearm, shin)
                snap_target_pole = 'snap_'+pole_target
                duplicate_bone (source_name=pole_target, new_name=snap_target_pole, parent_name=fk_prefix+bone_names[1], roll_override=False, length_override=False)
                bone_settings (name=snap_target_pole, layer=ctrl_ik_extra_layer, group=ik_group, deform=False, lock_loc=True, lock_rot=True, lock_scale=True, type='ik')

                #IK LIMITS:
#                default = 1 if limit_ik_b2 else 0 

                #lock ik axes
                pbone = pbones[ik_prefix+b2]          
                for axis in axis_locks_string:
                    setattr (pbone, 'lock_ik_'+axis, limit_ik_b2)
#                    prop_to_drive_bone_attribute (prop_bone, bone_name=ik_prefix+b2, bone_type='PBONE', prop_name='limit_ik_'+module, attribute='lock_ik_'+axis, prop_min=0, prop_max=1, prop_default=default, description='', expression='v1')
                    
                    
                #limit rot
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[ik_prefix+b2]
                if b2_bend_axis == 'X':
                    pbone.ik_min_x = b2_min
                elif b2_bend_axis == '-X':
                    pbone.ik_max_x = b2_max                    

                setattr (pbone, 'use_ik_limit_'+bend_axis, limit_ik_b2)
#                prop_to_drive_bone_attribute (prop_bone, bone_name=ik_prefix+b2, bone_type='PBONE', prop_name='limit_ik_'+module, attribute='use_ik_limit_'+bend_axis, prop_min=0, prop_max=1, prop_default=default, description='', expression='v1')

                    
                #BIND RIG TO IK RIG constraints
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones

                for index, name in enumerate(bone_names):
                    c = pbones[name].constraints.new ('COPY_ROTATION')
                    c.name = 'bind_to_ik_1'
                    c.target = rig
                    if create_ik_twist_bones == True:
                        if index == 0 or index == 1:
                            c.subtarget = ik_prefix + 'twist_' + name
                        else:
                            c.subtarget = ik_prefix + name
                    else:
                        c.subtarget = ik_prefix + name
                    c.mute = True
                    
                #BIND RIG TO (0:fk, 1:ik, 2:bind)
                for name in bone_names:
                    prop_to_drive_constraint (prop_bone, bone_name=name, constraint_name='bind_to_fk_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ik, 2:bind', expression='1 - (v1 < 1)')
                    prop_to_drive_constraint (prop_bone, bone_name=name, constraint_name='bind_to_ik_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ik, 2:bind', expression='1 - (v1 > 0 and v1 < 2)')
                
                #visibility
                bone_visibility (prop_bone, module, relevant_bones, ik_ctrl='ik')    

                #set module name on relevant bones (used by the 'N-panel' interface)
                set_module_on_relevant_bones (relevant_bones, module)


                #prop that stores bone names for fk/ik snapping
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[prop_bone]

                stem = 'snapinfo_3bonelimb_'
                index_is_free = False
                index = 0
                while index_is_free is False:
                    for n in range (0, 1000):
                        prop_name_candidate = stem + str(index + n)
                        if prop_name_candidate not in pbone:
                            pbone[prop_name_candidate] = [fk_prefix+b1, fk_prefix+b2, fk_prefix+b3, ik_prefix+b1, ik_prefix+b2, ik_prefix+b3, pole_target, str(pole_target_distance), snap_target_pole, fk_prefix+b3, ik_prefix+b3, 'None']
                            
                        #stop for loop
                        break
                    #stop while_loop
                    index_is_free = True

            ########################################################################################################
            ########################################################################################################

            #ISOLATE ROTATION

            def isolate_rotation (module, parent_bone, first_bone):    
                #should only be used to affect FK BONES    
                prop_bone = create_mudule_prop_bone (module)
                
                #delete parent relationship tween parent_bone and first bone
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                #create intermediate bones
                #one that's parented to 'parent bone'
                first_intermeidate_bone = 'isolate_rot_'+first_bone+'_parent'
                ebone = ebones.new (name=first_intermeidate_bone)
                ebone.head = ebones[first_bone].head
                ebone.tail = ebone.head + Vector ((0, 0, general_bone_size))
                ebones = rig.data.edit_bones
                ebone.parent = ebones[parent_bone]
                bone_settings (name=first_intermeidate_bone, layer=fk_extra_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)

                #one that becomes the parent of 'first_bone'
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                second_intermeidate_bone = 'isolate_rot_'+first_bone+'_child'
                ebone = ebones.new (name=second_intermeidate_bone)
                ebone.head = ebones[first_bone].head
                ebone.tail = ebone.head + Vector ((0, 0, general_bone_size))
                ebones = rig.data.edit_bones
                ebone.parent = ebones['root_extract']
                bone_settings (name=second_intermeidate_bone, layer=fk_extra_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)

                #parent first bone to this bone
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ebones[first_bone].parent = ebones[second_intermeidate_bone]
                
                #constraint second itermediate bone to the first one
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                cs = pbones[second_intermeidate_bone].constraints

                c = cs.new ('COPY_LOCATION')
                c.target = rig
                c.subtarget = first_intermeidate_bone
                
                c = cs.new ('COPY_SCALE')
                c.target = rig
                c.subtarget = first_intermeidate_bone
                
                c = cs.new ('COPY_ROTATION')
                c.name = 'isolate_rot_1'
                c.target = rig
                c.subtarget = first_intermeidate_bone
                
                prop_to_drive_constraint (first_bone, bone_name=second_intermeidate_bone, constraint_name='isolate_rot_1', prop_name='fixate_'+first_bone, attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=0.0, description='', expression='1-v1')


            def get_parent (first_bone):
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                parent = ebones[first_bone].parent.name
                return parent

            ########################################################################################################
            ########################################################################################################

            #BONE GROUPS
                
            bpy.ops.object.mode_set (mode='POSE')
            bgroups = rig.pose.bone_groups

            bg = bgroups.new (name = base_group)
            bg.color_set = 'THEME04'

            bg = bgroups.new (name = fk_group)
            bg.color_set = 'THEME06'

            bg = bgroups.new (name = central_ik_group)
            bg.color_set = 'THEME10'

            bg = bgroups.new (name = left_ik_group)
            bg.color_set = 'THEME01'

            bg = bgroups.new (name = right_ik_group)
            bg.color_set = 'THEME03'

            bg = bgroups.new (name = twist_group)
            bg.color_set = 'THEME07'

            bg = bgroups.new (name = spring_group)
            bg.color_set = 'THEME14'

            bg = bgroups.new (name = ik_prop_group)
            bg.color_set = 'THEME10'

            bg = bgroups.new (name = face_group)
            bg.color_set = 'THEME08'
            
            bg = bgroups.new (name = target_group)
            bg.color_set = 'THEME09'
               

            ########################################################################################################
            ########################################################################################################

            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #MODULES START HERE
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


            #PREPARE

            def prepare (layer):
                
                #remove all drivers
                rig.animation_data_clear ()
                rig.data.animation_data_clear ()

                #GYAZ stamp
                rig.data['GYAZ_rig'] = True
                
                bpy.ops.object.mode_set (mode='OBJECT')
                for bone in rig.data.bones:
                    set_bone_only_layer (bone.name, 23)
                    
                #make all bone layers visible
                for n in range (0, 32):
                    rig.data.layers[n] = True
                    
                #visualization
                rig.display_type = 'WIRE'
                rig.data.display_type = 'OCTAHEDRAL'
                
                rig.data.show_names = False
                rig.data.show_axes = False
                rig.data.show_bone_custom_shapes = True
                rig.data.show_group_colors = True
                rig.show_in_front = False
                rig.data.use_deform_delay = False
                
                create_mudule_prop_bone ('general')
                
                #delete constraints from all bones, should any exist
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                for pbone in pbones:
                    cs = pbone.constraints
                    if len (cs) > 0:
                        for c in cs:
                            cs.remove (c)
                            
                #for interface
                rig.data["switch_when_snap"] = 1
                rig.data["show_switch"] = 0
                rig.data["show_visible"] = 0
                
                rig.data['_RNA_UI']['switch_when_snap'] = {'min': 0, 'max': 1, 'soft_min': 0, 'soft_max': 1}
                rig.data['_RNA_UI']['show_switch'] = {'min': 0, 'max': 1, 'soft_min': 0, 'soft_max': 1}
                rig.data['_RNA_UI']['show_visible'] = {'min': 0, 'max': 1, 'soft_min': 0, 'soft_max': 1}
                
                #lock mesh transforms
                for child in rig.children:
                    if child.type == 'MESH':
                        child.lock_location[0] = True
                        child.lock_location[1] = True
                        child.lock_location[2] = True
                        child.lock_rotation[0] = True
                        child.lock_rotation[1] = True
                        child.lock_rotation[2] = True
                        child.lock_scale[0] = True
                        child.lock_scale[1] = True
                        child.lock_scale[2] = True
                

            #FINALIZE

            def finalize (visible_layers):
                
                #Add prop to toggle low-level rig's visibility
                prop_bone = 'module_props__general'
                prop_to_drive_layer (prop_bone, layer_index=base_layer, prop_name='visible_base_bones', prop_min=0, prop_max=1, prop_default=0, description='', expression='v1')
                prop_to_drive_layer (prop_bone, layer_index=twist_layer, prop_name='visible_twist_bones', prop_min=0, prop_max=1, prop_default=0, description='', expression='v1')
                prop_to_drive_layer (prop_bone, layer_index=spring_layer, prop_name='visible_spring_bones', prop_min=0, prop_max=1, prop_default=0, description='', expression='v1')
                prop_to_drive_layer (prop_bone, layer_index=face_layer, prop_name='visible_face_bones', prop_min=0, prop_max=1, prop_default=1, description='', expression='v1')    
                prop_to_drive_layer (prop_bone, layer_index=face_extra_layer, prop_name='visible_extra_face_bones', prop_min=0, prop_max=1, prop_default=0, description='', expression='v1')    
                prop_to_drive_layer (prop_bone, layer_index=root_layer, prop_name='visible_root_bone', prop_min=0, prop_max=1, prop_default=0, description='', expression='v1')
                prop_to_drive_layer (prop_bone, layer_index=ik_prop_layer, prop_name='visible_prop_bones', prop_min=0, prop_max=1, prop_default=0, description='', expression='v1')    
                prop_to_drive_layer (prop_bone, layer_index=twist_target_layer, prop_name='visible_twist_targets', prop_min=0, prop_max=1, prop_default=0, description='', expression='v1')    
                
                visible_layers = set (visible_layers)
                visible_layers = visible_layers.union ( {fk_layer, ctrl_ik_layer, touch_layer} )
                all_layers = set (n for n in range (32))
                hidden_layers = all_layers - visible_layers
                    
                for n in visible_layers:
                    rig.data.layers[n] = True
                    
                for n in hidden_layers:
                    rig.data.layers[n] = False
                    
                merged_character_mesh.user_clear ()
                bpy.data.objects.remove (merged_character_mesh)
                    
                rig.show_in_front = False
                
                bpy.ops.object.mode_set (mode='POSE')

                rig['snap_start'] = 1
                rig['snap_end'] = 250
                
                if "_RNA_UI" not in rig:
                    rig["_RNA_UI"] = {}

                rig["_RNA_UI"]['snap_start'] = {"min":0}
                rig["_RNA_UI"]['snap_end'] = {"min":0}
                
                list = rig.data['snappable_modules']
                list.sort ()
                rig.data['snappable_modules'] = list
                
                pbones = rig.pose.bones
                for pbone in pbones:
                    prop_list = pbone.keys ()
                    prop_list.sort ()
                    
                if 'temp' in rig.data:
                    del rig.data['temp']
                
                # save default values of all props
                prop_info = []
                
                for pbone in pbones:
                    for key in pbone.keys():
                        if key != '_RNA_UI':
                            info = {'bone': pbone.name, 'key': key, 'value': pbone[key]}
                            prop_info.append (info)
                        
                rig.data['prop_defaults'] = prop_info

                #rig has been generated successfuly
                rig.data['GYAZ_rig_generated'] = 1

                
            ########################################################################################################
            ########################################################################################################

            #ROOT BONES

            def root (size, root_extract_size):

                name = 'root'
                bpy.ops.object.mode_set (mode='EDIT')
                ebone = rig.data.edit_bones.new (name = name)
                ebone.head = Vector ((0, 0, 0))
                ebone.tail = ebone.head + Vector ((0, size, 0))                
                #format
                bone_settings (name, layer=root_layer, group=None, deform=False, lock_loc=False, lock_rot=False, lock_scale=True, type=None)
                set_bone_shape ('root', shape='master', transform_bone=None, auto_scale_with_offset=None, manual_scale=1, shape_bone=None, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)                
                
                name = 'root_extract'
                bpy.ops.object.mode_set (mode='EDIT')
                ebone = rig.data.edit_bones.new (name = name)
                ebone.head = Vector ((0, 0, 0))
                ebone.tail = ebone.head + Vector ((0, root_extract_size, 0))
                ebone.parent = rig.data.edit_bones['root']
                #format
                bone_settings (name, layer=misc_layer, group=None, deform=False, lock_loc=True, lock_rot=True, lock_scale=True, type=None)
                           

            #def extra_root_bone (name, size):

            #    bpy.ops.object.mode_set (mode='EDIT')
            #    
            #    ebone = rig.data.edit_bones.new (name = name)
            #    ebone.head = Vector ((0, 0, 0))
            #    ebone.tail = ebone.head + Vector ((0, size, 0))
            #    ebone.parent = rig.data.edit_bones['root']
            #    
            #    #format
            #    bone_settings (name, layer=extra_root_layer, group=None, deform=False, lock_loc=False, lock_rot=False, lock_scale=True, type=None)
                

            def ik_prop_bone (name, source_bone, parent):
                
                duplicate_bone (source_name=source_bone, new_name=name, parent_name=parent, roll_override=False, length_override=False)
                bone_settings (name, layer=ik_prop_layer, group=ik_prop_group, deform=False, lock_loc=False, lock_rot=False, lock_scale=True, type='ik_prop')
                set_bone_shape (name, shape='cube_outer', transform_bone=None, auto_scale_with_offset=auto_bone_shape_scale_offset_limb, manual_scale=1, shape_bone=None, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)    
                
                
            ########################################################################################################
            ########################################################################################################

            #BIPED TORSO

            def biped_torso (module, chain, first_parent):
                
                #chain length should be exactly 4
                
                #bones that should be used for animation
                relevant_bones = []
                
                #bone that holds all properties of the module
                prop_bone = create_mudule_prop_bone (module)
                
                #LOW-LEVEL BONES
                set_parent_chain (chain, first_parent=first_parent)

                #format bones
                for index, name in enumerate(chain):
                    if index == 0:
                        lock_loc = False
                    else:
                        lock_loc = True
                    bone_settings (name=name, layer=base_layer, group='base', deform=True, lock_loc=lock_loc, lock_rot=False, lock_scale=True, type='base')
                        
                    relevant_bones.append (name)
                    
                #FK BONES
                for index, name in enumerate(chain):
                    if index == 0:
                        lock_loc = False
                        parent = first_parent
                        shape = 'torso_2'
                        shape_bone = 'UP'
                    else:
                        lock_loc = True
                        parent = fk_prefix + chain[index-1]
                        shape = 'inner_circle'
                        shape_bone = None
                        
                    duplicate_bone (source_name=name, new_name=fk_prefix+name, parent_name=parent, roll_override=False, length_override=None)
                    bone_settings (name=fk_prefix+name, layer=fk_layer, group='fk', deform=False, lock_loc=lock_loc, lock_rot=False, lock_scale=True, type='fk')
                    set_bone_shape (bone_name=fk_prefix+name, shape=shape, transform_bone=None, auto_scale_with_offset=auto_bone_shape_scale_offset, manual_scale=1, shape_bone=shape_bone, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)           
                    
                    relevant_bones.append (fk_prefix+name)
                
  
                #LOW-LEVEL TO FK RIG CONSTRAINTS
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                for index, name in enumerate(chain):    
                    pbone = pbones[name]
                    cs = pbone.constraints
                    
                    c = cs.new ('COPY_ROTATION')
                    c.name = 'bind_to_fk_1'
                    c.target = rig
                    c.subtarget = fk_prefix + name  
                    c.mute = True
                        
                    if index == 0:
                        c = cs.new ('COPY_LOCATION')
                        c.name = 'bind_to_fk_2'
                        c.target = rig
                        c.subtarget = fk_prefix + name  
                        c.head_tail = 0
                        c.mute = True
                
                #IK BONES
                #create torso bone
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ctrl_torso = 'ctrl_torso'
                ebone = ebones.new (name = ctrl_torso)
                ebone.head = ebones[chain[0]].tail
                
                #get hips length
                length = get_distance (ebones[chain[0]].head, ebones[chain[0]].tail)
                
                ebone.tail = ebone.head + Vector ((0, length, 0))
                ebone.parent = ebones[first_parent]
                
                #format torso bone
                bone_settings (name=ctrl_torso, layer=ctrl_ik_layer, group=central_ik_group, deform=False, lock_loc=False, lock_rot=False, lock_scale=True, type='ctrl')
                
                relevant_bones.append (ctrl_torso)
                
                #create control bones    
                def spine_control (ctrl_name, length_multiplier, parent, is_on_main_layer, group):
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    ctrl_spine_name = 'ctrl_' + ctrl_name
                    ebone = ebones.new (name = ctrl_spine_name)
                    ebone.head = ebones[chain[0]].tail
                    ebone.tail = ebone.head + Vector ((0, 0, length * length_multiplier))
                    ebone.use_connect = False
                    ebone.parent = ebones[parent]
                    if is_on_main_layer == True:
                        layer=ctrl_ik_layer
                    else:
                        layer=ctrl_ik_extra_layer
                    bone_settings (name=ctrl_spine_name, layer=layer, group=group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type='ctrl')
                    return (ctrl_spine_name)
                
                ctrl_hips = spine_control ('hips', 1, ctrl_torso, True, group=central_ik_group)
                ctrl_waist_parent = spine_control ('waist_parent', 2.5, ctrl_hips, False, group=None)
                ctrl_waist = spine_control ('waist', 2, ctrl_waist_parent, True, group=central_ik_group)
                ctrl_chest = spine_control ('chest', 3, ctrl_torso, True, group=central_ik_group)
                
                relevant_bones.append (ctrl_hips)
                relevant_bones.append (ctrl_waist)
                relevant_bones.append (ctrl_chest)
                
                #ctrl_waist_parent constraints
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[ctrl_waist_parent]
                cs = pbone.constraints
                
                #constraints    
                c = cs.new ('COPY_ROTATION')
                c.name = 'copy ' + ctrl_chest
                c.target = rig
                c.subtarget = ctrl_chest
                c.influence = ctrl_waist__copy__ctrl_chest
                
                prop_to_drive_constraint (ctrl_waist, bone_name=ctrl_waist_parent, constraint_name=c.name, prop_name='ctrl_waist_copy_chest', attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=ctrl_waist__copy__ctrl_chest, description='', expression='v1')
                
                c = cs.new ('COPY_ROTATION')
                c.name = 'copy ' + ctrl_hips
                c.target = rig
                c.subtarget = ctrl_hips
                c.influence = ctrl_waist__copy__ctrl_hips
                
                prop_to_drive_constraint (ctrl_waist, bone_name=ctrl_waist_parent, constraint_name=c.name, prop_name='ctrl_waist_copy_hips', attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=ctrl_waist__copy__ctrl_hips, description='', expression='v1')
                
                
                for index, name in enumerate(chain):        
                    #create distributor bone
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    dist_bone_name = ik_prefix + name + '_dist'
                    ebone = ebones.new (name = dist_bone_name)
                    ebone.head = ebones[name].head
                    ebone.tail = ebone.head + Vector((0, 0, length/2))
                    ebone.use_connect = False
                    if index == 0:
                        parent = ctrl_torso
                    else:
                        parent = ik_prefix + 'fwd_' + chain[index-1]
                    ebone.parent = ebones[parent]
                    
                    #format distributor bone
                    bone_settings (name=dist_bone_name, layer=ctrl_ik_extra_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                    
                    #create ik fwd bone
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    ik_bone_name = ik_prefix + 'fwd_' + name
                    if index == 0:
                        bone_roll = ebones[name].roll + radians (180)
                    else:
                        bone_roll = ebones[name].roll
                    duplicate_bone (source_name=name, new_name=ik_bone_name, parent_name=dist_bone_name, roll_override=bone_roll, length_override=None)
                    
                    #format ik bone
                    bone_settings (name=ik_bone_name, layer=ctrl_ik_extra_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                    
                    
                #reverse hips
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ik_hips_name = ik_prefix + 'fwd_' + chain[0]
                ebones[ik_hips_name].head = ebones[chain[0]].tail
                ebones[ik_hips_name].tail = ebones[chain[0]].head
                #adjust hips distributor
                ik_hips_distributor_name = ik_prefix + chain[0] + '_dist'
                ebones[ik_hips_distributor_name].head = ebones[chain[0]].tail
                ebones[ik_hips_distributor_name].tail = ebones[ik_hips_distributor_name].head + Vector ((0, 0, length/3))
                #reset parents
                ebones[ik_hips_distributor_name].parent = ebones[ctrl_torso]
                ebones[ik_prefix + chain[1] + '_dist'].parent = ebones[ctrl_torso]
                
                
                #distributor constraints
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                
                def simple_spine_constraint (chain_index, ctrl_bone_name):
                    pbone = pbones[ik_prefix + chain[chain_index] + '_dist']
                    cs = pbone.constraints
                    c = cs.new ('COPY_ROTATION')
                    c.name = 'copy ' + ctrl_bone_name
                    c.target = rig
                    c.subtarget = ctrl_bone_name
                    c.influence = 1
                
                #0, 1, 3
                simple_spine_constraint (0, ctrl_hips)
                simple_spine_constraint (1, ctrl_waist)
                simple_spine_constraint (3, ctrl_chest)
                
                #2
                pbone = pbones[ik_prefix + chain[2] + '_dist']
                cs = pbone.constraints
                
                c = cs.new ('COPY_ROTATION')
                c.name = 'copy ' + ctrl_waist
                c.target = rig
                c.subtarget = ctrl_waist
                c.influence = ik_spine_2__copy__ctrl_waist
                
                #prop_to_drive_constraint (ctrl_waist, bone_name=pbone.name, constraint_name=c.name, prop_name='ctrl_spine_2_copy_waist', attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=ik_spine_2__copy__ctrl_waist, description='', expression='v1')
                
                
                c = cs.new ('COPY_ROTATION')
                c.name = 'copy ' + ctrl_chest
                c.target = rig
                c.subtarget = ctrl_chest
                c.influence = ik_spine_2__copy__ctrl_waist
                
                prop_to_drive_constraint (ctrl_chest, bone_name=pbone.name, constraint_name=c.name, prop_name='ctrl_spine_2_copy_chest', attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=ik_spine_2__copy__ctrl_waist, description='', expression='v1')           
                        
                #create ik bones (that will slide on reverse bones)
                for index, name in enumerate(chain):
                    if index == 0:
                        parent_name = ctrl_torso
                    else:
                        parent_name = ik_prefix + chain[index-1]
                    duplicate_bone (source_name=name, new_name=ik_prefix+name, parent_name=parent_name, roll_override=False, length_override=None)
                    bone_settings (name=ik_prefix+name, layer=ctrl_ik_extra_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                    
                    if index != 0:

                        #constrain it to ik_fwd bones
                        bpy.ops.object.mode_set (mode='POSE')
                        bone_name = ik_prefix + name
                        pbone = rig.pose.bones[bone_name]
                        cs = pbone.constraints
                        
                        c = cs.new ('COPY_ROTATION')
                        c.target = rig
                        c.subtarget = ik_prefix + 'fwd_' + name
                                    
                #reverse hips
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ik_hips_name = ik_prefix + chain[0]
                ebones[ik_hips_name].head = ebones[chain[0]].tail
                ebones[ik_hips_name].tail = ebones[chain[0]].head
                ebones[ik_hips_name].roll = 0 + radians (180)
                ebones[ik_prefix+chain[1]].parent = None
                ebones[ik_hips_name].parent = ebones[ik_prefix+chain[1]]
                ebones[ik_prefix+chain[1]].parent = ebones[ctrl_torso]
                
                #ik_hips copies ik_fwd_hips' rot
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[ik_hips_name]
                cs = pbone.constraints
                
                c = cs.new ('COPY_ROTATION')
                c.target = rig
                c.subtarget = ik_prefix + 'fwd_' + chain[0]         
                       
                        
                #PIVOT SLIDER
                #reverse spine chain from above hips
                for index, name in enumerate(chain):
                    if index > 0:
                        parent_name = ik_prefix + 'fwd_' + name
                        rev_bone_name = ik_prefix + 'rev_' + name
                        duplicate_bone (source_name=name, new_name=rev_bone_name, parent_name=parent_name, roll_override=False, length_override=None)            
                        mirror_bone_to_point (bone_name=rev_bone_name, point=ebones[ctrl_torso].head)
                        bone_settings (name=rev_bone_name, layer=ctrl_ik_extra_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                        
                        #stick rev bones together
                        if index > 1:
                            bpy.ops.object.mode_set (mode='POSE')
                            pbone = rig.pose.bones[rev_bone_name]
                            cs = pbone.constraints
                            c = cs.new ('COPY_LOCATION')
                            c.target = rig
                            c.subtarget = ik_prefix + 'rev_' + chain[index-1]
                            c.head_tail = 1
                            
                #constraints
                bpy.ops.object.mode_set (mode='POSE')
                bone_name = ik_prefix + chain[1]
                pbone = rig.pose.bones[bone_name]
                cs = pbone.constraints
                
                for index, name in enumerate(chain):
                    if index > 0:
                        c = cs.new ('COPY_LOCATION')
                        c.name = 'pivot_slide_' + str(index)
                        c.target = rig
                        c.subtarget = ik_prefix + 'rev_' + name
                        c.head_tail = 1
                        c.influence = 0
                        
                        #constraint driven by prop
                        prop_to_drive_constraint (ctrl_torso, bone_name=bone_name, constraint_name=c.name, prop_name='ctrl_spine_pivot_slide', attribute='influence', prop_min=0.25, prop_max=1.0, prop_default=0.25, description='', expression='(v1 - 0.25 * ' + str(index) + ') * 4' )

                #control bone shapes
                set_bone_shape (bone_name=ctrl_hips, shape='inner_circle', transform_bone=ik_prefix+chain[1], auto_scale_with_offset=auto_bone_shape_scale_offset, manual_scale=False, shape_bone=None, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                set_bone_shape (bone_name=ctrl_waist, shape='inner_circle', transform_bone=ik_prefix+chain[2], auto_scale_with_offset=auto_bone_shape_scale_offset, manual_scale=False, shape_bone=None, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                set_bone_shape (bone_name=ctrl_chest, shape='inner_circle', transform_bone=ik_prefix+chain[3], auto_scale_with_offset=auto_bone_shape_scale_offset, manual_scale=False, shape_bone=None, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)

                #ctrl_torso shape
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[ctrl_hips]
                scale = pbone.custom_shape_scale
                set_bone_shape (bone_name=ctrl_torso, shape='torso', transform_bone=None, auto_scale_with_offset=None, manual_scale=scale, shape_bone=None, keep_rot_when_radius_check=True, use_bone_size=False, shape_bone_parent_override=False)


                #LOW-LEVEL TO IK RIG CONSTRAINTS
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                for index, name in enumerate(chain):    
                    pbone = pbones[name]
                    cs = pbone.constraints
                    if index > 0:
                        c = cs.new ('COPY_ROTATION')
                        c.name = 'bind_to_ik_1'
                        c.target = rig
                        c.subtarget = ik_prefix + name  
                        c.mute = True
                        
                    else:
                        c = cs.new ('COPY_LOCATION')
                        c.name = 'bind_to_ik_2'
                        c.target = rig
                        c.subtarget = ik_prefix + name  
                        c.head_tail = 1
                        c.mute = True
                        
                        c = cs.new ('TRACK_TO')
                        c.name = 'bind_to_ik_1'
                        c.target = rig
                        c.subtarget = ik_prefix + name  
                        c.track_axis = 'TRACK_Y'
                        c.head_tail = 0
                        c.use_target_z = True
                        c.mute = True

                 
                #BIND TO (0: FK, 1: IK, 2:BIND)
                for index, name in enumerate(chain):
                    if index == 0:
                        constraint_count = 2
                    else:
                        constraint_count = 1
                    for n in range (1, constraint_count+1):
                        n = str(n)
                        prop_to_drive_constraint (prop_bone, bone_name=chain[index], constraint_name='bind_to_fk_'+n, prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ctrl, 2:base', expression='1 - (v1 < 1)')
                        prop_to_drive_constraint (prop_bone, bone_name=chain[index], constraint_name='bind_to_ik_'+n, prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ctrl, 2:base', expression='1 - (v1 > 0 and v1 < 2)')
                        
                bone_visibility (prop_bone, module, relevant_bones, ik_ctrl='ctrl')
                
                #set module name on relevant bones (used by the 'N-panel' interface)
                set_module_on_relevant_bones (relevant_bones, module)
                
                #snap_info
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                pbone = pbones[prop_bone]
                pbone['snapinfo_simpletobase_0'] = chain
                
                pbone['snap_n_key__should_snap'] = 0
                
                sm = 'snappable_modules'
                if sm in rig.data:
                    rig.data[sm] += [module]
                else:
                    rig.data[sm] = [module]
                 
            ########################################################################################################
            ########################################################################################################

            #NECK

            def short_neck (module, bone_name, distributor_parent, ik_rot_bone, ik_loc_bone):
                
                use_twist = generate__twist_neck
                
                #bones that should be used for animation
                relevant_bones = []
                
                #bone that holds all properties of the module
                prop_bone = create_mudule_prop_bone (module)
                
                #set parent
                parent = get_parent (bone_name)
                
                #LOW-LEVEL BONES
                
                neck = bone_name
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ebones[neck].parent = ebones[parent]
                bone_settings (name=neck, layer=base_layer, group='base', deform=True, lock_loc=True, lock_rot=False, lock_scale=True, type='base')    
                relevant_bones.append (neck)
                
                #_____________________________________________________________________________________________________
                
                #FK BONES

                bpy.ops.object.mode_set (mode='EDIT')
                name = fk_prefix+neck
                ebone = rig.data.edit_bones.new (name=name)
                ebones = rig.data.edit_bones
                ebone.head = ebones[neck].head
                ebone.tail = ebones[neck].tail
                ebone.roll = ebones[neck].roll
                ebone.parent = ebones[fk_prefix+parent]

                bone_settings (name=name, layer=fk_layer, group=fk_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type='fk')
                set_bone_shape (bone_name=name, shape='inner_circle', transform_bone=None, auto_scale_with_offset=auto_bone_shape_scale_offset, manual_scale=1, shape_bone='CENTER', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False) 
                
                relevant_bones.append (name)                
                
                #LOW-LEVEL TO FK RIG constraint
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[neck]
                cs = pbone.constraints
                
                c = cs.new ('COPY_ROTATION')
                c.name = 'bind_to_fk_1'
                c.target = rig
                c.subtarget = fk_prefix + neck
                c.mute = True
                
                #_____________________________________________________________________________________________________
                
                #TWIST BONES
                
                if use_twist == True:
                
                    twist_bones = create_twist_bones (source_bone=neck, count=1, upper_or_lower_limb='lower', twist_target_distance=0, twist_target_parent='', lock_xz_rot=False, end_affector=None, source_bone_bend_axis='')
                    
                    name = twist_bones[0]
                    
                    #adjust tail
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    ebone = ebones [name]
                    ebone.tail = mean (ebone.head, ebone.tail)
                    
                    #neck_mediator
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebone = rig.data.edit_bones.new (name='neck_mediator')
                    ebones = rig.data.edit_bones
                    ebone.head = ebones[neck].head
                    ebone.tail = ebones[neck].tail
                    ebone.roll = ebones[neck].roll
                    ebone.parent = ebones[neck].parent
                    
                    bone_settings (name=ebone.name, layer=misc_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                 
                    #constraints (neck_twist)
                    pbone = rig.pose.bones[name]
                    
                    c = pbone.constraints.new ('TRACK_TO')
                    c.target = rig
                    c.subtarget = 'head'
                    c.head_tail = 0
                    c.track_axis = 'TRACK_Y'
                    c.up_axis = 'UP_Z'
                    c.use_target_z = True
                    c.target_space = 'POSE'
                    c.owner_space = 'POSE'
                    c.influence = neck_twist_track_to_head
                    
                    c = pbone.constraints.new ('LIMIT_ROTATION')
                    c.owner_space = 'LOCAL'
                    c.use_limit_x = True
                    c.use_limit_y = False
                    c.use_limit_z = True
                    c.min_x = 0
                    c.max_x = 0
                    c.min_z = 0
                    c.max_z = 0
                    c.use_transform_limit = True
                    c.influence = 1
                    
                    c = pbone.constraints.new ('COPY_ROTATION')
                    c.target = rig
                    c.subtarget = 'neck_mediator'
                    c.use_x = True
                    c.use_y = True
                    c.use_z = True
                    c.invert_x = False
                    c.invert_y = False
                    c.invert_z = False
                    c.use_offset = False
                    c.target_space = 'POSE'
                    c.owner_space = 'POSE'
                    c.influence = neck_twist_rotate_back     
                    
                    c = pbone.constraints.new ('LIMIT_ROTATION')
                    c.owner_space = 'LOCAL'
                    c.influence = 1
                    c.use_limit_x = False
                    c.use_limit_y = False
                    c.use_limit_z = True
                    c.min_x = 0
                    c.max_x = 0
                    c.min_y = 0
                    c.max_y = 0
                    c.min_z = radians (neck_twist_min_y)
                    c.max_z = 0
                    c.use_transform_limit = True


                #_____________________________________________________________________________________________________
                
                #IK BONES  
                   
                bpy.ops.object.mode_set (mode='EDIT')
                #distributor
                distributor = 'ctrl_'+neck
                ebone = rig.data.edit_bones.new (name=distributor)
                ebones = rig.data.edit_bones
                ebone.head = ebones[neck].head
                ebone.tail = ebone.head + Vector ((0, 0, 0.05))
                ebone.parent = ebones[distributor_parent]   
                
                #bone
                name = ik_prefix+neck
                ebone = rig.data.edit_bones.new (name=name)
                ebones = rig.data.edit_bones
                ebone.head = ebones[neck].head
                ebone.tail = ebones[neck].tail
                ebone.roll = ebones[neck].roll
                ebone.parent = ebones[distributor]
                
                #costraints
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[distributor]  
                  
                c = pbone.constraints.new ('COPY_ROTATION')
                c.name = 'inherit_rot'
                c.target = rig
                c.subtarget = ik_rot_bone
                c.use_x = True
                c.use_y = True
                c.use_z = True
                c.invert_x = False
                c.invert_y = False
                c.invert_z = False
                c.use_offset = True
                c.target_space = 'LOCAL'
                c.owner_space = 'LOCAL'
                c.influence = fixate_ctrl_neck
                
                c = pbone.constraints.new ('COPY_LOCATION')
                c.target = rig
                c.subtarget = ik_loc_bone
                c.head_tail = 1
                c.use_x = True
                c.use_y = True
                c.use_z = True
                c.invert_x = False
                c.invert_y = False
                c.invert_z = False
                c.use_offset = False
                c.target_space = 'WORLD'
                c.owner_space = 'WORLD'
                c.influence = 1
                
                #bone settings
                set_bone_shape (distributor, shape='inner_circle', transform_bone=ik_prefix+neck, auto_scale_with_offset=auto_bone_shape_scale_offset, manual_scale=1, shape_bone='CENTER', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                bone_settings (name=name, layer=ctrl_ik_extra_layer, group=None, deform=True, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                bone_settings (name=distributor, layer=ctrl_ik_layer, group=central_ik_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)

                prop_to_drive_constraint (distributor, bone_name=distributor, constraint_name='inherit_rot', prop_name='fixate_ctrl_'+neck, attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=fixate_ctrl_neck, description='', expression='1-v1')
                
                #LOW-LEVEL TO IK RIG constraint
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[neck]
                cs = pbone.constraints
                
                c = cs.new ('COPY_ROTATION')
                c.name = 'bind_to_ik_1'
                c.target = rig
                c.subtarget = ik_prefix + neck
                c.mute = True
                
                #BIND TO (0: FK, 1: IK, 2:BIND)
                prop_to_drive_constraint (prop_bone, bone_name=neck, constraint_name='bind_to_fk_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ctrl, 2:base', expression='1 - (v1 < 1)')
                prop_to_drive_constraint (prop_bone, bone_name=neck, constraint_name='bind_to_ik_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ctrl, 2:base', expression='1 - (v1 > 0 and v1 < 2)')           
                
                relevant_bones.append ('ctrl_'+neck)
                set_bone_type (name='ctrl_'+neck, type='ctrl')
                
                bone_visibility (prop_bone, module, relevant_bones, ik_ctrl='ctrl')
                    
                #set module name on relevant bones (used by the 'N-panel' interface)
                set_module_on_relevant_bones (relevant_bones, module)
                
                #snap_info
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                pbone = pbones[prop_bone]
                si = 'snapinfo_simpletobase_0'
                if si in pbone:
                    pbone[si]= pbone[si] + [neck]
                
                
            ########################################################################################################
            ########################################################################################################

            #HEAD

            def head (module, bone_name, ik_rot_bone, ik_loc_bone, distributor_parent):
                
                #bones that should be used for animation
                relevant_bones = []
                
                #bone that holds all properties of the module
                prop_bone = create_mudule_prop_bone (module)
                
                #set parent
                parent = get_parent (bone_name)
                
                #LOW-LEVEL BONES
                
                head = bone_name
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ebones[head].parent = ebones[parent]
                ebones[head].parent = ebones[parent]
                bone_settings (name=head, layer=base_layer, group='base', deform=True, lock_loc=True, lock_rot=False, lock_scale=True, type='base')
                relevant_bones.append (head)
                
                #_____________________________________________________________________________________________________    
                
                #FK BONES

                bpy.ops.object.mode_set (mode='EDIT')
                name = fk_prefix+head
                ebone = rig.data.edit_bones.new (name=name)
                ebones = rig.data.edit_bones
                ebone.head = ebones[head].head
                ebone.tail = ebones[head].tail
                ebone.roll = ebones[head].roll
                ebone.parent = ebones[fk_prefix+parent]

                bone_settings (name=name, layer=fk_layer, group=fk_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type='fk')
                set_bone_shape (bone_name=name, shape='inner_circle', transform_bone=None, auto_scale_with_offset=auto_bone_shape_scale_offset, manual_scale=1, shape_bone='CENTER', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False) 
                
                relevant_bones.append (name)
                
                #LOW-LEVEL TO FK RIG constraint
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[head]
                cs = pbone.constraints
                
                c = cs.new ('COPY_ROTATION')
                c.name = 'bind_to_fk_1'
                c.target = rig
                c.subtarget = fk_prefix + head
                c.mute = True    

                #_____________________________________________________________________________________________________

                #IK BONES
                
                bpy.ops.object.mode_set (mode='EDIT')
                #distributor
                distributor = 'ctrl_'+head
                ebone = rig.data.edit_bones.new (name=distributor)
                ebones = rig.data.edit_bones
                ebone.head = ebones[head].head
                ebone.tail = ebone.head + Vector ((0, 0, 0.05))
                ebone.parent = ebones[distributor_parent]   
                
                #bone
                name = ik_prefix+head
                ebone = rig.data.edit_bones.new (name=name)
                ebones = rig.data.edit_bones
                ebone.head = ebones[head].head
                ebone.tail = ebones[head].tail
                ebone.roll = ebones[head].roll
                ebone.parent = ebones[distributor]
                
                #costraints
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[distributor]  
                  
                c = pbone.constraints.new ('COPY_ROTATION')
                c.name = 'inherit_rot'
                c.target = rig
                c.subtarget = ik_rot_bone
                c.use_x = True
                c.use_y = True
                c.use_z = True
                c.invert_x = False
                c.invert_y = False
                c.invert_z = False
                c.use_offset = True
                c.target_space = 'LOCAL'
                c.owner_space = 'LOCAL'
                c.influence = fixate_ctrl_head
                
                c = pbone.constraints.new ('COPY_LOCATION')
                c.target = rig
                c.subtarget = ik_loc_bone
                c.head_tail = 1
                c.use_x = True
                c.use_y = True
                c.use_z = True
                c.invert_x = False
                c.invert_y = False
                c.invert_z = False
                c.use_offset = False
                c.target_space = 'WORLD'
                c.owner_space = 'WORLD'
                c.influence = 1    

                #bone settings
                set_bone_shape (distributor, shape='inner_circle', transform_bone=ik_prefix+head, auto_scale_with_offset=auto_bone_shape_scale_offset, manual_scale=1, shape_bone='CENTER', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                bone_settings (name=distributor, layer=ctrl_ik_layer, group=central_ik_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                bone_settings (name=name, layer=ctrl_ik_extra_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                
                prop_to_drive_constraint (distributor, bone_name=distributor, constraint_name='inherit_rot', prop_name='fixate_ctrl_'+head, attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=fixate_ctrl_head, description='', expression='1-v1')
               
                #LOW-LEVEL TO IK RIG constraint
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[head]
                cs = pbone.constraints
                
                c = cs.new ('COPY_ROTATION')
                c.name = 'bind_to_ik_1'
                c.target = rig
                c.subtarget = ik_prefix + head
                c.mute = True
                
                #BIND TO (0: FK, 1: IK, 2:BIND)
                prop_to_drive_constraint (prop_bone, bone_name=head, constraint_name='bind_to_fk_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ctrl, 2:base', expression='1 - (v1 < 1)')
                prop_to_drive_constraint (prop_bone, bone_name=head, constraint_name='bind_to_ik_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ctrl, 2:base', expression='1 - (v1 > 0 and v1 < 2)')
                
                relevant_bones.append ('ctrl_'+head)
                set_bone_type (name='ctrl_'+head, type='ctrl')
                
                bone_visibility (prop_bone, module, relevant_bones, ik_ctrl='ctrl')
                
                #set module name on relevant bones (used by the 'N-panel' interface)
                set_module_on_relevant_bones (relevant_bones, module)
                
                #snap_info
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                pbone = pbones[prop_bone]
                si = 'snapinfo_simpletobase_0'
                if si in pbone:
                    pbone[si] = pbone[si] + [head]
                    
                
            ########################################################################################################
            ########################################################################################################

            #SPRING BELLY

            def spring_belly (module, waist_bones, loc_pelvis_front, loc_sternum_lower):
                
                if generate__spring_belly == True:
                    
                    #bones that should be used for animation
                    relevant_bones = []
                    
                    #bone that holds all properties of the module
                    prop_bone = create_mudule_prop_bone (module)
                    
                    #target belly
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    ebone = ebones.new (name = 'target_belly')
                    ebone.head = mean (ebones[loc_sternum_lower].head, ebones[loc_pelvis_front].head)
                    ebone.tail = (ebone.head - ebones[waist_bones[0]].tail) + ebone.head
                    ebone.parent = ebones [waist_bones[0]]

                    #spring belly
                    ebone = ebones.new (name = 'spring_belly')
                    ebone.head = ebones[waist_bones[0]].tail
                    ebone.tail = ebones['target_belly'].head
                    ebone.parent = ebones[waist_bones[0]]

                    bpy.ops.armature.select_all (action='DESELECT')
                    ebone.select = True
                    ebone.select_head = True
                    ebone.select_tail = True
                    ebones.active = ebone
                    bpy.ops.armature.subdivide (number_cuts=1)
                    ebone = ebones['spring_belly.001'].name = 'belly'
                    
                    relevant_bones.append ('spring_belly')

                    #waist_mediator
                    ebone = rig.data.edit_bones.new (name = 'waist_mediator')
                    ebones = rig.data.edit_bones
                    ebone.head = ebones[waist_bones[0]].head
                    ebone.tail = ebones[waist_bones[-1]].tail
                    ebone.roll = 0
                    ebone.parent = ebones[waist_bones[0]]
                    
                    #tracker_belly
                    ebone = rig.data.edit_bones.new (name = 'tracker_belly')
                    ebones = rig.data.edit_bones
                    ebone.head = ebones['spring_belly'].head
                    ebone.tail = ebones['belly'].tail
                    ebone.parent = ebones[waist_bones[0]]
                    
                    #constraints
                    
                    bpy.ops.object.mode_set (mode='POSE')
                    pbones = rig.pose.bones
                    
                    pbone = pbones['waist_mediator']
                    c = pbone.constraints.new ('DAMPED_TRACK')
                    c.name = 'track to waist_upper.tail'
                    c.target = rig
                    c.subtarget = waist_bones[-1]
                    c.head_tail = 1
                    c.track_axis = 'TRACK_Y'
                    c.influence = 1

                    pbone = pbones['target_belly']
                    cs = pbone.constraints
                    c = cs.new ('COPY_LOCATION')
                    c.name = 'mean: sternum, hips 1'
                    c.target = rig
                    c.subtarget = loc_sternum_lower
                    c.use_x = True
                    c.use_y = True
                    c.use_z = True
                    c.invert_x = False
                    c.invert_y = False
                    c.invert_z = False
                    c.use_offset = False
                    c.head_tail = 0
                    c.target_space = 'WORLD'
                    c.owner_space = 'WORLD'
                    c.influence = 1

                    c = cs.new ('COPY_LOCATION')
                    c.name = 'mean: sternum, hips 2'
                    c.target = rig
                    c.subtarget = loc_pelvis_front
                    c.use_x = True
                    c.use_y = True
                    c.use_z = True
                    c.invert_x = False
                    c.invert_y = False
                    c.invert_z = False
                    c.use_offset = False
                    c.head_tail = 0
                    c.target_space = 'WORLD'
                    c.owner_space = 'WORLD'
                    c.influence = 0.5

                    pbone = pbones['spring_belly']
                    cs = pbone.constraints
                    c = cs.new ('TRANSFORM')
                    c.name = 'waist_lower rot to scale'
                    c.use_motion_extrapolate = False
                    c.target = rig
                    c.subtarget = 'waist_mediator'
                    c.map_from = 'ROTATION'
                    c.map_to = 'SCALE'
                    c.map_to_x_from = 'X'
                    c.map_to_y_from = 'X'
                    c.map_to_z_from = 'X'
                    c.from_min_x_rot = 0
                    c.from_max_x_rot = radians(spring_belly__waist_lower_rot_to_scale__waist_lower_rot)
                    c.to_min_y_scale = 1
                    c.to_max_y_scale = spring_belly__waist_lower_rot_to_scale__scale
                    c.to_min_x_scale = 1
                    c.to_max_x_scale = spring_belly__waist_lower_rot_to_scale__scale
                    c.to_min_z_scale = 1
                    c.to_max_z_scale = spring_belly__waist_lower_rot_to_scale__scale
                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    c.influence = 1
                    
                    c = cs.new ('COPY_ROTATION')
                    c.name = 'copy tracker_belly'
                    c.target = rig
                    c.subtarget = 'tracker_belly'
                    c.use_x = True
                    c.use_y = True
                    c.use_z = True
                    c.invert_x = False
                    c.invert_y = False
                    c.invert_z = False
                    c.use_offset = True
                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    c.influence = 1
                    
                    pbone = pbones['tracker_belly']
                    c = pbone.constraints.new ('TRACK_TO')
                    c.name = 'track to target belly'
                    c.target = rig
                    c.subtarget = 'target_belly'
                    c.head_tail = 0
                    c.track_axis = 'TRACK_Y'
                    c.up_axis = 'UP_Z'
                    c.use_target_z = True
                    c.target_space = 'WORLD'
                    c.owner_space = 'WORLD'
                    c.influence = 1

                    pbone = pbones['belly']
                    c = pbone.constraints.new ('LIMIT_SCALE')
                    c.name = 'keep scale 1'
                    c.use_min_x = True
                    c.use_max_x = True
                    c.use_min_y = True
                    c.use_max_y = True
                    c.use_min_z = True
                    c.use_max_z = True
                    c.min_x = 1
                    c.max_x = 1
                    c.min_y = 1
                    c.max_y = 1
                    c.min_z = 1
                    c.max_z = 1
                    c.use_transform_limit = True
                    c.owner_space = 'POSE'
                    c.influence = 1
                    
                    #format bones
                    bpy.ops.object.mode_set (mode='POSE')
                    belly_bones = ['spring_belly', 'belly']
                    for name in belly_bones:
                        #bone settings
                        bone_settings (name, layer=spring_layer, group=spring_group, deform=True, lock_loc=True, lock_rot=False, lock_scale=False, type='spring')
                    #deform
                    set_bone_deform ('spring_belly', False)
                    #shape
                    set_bone_shape (bone_name='spring_belly', shape='sphere', transform_bone='belly', auto_scale_with_offset=None, manual_scale=target_shape_size, shape_bone='LEAF', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                        
                    belly_extra_bones = [loc_sternum_lower, loc_pelvis_front, 'target_belly', 'waist_mediator', 'tracker_belly']
                    for name in belly_extra_bones:
                        #bone settings
                        bone_settings (name, layer=misc_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=False, type=None)
                    
                    
                    #set module name on relevant bones (used by the 'N-panel' interface)
                    set_module_on_relevant_bones (relevant_bones, module)

                    
            ########################################################################################################
            ########################################################################################################

            #SPRING chest

            def spring_chest (module, chest, shoulder):
                
                if generate__spring_chest == True:
                    
                    #bones that should be used for animation
                    relevant_bones = []
                    
                    #bone that holds all properties of the module
                    prop_bone = create_mudule_prop_bone (module)
                    
                    #bone settings            
                    name = chest
                    bone_settings (name, layer=spring_layer, group=spring_group, deform=True, lock_loc=True, lock_rot=False, lock_scale=True, type='spring')
                    set_bone_shape (bone_name=chest, shape='sphere', transform_bone=None, auto_scale_with_offset=None, manual_scale=target_shape_size, shape_bone='LEAF', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                            
                    relevant_bones.append (chest)
                    
                    #constraints
                    left_suffix = sides[0]
                    side = 'left' if chest.endswith (left_suffix) else 'right'
                       
                    
                    bpy.ops.object.mode_set (mode='POSE')
                    pbones = rig.pose.bones
                    pbone = pbones[chest]
                    c = pbone.constraints.new ('TRANSFORM')
                    c.name = 'move shoulder up'
                    c.use_motion_extrapolate = False
                    c.target = rig
                    c.subtarget = shoulder
                    c.map_from = 'ROTATION'
                    c.map_to = 'ROTATION'
                    c.map_to_x_from = 'Z'
                    c.map_to_y_from = 'Z'
                    c.map_to_z_from = 'Z'
                    
                    if side == 'left':                    
                        c.from_min_z_rot = 0
                        c.from_max_z_rot = radians(spring_chest__shoulder_up__shoulder_rot)
                        c.to_min_x_rot = 0
                        c.to_max_x_rot = radians(spring_chest__shoulder_up__rot)
                    else:
                        c.from_min_z_rot = radians(spring_chest__shoulder_up__shoulder_rot) * -1
                        c.from_max_z_rot = 0
                        c.to_min_x_rot = radians(spring_chest__shoulder_up__rot)
                        c.to_max_x_rot = 0

                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    c.influence = 1
                    
                    c = pbone.constraints.new ('TRANSFORM')
                    c.name = 'move shoulder down'
                    c.use_motion_extrapolate = False
                    c.target = rig
                    c.subtarget = shoulder
                    c.map_from = 'ROTATION'
                    c.map_to = 'ROTATION'
                    c.map_to_x_from = 'Z'
                    c.map_to_y_from = 'Z'
                    c.map_to_z_from = 'Z'
                    
                    if side == 'left':
                        c.from_min_z_rot = radians(spring_chest__shoulder_down__shoulder_rot)
                        c.from_max_z_rot = 0
                        c.to_min_x_rot = radians(spring_chest__shoulder_down__rot)
                        c.to_max_x_rot = 0
                    else:
                        c.from_min_z_rot = 0
                        c.from_max_z_rot = radians(spring_chest__shoulder_down__shoulder_rot) * -1
                        c.to_min_x_rot = 0
                        c.to_max_x_rot = radians(spring_chest__shoulder_down__rot)                      
                    
                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    c.influence = 1

                    #set module name on relevant bones (used by the 'N-panel' interface)
                    set_module_on_relevant_bones (relevant_bones, module)


            ########################################################################################################
            ########################################################################################################            

            #SPRING BOTTOM

            def spring_bottom (module, source_bone, parent, side, source_bone_bend_axis):
                
                if generate__spring_bottom == True:
                    
                    bend_axis = source_bone_bend_axis
                    
                    relevant_bones = []

                    #create spring bottom
                    bpy.ops.object.mode_set (mode='EDIT')
                    bottom_raw = 'bottom_raw'
                    ebone = rig.data.edit_bones.new (name = bottom_raw)
                    ebones = rig.data.edit_bones
                    ebone.head = ebones[source_bone].head
                    ebone.tail = ebones[source_bone].tail
                    ebone.roll = ebones[source_bone].roll
                    ebone.parent = ebones[source_bone].parent
                    #rotate it 
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    ebone = ebones[bottom_raw]
                    
                    if bend_axis == '-X':
                        angle = radians(-90)
                        axis = 'X'
                    
                    rotate_ebone_local (ebone=ebone, angle=angle, axis=axis)
                        
                    #set ray start and direction   
                    ray_start = ebones[source_bone].head
                    ray_direction = ebones[bottom_raw].tail - ray_start
                    bpy.ops.object.mode_set (mode='OBJECT')
                    ray_distance = 10

                    #cast ray
                    hit_loc, hit_nor, hit_index, hit_dist = my_tree.ray_cast (ray_start, ray_direction, ray_distance)     

                    #adjust tail
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    ebone = ebones[bottom_raw]
                    ebone.tail = hit_loc
                    ebone.parent = ebones[parent]
                    #subdivide it
                    bpy.ops.armature.select_all (action='DESELECT')
                    ebone.select = True
                    ebone.select_head = True
                    ebone.select_tail = True
                    ebones.active = ebone
                    bpy.ops.armature.subdivide (number_cuts=1)
                    #rename bones
                    bottom = 'bottom'+side
                    spring_bottom = 'spring_bottom'+side
                    ebones = rig.data.edit_bones
                    ebones[bottom_raw+'.001'].name = bottom
                    ebones[bottom_raw].name = spring_bottom

                    #thigh mediator
                    no_twist_name = create_no_twist_bone (source_bone=source_bone)

                    bone_settings (name=spring_bottom, layer=spring_layer, group=spring_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=False, type='spring')
                    bone_settings (name=bottom, layer=spring_layer, group=spring_group, deform=True, lock_loc=True, lock_rot=False, lock_scale=False, type='spring')
                    set_bone_shape (bone_name=spring_bottom, shape='sphere', transform_bone=bottom, auto_scale_with_offset=None, manual_scale=target_shape_size, shape_bone='LEAF', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                    
                    bpy.ops.object.mode_set (mode='POSE')
                    pbones = rig.pose.bones
                    pbone = pbones[spring_bottom]    
                    c = pbone.constraints.new ('TRANSFORM')
                    c.name = 'thigh bend fwd to scale'
                    c.use_motion_extrapolate = False
                    c.target = rig
                    c.subtarget = no_twist_name
                    c.map_from = 'ROTATION'
                    c.map_to = 'SCALE'

                    if bend_axis == '-X':
                        c.map_to_x_from = 'X'
                        c.map_to_y_from = 'X'
                        c.map_to_z_from = 'X'
                        c.from_min_x_rot = 0
                        c.from_max_x_rot = radians(spring_bottom__thigh_bend_fwd_to_scale__thigh_rot)
                        c.to_min_x_scale = 1
                        c.to_max_x_scale = spring_bottom__thigh_bend_fwd_to_scale__scale
                        c.to_min_y_scale = 1
                        c.to_max_y_scale = spring_bottom__thigh_bend_fwd_to_scale__scale
                        c.to_min_z_scale = 1
                        c.to_max_z_scale = spring_bottom__thigh_bend_fwd_to_scale__scale
                                 
                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    c.influence = 0.5
                    
                    c = pbone.constraints.new ('TRANSFORM')
                    c.name = 'thigh bend fwd to rot'
                    c.use_motion_extrapolate = False
                    c.target = rig
                    c.subtarget = no_twist_name
                    c.map_from = 'ROTATION'
                    c.map_to = 'ROTATION'

                    if bend_axis == '-X':
                        c.map_to_x_from = 'X'
                        c.map_to_y_from = 'X'
                        c.map_to_z_from = 'X'
                        c.from_min_x_rot = 0
                        c.from_max_x_rot = radians(spring_bottom__thigh_bend_fwd_to_rot__thigh_rot)
                        c.to_min_x_rot = 0
                        c.to_max_x_rot = radians(spring_bottom__thigh_bend_fwd_to_rot__rot)
                        
                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    c.influence = 0.5
                    
                    c = pbone.constraints.new ('TRANSFORM')
                    c.name = 'thigh bend bwd to scale'
                    c.use_motion_extrapolate = False
                    c.target = rig
                    c.subtarget = no_twist_name
                    c.map_from = 'ROTATION'
                    c.map_to = 'SCALE'

                    if bend_axis == '-X':
                        c.map_to_x_from = 'X'
                        c.map_to_y_from = 'X'
                        c.map_to_z_from = 'X'
                        c.from_min_x_rot = radians(spring_bottom__thigh_bend_bwd_to_scale__thigh_rot)
                        c.from_max_x_rot = 0
                        c.to_min_x_scale = spring_bottom__thigh_bend_bwd_to_scale__scale
                        c.to_max_x_scale = 1
                        c.to_min_y_scale = spring_bottom__thigh_bend_bwd_to_scale__scale
                        c.to_max_y_scale = 1 
                        c.to_min_z_scale = spring_bottom__thigh_bend_bwd_to_scale__scale
                        c.to_max_z_scale = 1
                        
                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    c.influence = 0.5
                    
                    c = pbone.constraints.new ('TRANSFORM')
                    c.name = 'thigh bend bwd to rot'
                    c.use_motion_extrapolate = False
                    c.target = rig
                    c.subtarget = no_twist_name
                    c.map_from = 'ROTATION'
                    c.map_to = 'ROTATION'

                    if bend_axis == '-X':
                        c.map_to_x_from = 'X'
                        c.map_to_y_from = 'X'
                        c.map_to_z_from = 'X'
                        c.from_min_x_rot = radians(spring_bottom__thigh_bend_bwd_to_scale__thigh_rot)
                        c.from_max_x_rot = 0
                        c.to_min_x_rot = radians(spring_bottom__thigh_bend_bwd_to_rot__rot)
                        c.to_max_x_rot = 0
                        
                    c.target_space = 'LOCAL'
                    c.owner_space = 'LOCAL'
                    c.influence = 0.5
                    
                    pbone = pbones[bottom]
                    c = pbone.constraints.new ('LIMIT_SCALE')
                    c.name = 'keep scale 1'
                    c.use_min_x = True
                    c.use_max_x = True
                    c.use_min_y = True
                    c.use_max_y = True
                    c.use_min_z = True
                    c.use_max_z = True
                    c.min_x = 1
                    c.max_x = 1
                    c.min_y = 1
                    c.max_y = 1
                    c.min_z = 1
                    c.max_z = 1
                    c.use_transform_limit = True
                    c.owner_space = 'POSE'
                    c.influence = 1
                    
                    relevant_bones = [spring_bottom, bottom]
                    #set module name on relevant bones (used by the 'N-panel' interface)
                    set_module_on_relevant_bones (relevant_bones, module)


            ########################################################################################################
            ########################################################################################################

            #BIPED_ARM

            def biped_arm (module, chain, pole_target, parent_pt_to_ik_target, forearm_bend_axis, forearm_bend_back, ik_parent, pole_parent, side):
                        
                ik_group = set_ik_group (side)
                
                #chain length should be exactly 4
                
                #bones that should be used for animation
                relevant_bones = []
                
                #bone that holds all properties of the module
                prop_bone = create_mudule_prop_bone (module=module)
                
                #set parent
                first_parent = get_parent (chain[0])
                
                #LOW-LEVEL BONES    
                #set parents
                for index, name in enumerate(chain):
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    if index == 0:
                        ebones[name].parent = ebones[first_parent]
                    else:
                        ebones[name].parent = ebones[chain[index-1]]
                        
                    relevant_bones.append (name)
                    bone_settings (name=name, layer=base_layer, group=base_group, deform=True, lock_loc=True, lock_rot=False, lock_scale=True, type='base')
                    
                #_____________________________________________________________________________________________________
                    
                #SHOULDER BONE:
                #FK
                name = fk_prefix+chain[0]
                duplicate_bone (source_name=chain[0], new_name=name, parent_name=first_parent, roll_override=False, length_override=None)
                bone_settings (name=name, layer=fk_layer, group='fk', deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type='fk')
                set_bone_shape (bone_name=name, shape='sphere', transform_bone=None, auto_scale_with_offset=False, manual_scale=target_shape_size, shape_bone='LEAF', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                relevant_bones.append (name)
                
                #bind low-level bones to FK constraints
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[chain[0]]

                c = pbone.constraints.new ('COPY_ROTATION')
                c.name = 'bind_to_fk_1'
                c.target = rig
                c.subtarget = fk_prefix + chain[0]
                c.mute = True
                
                #filler bones (needed for GYAZ retargeter)
                bpy.ops.object.mode_set (mode='EDIT')
                ebone = rig.data.edit_bones.new (name='fk_filler_'+chain[0])
                ebones = rig.data.edit_bones
                ebone.head = ebones[first_parent].head
                ebone.tail = ebones[chain[0]].head
                ebone.roll = 0
                ebone.parent = ebones[first_parent]
                set_bone_only_layer (bone_name=ebone.name, layer_index=fk_extra_layer)
                
                #IK
                name = ik_prefix+chain[0]
                duplicate_bone (source_name=chain[0], new_name=name, parent_name=first_parent, roll_override=False, length_override=None)
                bone_settings (name=name, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type='ik')
                set_bone_shape (bone_name=name, shape='cube', transform_bone=None, auto_scale_with_offset=False, manual_scale=target_shape_size, shape_bone='LEAF', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                relevant_bones.append (name)
                
                #bind low-level bones to IK constraints
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[chain[0]]

                c = pbone.constraints.new ('COPY_ROTATION')
                c.name = 'bind_to_ik_1'
                c.target = rig
                c.subtarget = ik_prefix + chain[0]
                c.mute = True

                
                #BIND TO (0: FK, 1: IK, 2:BIND)
                prop_to_drive_constraint (prop_bone, bone_name=chain[0], constraint_name='bind_to_fk_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ik, 2:base', expression='1 - (v1 < 1)')
                prop_to_drive_constraint (prop_bone, bone_name=chain[0], constraint_name='bind_to_ik_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ik, 2:base', expression='1 - (v1 > 0 and v1 < 2)')            
                
                bone_visibility (prop_bone, module, relevant_bones, ik_ctrl='ik')

                #SNAP INFO
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[prop_bone]
                pbone['snapinfo_singlebone_0'] = [fk_prefix+chain[0], ik_prefix+chain[0]]
                    
                #three bone limb set-up    
                three_bone_limb (module=module, b1=chain[1], b2=chain[2], b3=chain[3], pole_target=pole_target, pt_distance=pole_target_distance, parent_pt_to_ik_target=parent_pt_to_ik_target, b2_bend_axis=forearm_bend_axis, b2_bend_back=forearm_bend_back, first_parent=chain[0], fk_layer=fk_layer, ctrl_ik_layer=ctrl_ik_layer, ik_group=ik_group, keep_last_bone_rot_when_radius_check=False, ik_parent=ik_parent, pole_parent=pole_parent, b3_shape_bone=None)

                isolate_rotation (module=module, parent_bone=fk_prefix+chain[0], first_bone=fk_prefix+chain[1])
                
                #set module name on relevant bones (used by the 'N-panel' interface)
                set_module_on_relevant_bones (relevant_bones, module=module)
                
                #make the 'Snap&Key' operator recognize this module    
                snappable_module (module)
                


            ########################################################################################################
            ########################################################################################################

            #BIPED_LEG

            def biped_leg (module, chain, pole_target, parent_pt_to_ik_target, shin_bend_axis, shin_bend_back, ik_parent, foot_toes_bend_axis, pole_parent, side):
                
                ik_group = set_ik_group (side)
                
                #chain length should be exactly 4
                
                #bones that should be used for animation
                relevant_bones = []
                
                #bone that holds all properties of the module
                prop_bone = create_mudule_prop_bone (module=module)
                
                #set parent
                first_parent = get_parent (chain[0])
                
                #LOW-LEVEL BONES    
                #set parents
                for index, name in enumerate(chain):
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    if index == 0:
                        ebones[name].parent = ebones[first_parent]
                    else:
                        ebones[name].parent = ebones[chain[index-1]]
                        
                    relevant_bones.append (name)
                    bone_settings (name=name, layer=base_layer, group=base_group, deform=True, lock_loc=True, lock_rot=False, lock_scale=True, type='base')
                    
                #_____________________________________________________________________________________________________

                
                #three bone limb set-up    
                three_bone_limb (module=module, b1=chain[0], b2=chain[1], b3=chain[2], pole_target=pole_target, pt_distance=pole_target_distance, parent_pt_to_ik_target=parent_pt_to_ik_target, b2_bend_axis=shin_bend_axis, b2_bend_back=shin_bend_back, first_parent=first_parent, fk_layer=fk_layer, ctrl_ik_layer=ctrl_ik_layer, ik_group=ik_group, keep_last_bone_rot_when_radius_check=False, ik_parent=ik_parent, pole_parent=pole_parent, b3_shape_bone='UP')

                isolate_rotation (module=module, parent_bone=first_parent, first_bone=fk_prefix+chain[0])

                
                #TOES BONE:
                #FK
                name = fk_prefix+chain[3]
                duplicate_bone (source_name=chain[3], new_name=name, parent_name=fk_prefix+chain[2], roll_override=False, length_override=None)
                bone_settings (name=name, layer=fk_layer, group='fk', deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type='fk')
                set_bone_shape (bone_name=name, shape='sphere', transform_bone=None, auto_scale_with_offset=False, manual_scale=target_shape_size, shape_bone=None, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                relevant_bones.append (name)
                
                #bind low-level bones to FK constraints
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[chain[3]]

                c = pbone.constraints.new ('COPY_ROTATION')
                c.name = 'bind_to_fk_1'
                c.target = rig
                c.subtarget = fk_prefix + chain[3]
                c.mute = True
                
                #lock toe axes
                bend_axis = foot_toes_bend_axis
                if 'X' in bend_axis:
                    lock_1 = 1
                    lock_2 = 2
                
                for ai in [lock_1, lock_2]:   
                    prop_to_drive_pbone_attribute_with_array_index (name, bone_name=name, prop_name='limit_fk_toes'+side, attribute='lock_rotation', array_index=ai, prop_min=0, prop_max=1, prop_default=0, description='limit toes to single axis rotation', expression='v1')
                
                #filler bones (needed for GYAZ retargeter)
                bpy.ops.object.mode_set (mode='EDIT')
                ebone = rig.data.edit_bones.new (name='fk_filler_'+chain[0])
                ebones = rig.data.edit_bones
                ebone.head = ebones[first_parent].head
                ebone.tail = ebones[chain[0]].head
                ebone.roll = 0
                ebone.parent = ebones[first_parent]
                set_bone_only_layer (bone_name=ebone.name, layer_index=fk_extra_layer)    
                
                #IK
                name = ik_prefix+chain[3]
                duplicate_bone (source_name=chain[3], new_name=name, parent_name=ik_prefix+chain[2], roll_override=False, length_override=None)
                bone_settings (name=name, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type='ik')
                set_bone_shape (bone_name=name, shape='cube', transform_bone=None, auto_scale_with_offset=False, manual_scale=target_shape_size, shape_bone=None, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                relevant_bones.append (name)
                
                #lock toe axes
                bend_axis = foot_toes_bend_axis
                if 'X' in bend_axis:
                    lock_1 = 1
                    lock_2 = 2
                
                for ai in [lock_1, lock_2]:   
                    prop_to_drive_pbone_attribute_with_array_index (name, bone_name=name, prop_name='limit_ik_toes'+side, attribute='lock_rotation', array_index=ai, prop_min=0, prop_max=1, prop_default=1, description='limit toes to single axis rotation', expression='v1')
                    
                
                #bind low-level bones to IK constraints
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[chain[3]]

                c = pbone.constraints.new ('COPY_ROTATION')
                c.name = 'bind_to_ik_1'
                c.target = rig
                c.subtarget = ik_prefix + chain[3]
                c.mute = True

                
                #BIND TO (0: FK, 1: IK, 2:BIND)
                prop_to_drive_constraint (prop_bone, bone_name=chain[3], constraint_name='bind_to_fk_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ik, 2:base', expression='1 - (v1 < 1)')
                prop_to_drive_constraint (prop_bone, bone_name=chain[3], constraint_name='bind_to_ik_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ik, 2:base', expression='1 - (v1 > 0 and v1 < 2)')            


                #SNAP INFO
                bpy.ops.object.mode_set (mode='POSE')
                pbone = rig.pose.bones[prop_bone]
                pbone['snapinfo_singlebone_0'] = [fk_prefix+chain[3], ik_prefix+chain[3]]
                
                
                #FOOT ROLL:
                #get heel position
                foot = chain[2]
                toes = chain[3]
                bpy.ops.object.mode_set (mode='EDIT')
                    
                #set ray start and direction    
                ray_start = rig.data.edit_bones[toes].head
                ray_direction = (0, 1, 0)
                ray_distance = 1
                
                #cast ray
                hit_loc, hit_nor, hit_index, hit_dist = my_tree.ray_cast (ray_start, ray_direction, ray_distance)
                
                #third-point of toes.head and hit_loc(heel)
                difference = ray_start - hit_loc
                difference /= 3
                third_point = hit_loc + difference
                
                #ik foot main
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ik_foot_main = ik_prefix+'main_'+foot
                ebone = ebones.new (name = ik_foot_main)
                ik_foot_name = ik_prefix+foot
                ik_foot_ebone = ebones[ik_foot_name]
                foot_length = get_distance (ik_foot_ebone.head, ik_foot_ebone.tail)
                ebone.head = ik_foot_ebone.head
                ebone.tail = (ik_foot_ebone.head[0], ik_foot_ebone.head[1] - foot_length, ik_foot_ebone.head[2])
                ebone.roll = radians (-180) if side == '_l' else radians (180)
                ebone.parent = ebones[ik_parent]
                bone_settings (name=ik_foot_main, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=False, lock_rot=False, lock_scale=True, type='ik')
                set_bone_shape (bone_name=ik_foot_main, shape='cube', transform_bone=None, auto_scale_with_offset=auto_bone_shape_scale_offset_limb, manual_scale=1, shape_bone='UP', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)   
                relevant_bones.append (ik_foot_main)
                
                #ik foot snap target
                snap_target_foot = 'snap_target_'+foot
                duplicate_bone (source_name=ik_foot_main, new_name=snap_target_foot, parent_name=fk_prefix+foot, roll_override=False, length_override=False)
                bone_settings (name=snap_target_foot, layer=fk_extra_layer, group=None, deform=False, lock_loc=True, lock_rot=True, lock_scale=True, type=None)
                
                #foot roll back
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                foot_roll_back = 'roll_back_'+foot
                ebone = ebones.new (name = foot_roll_back)
                ebone.head = hit_loc
                ebone.tail = third_point
                ebone.roll = ebones[foot].roll
                ebone.parent = ebones[ik_foot_main]
                bone_settings (name=foot_roll_back, layer=ctrl_ik_extra_layer, group=ik_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                
                #foot roll front
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                foot_roll_front = 'roll_front_'+foot
                ebone = ebones.new (name = foot_roll_front)
                ebone.head = ebones[toes].head
                ebone.tail = third_point
                ebone.roll = ebones[foot].roll
                ebone.parent = ebones[foot_roll_back]
                ebones[ik_prefix+foot].parent = ebones[foot_roll_front]
                bone_settings (name=foot_roll_front, layer=ctrl_ik_extra_layer, group=ik_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                
                #foot roll main
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                foot_roll_main = 'roll_main_'+foot
                ebone = ebones.new (name = foot_roll_main)
                ebone.head = ebones[foot].head
                length = get_distance (ebones[foot].head, ebones[foot].tail)
                ebone.tail = ebone.head + Vector ((0, length, 0))
                ebone.roll = ebones[foot].roll
                ebone.parent = ebones[ik_foot_main]
                bone_settings (name=foot_roll_main, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type='ik')
                set_bone_shape (bone_name=foot_roll_main, shape='foot_roll', transform_bone=None, auto_scale_with_offset=None, manual_scale=target_shape_size, shape_bone='LEAF', keep_rot_when_radius_check=True, use_bone_size=False, shape_bone_parent_override=False)
                relevant_bones.append (foot_roll_main)
                
                #parent pole target to foot_roll_main
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ebones['target_'+pole_target].parent = ebones[ik_foot_main]                
                
                #ik_toes parent
                ik_toes_parent = ik_prefix+'parent_'+toes
                duplicate_bone (source_name=ik_prefix+toes, new_name=ik_toes_parent, parent_name=ik_prefix+foot, roll_override=False, length_override=None)
                bone_settings (name=ik_toes_parent, layer=ctrl_ik_extra_layer, group=None, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=None)
                bpy.ops.object.mode_set (mode='EDIT')
                ebones = rig.data.edit_bones
                ebones[ik_prefix+toes].parent = ebones[ik_toes_parent]    

                #relegate old ik_foot bone
                set_bone_only_layer (bone_name=ik_prefix+foot, layer_index=ctrl_ik_extra_layer)
                #update snap_info
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                old_snap_info = pbones['module_props__'+module]["snapinfo_3bonelimb_0"]
                old_snap_info[9], old_snap_info[10], old_snap_info[11] = snap_target_foot, ik_foot_main, foot_roll_main
                pbones['module_props__'+module]["snapinfo_3bonelimb_0"] = old_snap_info
                
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                #foot roll constraints:    
                #foot roll front
                if foot_toes_bend_axis == '-X':
                    use_x = True
                    use_z = False

                pbone = pbones [foot_roll_front]
                c = pbone.constraints.new ('COPY_ROTATION')
                c.name = 'copy foot_roll_main'
                c.target = rig
                c.subtarget = foot_roll_main
                c.use_x = use_x
                c.use_y = False
                c.use_z = use_z
                c.invert_x = False
                c.invert_y = False
                c.invert_z = False
                c.use_offset = False
                c.target_space = 'LOCAL'
                c.owner_space = 'LOCAL'
                c.influence = 1
                
                if foot_toes_bend_axis == '-X':
                    min_x = 0
                    max_x = radians (180)
                    min_z = 0
                    max_z = 0
                                
                c = pbone.constraints.new ('LIMIT_ROTATION')
                c.name = 'limit rotation'
                c.owner_space = 'LOCAL'
                c.use_transform_limit = True
                c.influence = 1
                c.use_limit_x = True
                c.use_limit_y = True
                c.use_limit_z = True
                c.min_x = min_x
                c.max_x = max_x
                c.min_y = 0
                c.min_y = 0
                c.min_z = min_z
                c.max_z = max_z

                if foot_toes_bend_axis == '-X':
                    use_x = True
                    use_z = False
     
                #foot roll back   
                pbone = pbones [foot_roll_back]
                c = pbone.constraints.new ('COPY_ROTATION')
                c.name = 'copy foot_roll_main'
                c.target = rig
                c.subtarget = foot_roll_main
                c.use_x = use_x
                c.use_y = False
                c.use_z = use_z
                c.invert_x = use_x
                c.invert_y = False
                c.invert_z = use_z
                c.use_offset = False
                c.target_space = 'LOCAL'
                c.owner_space = 'LOCAL'
                c.influence = 1
                
                if foot_toes_bend_axis == '-X':
                    min_x = 0
                    max_x = radians (180)
                    min_z = 0
                    max_z = 0
   
                c = pbone.constraints.new ('LIMIT_ROTATION')
                c.name = 'limit rotation'
                c.owner_space = 'LOCAL'
                c.use_transform_limit = True
                c.influence = 1
                c.use_limit_x = True
                c.use_limit_y = True
                c.use_limit_z = True
                c.min_x = min_x
                c.max_x = max_x
                c.min_y = 0
                c.min_y = 0
                c.min_z = min_z
                c.max_z = max_z
                    
                #foot roll main
                if foot_toes_bend_axis == '-X':
                    min_x = radians (-180)
                    max_x = radians (180)
                    min_z = 0
                    max_z = 0

                pbone = pbones [foot_roll_main]
                c = pbone.constraints.new ('LIMIT_ROTATION')
                c.name = 'limit rotation'
                c.owner_space = 'LOCAL'
                c.use_transform_limit = True
                c.influence = 1
                c.use_limit_x = True
                c.use_limit_y = True
                c.use_limit_z = True
                c.min_x = min_x
                c.max_x = max_x
                c.min_y = 0
                c.min_y = 0
                c.min_z = min_z
                c.max_z = max_z

                #ik_toes_parent
                if foot_toes_bend_axis == '-X':
                    use_x = True
                    use_z = False

                pbone = pbones [ik_toes_parent]
                c = pbone.constraints.new ('COPY_ROTATION')
                c.name = 'copy foot_roll_front'
                c.target = rig
                c.subtarget = foot_roll_front
                c.use_x = use_x
                c.use_y = False
                c.use_z = use_z
                c.invert_x = True
                c.invert_y = False
                c.invert_z = True
                c.use_offset = True
                c.target_space = 'LOCAL'
                c.owner_space = 'LOCAL'
                c.influence = 1
                
                bone_visibility (prop_bone, module, relevant_bones, ik_ctrl='ik')

                #set module name on relevant bones (used by the 'N-panel' interface)
                set_module_on_relevant_bones (relevant_bones, module=module)
                
                #make the 'Snap&Key' operator recognize this module    
                snappable_module (module)

                
            ########################################################################################################
            ########################################################################################################

            #TWIST BONES

            def twist_bones (source_bone, number, upper_or_lower_limb, twist_target_parent, twist_distribution, end_affector, source_bone_bend_axis, is_thigh):
                if number > 0:
                    count = 3
                    twist_bones = create_twist_bones (source_bone=source_bone, count=count, upper_or_lower_limb=upper_or_lower_limb, twist_target_distance=pole_target_distance, twist_target_parent=twist_target_parent, lock_xz_rot=True, end_affector=end_affector, source_bone_bend_axis=source_bone_bend_axis)
                    removed_twist_bones = remove_surplus_twist_bones (twist_bone_target_count=number, twist_bones_created=count, limb=source_bone)

                    twist_influences = twist_distribution[number-1]
                        
                    twist_constraints (upper_or_lower=upper_or_lower_limb, source_bone=source_bone, target_bone='twist_target_'+source_bone, twist_bone_count=number, influences=twist_influences, source_bone_bend_axis=source_bone_bend_axis, is_thigh=is_thigh)


            ########################################################################################################
            ########################################################################################################

            #FINGERS

            def fingers (module, finger_names, side, bend_axis):
                
                if generate__fingers == True:
                
                    ik_group = set_ik_group (side)
                        
                    #bones that should be used for animation
                    relevant_bones = []
                    
                    #bone that holds all properties of the module
                    prop_bone = create_mudule_prop_bone (module)
                    
                    #set parent
                    first_parent = get_parent (finger_names[0]+'_1'+side)
                        
                    #BASE
                    bpy.ops.object.mode_set (mode='EDIT')
                    ebones = rig.data.edit_bones
                    for finger in finger_names:
                        for n in range (1, 4):
                            name = finger+'_'+str(n)+side
                            ebone = ebones [name]
                            if n == 1:
                                ebone.parent = ebones[first_parent]
                            else:
                                ebone.parent = ebones[finger+'_'+str(n-1)+side]
                    for finger in finger_names:
                        for n in range (1, 4):
                            name = finger+'_'+str(n)+side
                            bone_settings (name=name, layer=base_layer, group='base', deform=True, lock_loc=True, lock_rot=False, lock_scale=True, type='base')
                            relevant_bones.append (name)        
                        

                    def create_finger_bones (prefix, set_shape, layer, group, constraint_name, type):
                        bpy.ops.object.mode_set (mode='EDIT')
                        for finger in finger_names:
                            for n in range (1, 4):
                                name = prefix+finger+'_'+str(n)+side
                                rig.data.edit_bones.new (name=name)
                                ebones = rig.data.edit_bones
                                ebone = ebones [name]
                                if n == 1:
                                    ebone.parent = ebones[first_parent]
                                else:
                                    ebone.parent = ebones[prefix+finger+'_'+str(n-1)+side]
                                source_name = finger+'_'+str(n)+side
                                ebone.head = ebones[source_name].head
                                ebone.tail = ebones[source_name].tail
                                ebone.roll = ebones[source_name].roll
                        for finger in finger_names:
                            for n in range (1, 4):
                                name = prefix+finger+'_'+str(n)+side
                                bone_settings (name=name, layer=layer, group=group, deform=False, lock_loc=True, lock_rot=False, lock_scale=True, type=type)
                                if set_shape == True:
                                    set_bone_shape (bone_name=name, shape='sphere', transform_bone=None, auto_scale_with_offset=None, manual_scale=finger_shape_size, shape_bone='-X', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                                relevant_bones.append (name)
                                
                        #BIND RIG TO FK RIG constraints
                        bpy.ops.object.mode_set (mode='POSE')
                        pbones = rig.pose.bones

                        for finger in finger_names:
                            for n in range (1, 4):
                                name = finger+'_'+str(n)+side
                                c = pbones[name].constraints.new ('COPY_ROTATION')
                                c.name = constraint_name
                                c.target = rig
                                c.subtarget = prefix + name
                                c.mute = True 

                    #FK
                    create_finger_bones (prefix=fk_prefix, set_shape=True, layer=fk_layer, group=fk_group, constraint_name='bind_to_fk_1', type='fk')                                    
                         
                    #IK
                    create_finger_bones (prefix=ik_prefix, set_shape=False, layer=ctrl_ik_extra_layer, group=None, constraint_name='bind_to_ik_1', type=None)

                    #finger ctrl bones
                    for index, finger in enumerate(finger_names):
                        #create ctrl finger bones
                        bpy.ops.object.mode_set (mode='EDIT') 
                        ebones = rig.data.edit_bones
                        ctrl_name = 'ctrl_'+finger+side
                        ebone = ebones.new (name = ctrl_name)
                        if index == 0:
                            source = ik_prefix+finger+'_2'+side
                        else:
                            source = ik_prefix+finger+'_1'+side
                        ebone.head = ebones[source].head
                        ebone.tail = ebones[source].tail
                        ebone.roll = ebones[source].roll
                        ebone.parent = ebones[first_parent]
                        bone_settings (name=ctrl_name, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=True, lock_rot=False, lock_scale=False, type='ctrl')
                        set_bone_shape (bone_name=ctrl_name, shape='cube', transform_bone=None, auto_scale_with_offset=None, manual_scale=finger_shape_size, shape_bone='-X', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                        relevant_bones.append (ctrl_name)
                        bpy.ops.object.mode_set (mode='POSE')
                        pbone = rig.pose.bones[ctrl_name]
                        pbone.lock_scale[0] = True
                        pbone.lock_scale[1] = False
                        pbone.lock_scale[2] = True
                        if index == 0:
                            pbone.lock_location[0] = False
                            pbone.lock_location[1] = False
                            pbone.lock_location[2] = False

                    # constraints
                    bpy.ops.object.mode_set (mode='POSE')
                    pbones = rig.pose.bones
                    for index, finger in enumerate(finger_names):
                            
                        #constraint ik finger bones to finger ctrl bones
                        if index == 0:
                            name = ik_prefix+finger+'_2'+side
                        else:
                            name = ik_prefix+finger+'_1'+side        
                        pbone = pbones[name]
                        c = pbone.constraints.new ('COPY_ROTATION')
                        c.name = 'copy ctrl finger'
                        c.target = rig
                        c.subtarget = 'ctrl_'+finger+side
                        c.use_x = True
                        c.use_y = True
                        c.use_z = True
                        c.invert_x = False
                        c.invert_y = False
                        c.invert_z = False
                        c.use_offset = False
                        c.target_space = 'LOCAL'
                        c.owner_space = 'LOCAL'
                        c.influence = 1
                        
                        #ctrl finger scale to finger rot
                        def add_c (pbone, scale_fwd, rot_fwd, scale_bwd, rot_bwd):
                            c = pbone.constraints.new ('TRANSFORM')
                            c.name = 'ctrl finger scale to bend fwd'
                            c.use_motion_extrapolate = False
                            c.target = rig
                            c.subtarget = 'ctrl_'+finger+side
                            c.map_from = 'SCALE'
                            c.map_to = 'ROTATION'
                            c.map_to_x_from = 'Y'
                            c.map_to_y_from = 'Y'
                            c.map_to_z_from = 'Y'
                            c.from_min_x_scale = 1
                            c.from_max_x_scale = 1
                            c.from_min_y_scale = scale_fwd
                            c.from_max_y_scale = 1
                            c.from_min_z_scale = 1
                            c.from_max_z_scale = 1

                            if bend_axis == '-X':
                                c.to_min_x_rot = radians(rot_fwd)
                                c.to_max_x_rot = 0
                                            
                            c.target_space = 'LOCAL'
                            c.owner_space = 'LOCAL'
                            c.influence = 1
                            
                            c = pbone.constraints.new ('TRANSFORM')
                            c.name = 'ctrl finger scale to bend bwd'
                            c.use_motion_extrapolate = False
                            c.target = rig
                            c.subtarget = 'ctrl_'+finger+side
                            c.map_from = 'SCALE'
                            c.map_to = 'ROTATION'
                            c.map_to_x_from = 'Y'
                            c.map_to_y_from = 'Y'
                            c.map_to_z_from = 'Y'
                            c.from_min_x_scale = 1
                            c.from_max_x_scale = 1
                            c.from_min_y_scale = 1
                            c.from_max_y_scale = scale_bwd
                            c.from_min_z_scale = 1
                            c.from_max_z_scale = 1

                            if bend_axis == '-X':
                                c.to_min_x_rot = 0
                                c.to_max_x_rot = radians(rot_bwd)  
                                           
                            c.target_space = 'LOCAL'
                            c.owner_space = 'LOCAL'
                            c.influence = 1
                                
                        if index == 0:
                            pbone = pbones[ik_prefix+finger+'_3'+side]
                            add_c (pbone, ctrl_finger_scale__to_finger_2_3_bend_fwd__scale, ctrl_finger_scale__to_thumb_2_bend_fwd__rot, ctrl_finger_scale__to_finger_2_3_bend_bwd__scale, ctrl_finger_scale__to_thumb_2_bend_bwd__rot)
                            
                            pbone = pbones[ik_prefix+finger+'_1'+side]
                            c = pbone.constraints.new ('DAMPED_TRACK')
                            c.name = 'track to ctrl_finger.head'
                            c.target = rig
                            c.subtarget = 'ctrl_'+finger+side
                            c.head_tail = 0
                            c.track_axis = 'TRACK_Y'
                            c.influence = 1
                            
                        else:
                            for n in range (2, 4): 
                                pbone = pbones[ik_prefix+finger+'_'+str(n)+side]
                                add_c (pbone, ctrl_finger_scale__to_finger_2_3_bend_fwd__scale, ctrl_finger_scale__to_finger_2_3_bend_fwd__rot, ctrl_finger_scale__to_finger_2_3_bend_bwd__scale, ctrl_finger_scale__to_finger_2_3_bend_bwd__rot)           
                                
                        #limit ctrl finger bone scale
                        pbone = pbones['ctrl_'+finger+side]
                        c = pbone.constraints.new ('LIMIT_SCALE')
                        c.name = 'limit scale'
                        c.owner_space = 'LOCAL'
                        c.influence = 1
                        c.use_transform_limit = True
                        c.use_min_x = True
                        c.use_min_y = True
                        c.use_min_z = True
                        c.use_max_x = True
                        c.use_max_y = True
                        c.use_max_z = True
                        c.min_x = 1
                        c.max_x = 1
                        c.min_y = ctrl_finger_scale__to_finger_2_3_bend_fwd__scale
                        c.max_y = ctrl_finger_scale__to_finger_2_3_bend_bwd__scale
                        c.min_z = 1
                        c.max_z = 1


                    #BIND RIG TO (0:fk, 1:ik, 2:bind)
                    for finger in finger_names:
                        for n in range (1, 4):
                            name = finger+'_'+str(n)+side
                            prop_to_drive_constraint (prop_bone, bone_name=name, constraint_name='bind_to_fk_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ctrl, 2:bind', expression='1 - (v1 < 1)')
                            prop_to_drive_constraint (prop_bone, bone_name=name, constraint_name='bind_to_ik_1', prop_name='switch_'+module, attribute='mute', prop_min=0, prop_max=2, prop_default=0, description='0:fk, 1:ctrl, 2:bind', expression='1 - (v1 > 0 and v1 < 2)')
                 
                    bone_visibility (prop_bone, module, relevant_bones, ik_ctrl='ctrl')

                    #set module name on relevant bones (used by the 'N-panel' interface)
                    set_module_on_relevant_bones (relevant_bones, module)


            ########################################################################################################
            ########################################################################################################

            #TOUCH BONE

            def touch_bone (module, source_bone, ik_bone, side, shape_bone):
                
                group = set_ik_group (side)
                
                name = 'touch_'+source_bone
                duplicate_bone (source_name=source_bone, new_name=name, parent_name=None, roll_override=False, length_override=False)
                bone_settings (name, layer=touch_layer, group=group, deform=False, lock_loc=False, lock_rot=False, lock_scale=True, type='touch')
                
                bpy.ops.object.mode_set (mode='POSE')
                pbones = rig.pose.bones
                
                scale = pbones[ik_bone].custom_shape_scale
                set_bone_shape (bone_name=name, shape='twist_target', transform_bone=None, auto_scale_with_offset=None, manual_scale=scale, shape_bone=shape_bone, keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)
                
                pbone = pbones[name]
                c = pbone.constraints.new ('CHILD_OF')
                c.name = 'Touch Bone'
                c.target = rig                   
                #set inverse matrix
                rig.data.bones.active = rig.data.bones[name]
                context_copy = bpy.context.copy()
                context_copy["constraint"] = pbone.constraints['Touch Bone']
                bpy.ops.constraint.childof_set_inverse(context_copy, constraint='Touch Bone', owner='BONE')
                
                #ik bone copy touch bone transforms
                pbone = pbones[ik_bone]
                c = pbone.constraints.new ('COPY_TRANSFORMS')
                c.name = 'Copy Touch Bone'
                c.target = rig
                c.subtarget = name
                c.mute = False
                
                prop_bone = 'module_props__'+module
                prop_to_drive_constraint (ik_bone, bone_name=ik_bone, constraint_name='Copy Touch Bone', prop_name='touch_active_'+module, attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=0.0, description='', expression='v1')
                
                relevant_bones = [name]
                #visibility
                bone_visibility (prop_bone, module, relevant_bones, ik_ctrl='touch')
                
                #for N-panel
                pbone = pbones[name]
                pbone['module'] = module
                

            ########################################################################################################
            ########################################################################################################

            #FACE_BASE

            def face_base (module, use_jaw, parent):
                
                if generate__face_eyes == True:
                
                    prop_bone = create_mudule_prop_bone (module)
                    relevant_bones = []
                    
                    #create face parent bone
                    duplicate_bone (source_name='head', new_name='face_parent', parent_name=parent, roll_override=False, length_override='HALF')
                    
                    face_parent_parent = parent
                    parent = 'face_parent'
                    
                    #create look target bones
                    bpy.ops.object.mode_set (mode='EDIT')
                    #eye_targets
                    for side in sides:
                        ebone = rig.data.edit_bones.new (name='target_eye'+side)
                        ebone.head = rig.data.edit_bones['eye'+side].head + Vector ((0, -look_target_offset, 0))
                        ebone.tail = rig.data.edit_bones['eye'+side].tail + Vector ((0, -look_target_offset, 0))
                        ebone.roll = 0
                    #look bone
                    look = 'target_look'
                    ebone = rig.data.edit_bones.new (name=look)
                    ebones = rig.data.edit_bones
                    ebone.head = mean (ebones['target_eye'+sides[0]].head, ebones['target_eye'+sides[1]].head)
                    ebone.tail = ebone.head + Vector ((0, 0, general_bone_size))
                    ebone.roll = 0
                    ebone.parent = ebones[parent]
                    #parent eye targets to look bone
                    for side in sides:
                        ebones['target_eye'+side].parent = ebones[look]
                    
                    
                    #name, parent, deform, lock location, lock rotation, shape
                    bone_table = [
                        ['face_parent', face_parent_parent, False, True, True, None],
                        ['eye_l', parent, True, True, False, 'sphere'],
                        ['eye_r', parent, True, True, False, 'sphere'],
                        ['upperlid_l', parent, True, True, False, 'small_cube_r'],
                        ['upperlid_r', parent, True, True, False, 'small_cube_r'],
                        ['lowerlid_l', parent, True, True, False, 'small_cube_l'],
                        ['lowerlid_r', parent, True, True, False, 'small_cube_l'],
                        [look, parent, False, False, True, 'eye_target'],
                        ['target_eye_l', look, False, False, False, None],
                        ['target_eye_r', look, False, False, False, None]
                        ]
                        
                    extra_bones = ['target_eye_l', 'target_eye_r', 'face_parent']
                    shape_bone_layer = []
                        
                    if use_jaw == True:
                        bone_table_jaw = [
                        ['jaw', parent, True, True, False, 'brick2'],
                        ['teeth_lower', parent, True, True, False, None],
                        ['chin', 'jaw', False, True, True, None]
                        ]
                        bone_table += bone_table_jaw
                        extra_bones.append ('teeth_lower')
                        shape_bone_layer.append ('chin')
                        

                    for name, bone_parent, use_deform, lock_loc, lock_rot, bone_shape in bone_table:
                        bpy.ops.object.mode_set (mode='EDIT')
                        ebones = rig.data.edit_bones
                        ebones[name].parent = ebones[bone_parent]
                        ebones[name].roll = 0
                        
                        if look in name:
                            group = target_group
                        else:
                            group = face_group
                        bone_settings (name, layer=face_layer, group=group, deform=use_deform, lock_loc=lock_loc, lock_rot=lock_rot, lock_scale=True, type='face')
                        
                        if bone_shape != None:
                            if 'upperlid' in name or 'lowerlid' in name:
                                shape_bone_parent_override = parent
                            else:
                                shape_bone_parent_override = False
                            if 'jaw' in name:
                                shape_bone = None
                                transform_bone = 'chin'
                                keep_rot_when_radius_check = True
                            else:
                                transform_bone = None
                                shape_bone = '-X'
                                keep_rot_when_radius_check = False
                            if look in name:
                                scale = look_target_size
                            else:
                                scale = face_shape_size
                            set_bone_shape (bone_name=name, shape=bone_shape, transform_bone=transform_bone, auto_scale_with_offset=None, manual_scale=scale, shape_bone=shape_bone, keep_rot_when_radius_check=keep_rot_when_radius_check, use_bone_size=False, shape_bone_parent_override=shape_bone_parent_override)
                        
                        if name in extra_bones:
                            set_bone_only_layer (name, face_extra_layer)
                            
                        if name in shape_bone_layer:
                            set_bone_only_layer (name, 30)
                            
                        relevant_bones.append (name)
                        
                    #eye no twist
                    for side in sides:
                        create_no_twist_bone (source_bone='eye'+side)
                        
                    #constraints
                    bpy.ops.object.mode_set (mode='POSE')
                    pbones = rig.pose.bones
                    
                    if use_jaw == True:
                        
                        c = pbones['teeth_lower'].constraints.new ('COPY_ROTATION')
                        c.name = 'Copy Jaw'
                        c.target = rig
                        c.subtarget = 'jaw'
                        c.influence = teeth_lower_copy_jaw_rot
                        
                        prop_to_drive_constraint ('jaw', bone_name='teeth_lower', constraint_name='Copy Jaw', prop_name='teeth_lower_follow_jaw', attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=teeth_lower_copy_jaw_rot, description='', expression='v1')
                    
                    #eye constraints
                    for side in sides:
                        c = pbones['eye'+side].constraints.new ('TRACK_TO')
                        c.name = 'Eye Target'
                        c.target = rig
                        c.subtarget ='target_eye'+side
                        c.track_axis = 'TRACK_Z'
                        c.up_axis = 'UP_Y'
                        c.mute = True
                        
                        c = pbones['upperlid'+side].constraints.new ('COPY_ROTATION')
                        c.name = 'Copy Eye'
                        c.target = rig
                        c.subtarget = 'no_twist_eye'+side
                        c.influence = upperlid_copy_eye_rot
                        
                        c = pbones['lowerlid'+side].constraints.new ('COPY_ROTATION')
                        c.name = 'Copy Eye'
                        c.target = rig
                        c.subtarget = 'no_twist_eye'+side
                        c.influence = lowerlid_copy_eye_rot
                        
                        prop_to_drive_constraint (look, bone_name='eye'+side, constraint_name='Eye Target', prop_name='active_look_target', attribute='mute', prop_min=0, prop_max=1, prop_default=0, description='', expression='1-v1')
                        prop_to_drive_constraint ('upperlid'+side, bone_name='upperlid'+side, constraint_name='Copy Eye', prop_name='upperlid_follow_eye', attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=upperlid_copy_eye_rot, description='', expression='v1')
                        prop_to_drive_constraint ('lowerlid'+side, bone_name='lowerlid'+side, constraint_name='Copy Eye', prop_name='lowerlid_follow_eye', attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=lowerlid_copy_eye_rot, description='', expression='v1')
        
                    set_module_on_relevant_bones (relevant_bones, module)
                
                
            #FACE_DETAIL

            def face_detail (module):
                
                if generate__face_detail == True:
                
                    prop_bone = create_mudule_prop_bone (module)
                    relevant_bones = []
                    
                    #set parent
                    parent = "face_parent"
                    
                    #create lowerlip parent bone
                    duplicate_bone (source_name='jaw', new_name='lowerlip', parent_name=parent, roll_override=False, length_override='HALF')
                    
                    #name, parent, deform, lock location, lock rotation
                    bone_table = [
                        ['innerbrow_l', parent, True, False, False, 'sphere'],
                        ['innerbrow_r', parent, True, False, False, 'sphere'],
                        ['outerbrow_l', parent, True, False, False, 'sphere'],
                        ['outerbrow_r', parent, True, False, False, 'sphere'],
                        ['cheek_l', parent, True, False, False, 'sphere'],
                        ['cheek_r', parent, True, False, False, 'sphere'],
                        ['nostril_l', parent, True, False, False, 'sphere'],
                        ['nostril_r', parent, True, False, False, 'sphere'],
                        ['upperlip_l', parent, True, False, False, 'sphere'],
                        ['upperlip_r', parent, True, False, False, 'sphere'],
                        ['upperlip_m', parent, True, False, False, 'sphere'],
                        ['mouth_corner_l', parent, True, False, False, 'sphere'],
                        ['mouth_corner_r', parent, True, False, False, 'sphere'],
                        ['lowerlip', parent, False, True, False, None],
                        ['lowerlip_l', 'lowerlip', True, False, False, 'sphere'],
                        ['lowerlip_r', 'lowerlip', True, False, False, 'sphere'],
                        ['tongue_back', 'teeth_lower', True, True, False, 'sphere'],
                        ['tongue_tip', 'tongue_back', True, True, False, 'sphere']
                        ]
                        
                    extra_bones = ['lowerlip']
                        
                    for name, bone_parent, use_deform, lock_loc, lock_rot, bone_shape in bone_table:
                        bpy.ops.object.mode_set (mode='EDIT')
                        ebones = rig.data.edit_bones
                        ebones[name].parent = ebones[bone_parent]
                        ebones[name].roll = 0
                        bone_settings (name, layer=face_layer, group=face_group, deform=use_deform, lock_loc=lock_loc, lock_rot=lock_rot, lock_scale=True, type='face')
                        
                        if bone_shape != None:
                            set_bone_shape (bone_name=name, shape=bone_shape, transform_bone=None, auto_scale_with_offset=None, manual_scale=face_shape_size, shape_bone='-X', keep_rot_when_radius_check=False, use_bone_size=False, shape_bone_parent_override=False)   
                        
                        if name in extra_bones:
                            set_bone_only_layer (name, face_extra_layer)
                            
                        relevant_bones.append (name)
                        
                    #constraints
                    bpy.ops.object.mode_set (mode='POSE')
                    pbones = rig.pose.bones
                    
                    c = pbones['lowerlip'].constraints.new ('COPY_ROTATION')
                    c.name = 'Copy Jaw'
                    c.target = rig
                    c.subtarget = 'jaw'
                    c.influence = lowerlip_copy_jaw_rot
                    
                    prop_to_drive_constraint ('jaw', bone_name='lowerlip', constraint_name='Copy Jaw', prop_name='lowerlip_follow_jaw', attribute='influence', prop_min=0.0, prop_max=1.0, prop_default=lowerlip_copy_jaw_rot, description='', expression='v1')

                    set_module_on_relevant_bones (relevant_bones, module)

            ########################################################################################################
            ########################################################################################################

            #SETUP RIG
                
            prepare (layer=23)
            root (size=root_size, root_extract_size=root_extract_size)
            biped_torso (module='spine', chain=['hips', 'spine_1', 'spine_2', 'spine_3'], first_parent='root_extract')
            short_neck (module='spine', bone_name='neck', ik_rot_bone='ctrl_chest', ik_loc_bone=ik_prefix+'spine_3', distributor_parent='ctrl_torso')
            head (module='spine', bone_name='head', ik_rot_bone='ctrl_neck', ik_loc_bone=ik_prefix+'neck', distributor_parent='ctrl_torso')
            chain_target (fk_chain=[fk_prefix+'neck', fk_prefix+'head'], ik_chain=['ctrl_neck', 'ctrl_head'], chain_target_distance=chest_target_distance, chain_target_size=chest_target_size, target_name='target_head', shape='sphere', use_copy_loc=False, copy_loc_target_bone='', add_constraint_to_layer=True, module='spine', prop_name='visible_spine_targets') 
            chain_target (fk_chain=[fk_prefix+'hips', fk_prefix+'spine_1', fk_prefix+'spine_2', fk_prefix+'spine_3'], ik_chain=['ctrl_chest'], chain_target_distance=chest_target_distance, chain_target_size=chest_target_size, target_name='target_chest', shape='cube', use_copy_loc=True, copy_loc_target_bone='target_head', add_constraint_to_layer=False, module='', prop_name='')              
            touch_bone (module='spine', source_bone='ctrl_torso', ik_bone='ctrl_torso', side='_c', shape_bone='FRONT')  
            ik_prop_bone (name='ik_hand_prop', source_bone='hand_r', parent='root_extract')
            spring_belly (module='spring', waist_bones=['spine_1', 'spine_2'], loc_pelvis_front='loc_pelvis_front', loc_sternum_lower='loc_sternum_lower') 

            for side in sides:
                biped_arm (module='arm'+side, chain=['shoulder'+side, 'upperarm'+side, 'forearm'+side, 'hand'+side], pole_target='elbow'+side, parent_pt_to_ik_target=False, forearm_bend_axis='X', forearm_bend_back=30, ik_parent='ik_hand_prop', pole_parent='root_extract', side=side)    
                biped_leg (module='leg'+side, chain=['thigh'+side, 'shin'+side, 'foot'+side, 'toes'+side], pole_target='knee'+side, parent_pt_to_ik_target=True, shin_bend_axis='-X', shin_bend_back=0, ik_parent='root_extract', foot_toes_bend_axis='-X', pole_parent='root_extract', side=side)
                fingers (module='fingers'+side, finger_names = ['thumb', 'pointer', 'middle', 'ring', 'pinky'], side=side, bend_axis='-X')    
                touch_bone (module='arm'+side, source_bone='hand'+side, ik_bone=ik_prefix+'hand'+side, side=side, shape_bone=None)
                touch_bone (module='leg'+side, source_bone='foot'+side, ik_bone=ik_prefix+'main_foot'+side, side=side, shape_bone='FRONT')
                twist_bones (source_bone='upperarm'+side, number=generate__twist_upperarm_count, upper_or_lower_limb='upper', twist_target_parent='shoulder'+side, twist_distribution=upperarm_twists, end_affector=None, source_bone_bend_axis='-X', is_thigh=False)
                twist_bones (source_bone='forearm'+side, number=generate__twist_forearm_count, upper_or_lower_limb='lower', twist_target_parent='', twist_distribution=forearm_twists, end_affector='hand'+side, source_bone_bend_axis='-X', is_thigh=False)
                twist_bones (source_bone='thigh'+side, number=generate__twist_thigh_count, upper_or_lower_limb='upper', twist_target_parent='hips', twist_distribution=thigh_twists, end_affector=None, source_bone_bend_axis='-X', is_thigh=True)
                twist_bones (source_bone='shin'+side, number=generate__twist_shin_count, upper_or_lower_limb='lower', twist_target_parent='', twist_distribution=shin_twists, end_affector='foot'+side, source_bone_bend_axis='-X', is_thigh=False)    
                spring_chest (module='spring', chest='spring_chest'+side, shoulder='shoulder'+side)
                spring_bottom (module='spring', source_bone='thigh'+side, parent='hips', side=side, source_bone_bend_axis = '-X')
                        
            face_base (module='face', use_jaw=generate__face_jaw, parent='head')
            face_detail (module='face')
            finalize (visible_layers=[])
            
        
        #safety checks
        obj = bpy.context.object
        
        good_to_go = False
        if obj.type == 'ARMATURE' and "GYAZ_rig" in obj.data:
            good_to_go = True
        
        if good_to_go == False:
             report (self, 'Object is not a GYAZ rig', 'WARNING')
        else:
            
            mesh_children = []
            for child in obj.children:
                if child.type == 'MESH':
                    mesh_children.append (child)
                    
            if len (mesh_children) == 0:
                report (self, 'Object has no mesh children.', 'WARNING')
                
            else:
                
                if obj.scale != Vector ((1, 1, 1)):
                    report (self, "Armature has object scaling, cannot proceed.", 'WARNING')
                    
                else:
                    main ()
          
        return {'FINISHED'}


#######################################################
#######################################################

#REGISTER

def register():
    bpy.utils.register_class (Op_GYAZ_GameRig_GenerateRig)
   

def unregister ():
    bpy.utils.unregister_class (Op_GYAZ_GameRig_GenerateRig)

  
if __name__ == "__main__":   
    register()   