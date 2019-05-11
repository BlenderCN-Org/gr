import bpy, os
from mathutils.bvhtree import BVHTree
from mathutils import Vector, Matrix
from math import radians
#from .constants import Constants


class Constants():
        
    bone_shape_scale_multiplier = 1.1
    target_shape_size = 0.05
    general_bone_size = 0.05
    pole_target_distance = 0.5
    finger_shape_size = 0.01
    face_shape_size = 0.005
    look_target_size = face_shape_size * 5
    look_target_offset = 0.5
    chest_target_distance = 1
    chest_target_size = 0.25
    fallback_shape_size = 0.1

    source_path = os.path.dirname(__file__) + "/source_shapes.blend"

    # BIPED:
    # root
    root_size = 0.25
    root_extract_size = 0.15

    # TWIST BONES:
    neck_twist_rotate_back = 0.5
    neck_twist_min_y = -20
    neck_twist_track_to_head = 1

    twist_target_distance = -0.4

    # upperarm
    upperarm_twist_influences = [
        [0.75],
        [0.75, 0.5],
        [0.75, 0.5, 0.25]
    ]

    # forearm
    forearm_twist_influences = [
        [1],
        [1, 0.5],
        [1, 0.5, 0.25]
    ]

    # thigh
    thigh_twist_influences = [
        [0.75],
        [0.75, 0.5],
        [0.75, 0.5, 0.25]
    ]

    # shin
    shin_twist_influences = [
        [0.75],
        [1, 0.5],
        [1, 0.5, 0.25]
    ]

    # SPRING BONES (left):
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

    # FACIAL BONES
    teeth_lower_copy_jaw_rot = 0.7
    lowerlip_copy_jaw_rot = 0.5
    upperlid_copy_eye_rot = 0.25
    lowerlid_copy_eye_rot = 0.1

    # CTRL FINGERS (left):
    ctrl_finger_scale__to_finger_2_3_bend_fwd__scale = 0.5
    ctrl_finger_scale__to_finger_2_3_bend_fwd__rot = -90
    ctrl_finger_scale__to_finger_2_3_bend_bwd__scale = 1.25
    ctrl_finger_scale__to_finger_2_3_bend_bwd__rot = 10

    ctrl_finger_scale__to_thumb_2_bend_fwd__rot = -75
    ctrl_finger_scale__to_thumb_2_bend_bwd__rot = 30

    # CTRL SPINE
    ctrl_waist__copy__ctrl_chest = 1.0
    ctrl_waist__copy__ctrl_hips = 0.6

    ik_spine_2__copy__ctrl_waist = 0.6
    ik_spine_2__copy__ctrl_waist = 0.5

    fixate_ctrl_neck = 0.3
    fixate_ctrl_head = 0.5

    # MISC
    sides = ['_l', '_r']
    fk_prefix = 'fk_'
    ik_prefix = 'ik_'

    # LAYERS
    # game bones
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

    # GROUPS
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


def vis_point(loc):
    v = bpy.data.objects.new('fwd', None)
    v.empty_display_size = .05
    v.location = loc
    bpy.context.scene.collection.objects.link(v)
    
    
def translate_bone_local(name, vector):
    ebone = bpy.context.object.data.edit_bones[name]
    
    mat = ebone.matrix
    mat.invert()

    vec = Vector(vector) @ mat

    ebone.head += vec
    ebone.tail += vec


# angle: degrees, axis: 'X', 'Y', 'Z'
def rotate_bone_local(name, angle, axis):
    ebone = bpy.context.object.data.edit_bones[name]
    
    saved_roll = ebone.roll
    saved_pos = ebone.head.copy()

    mat = ebone.matrix
    eul = mat.to_euler()
    eul.rotate_axis(axis, radians(angle))
    mat = eul.to_matrix().to_4x4()
    mat.translation = saved_pos[0], saved_pos[1], saved_pos[2]
    ebone.matrix = mat

    ebone.roll = saved_roll


def subdivide_bone(name, number, number_to_keep, reverse_naming, prefix, parent_all_to_source, delete_source):
    ebones = bpy.context.object.data.edit_bones
    ebone = ebones[name]
    
    new_ebones = []

    prev_pos = ebone.head
    prev_ebone = ebone
    for n in range(number):
        next_pos = (ebone.tail - ebone.head) * ((1 / number) * (n + 1)) + ebone.head

        new_ebone = ebones.new(
            name=prefix + '_' + str(n + 1) + '_' + ebone.name if not reverse_naming else prefix + '_' + str(
                number - n) + '_' + ebone.name)
        new_ebone.head = prev_pos
        new_ebone.tail = next_pos
        new_ebone.roll = ebone.roll
        new_ebone.use_connect = False
        new_ebone.parent = ebone if parent_all_to_source else prev_ebone

        new_ebones.append(new_ebone)

        prev_pos = next_pos
        prev_ebone = new_ebone

    if delete_source:
        ebones.remove(ebone)

    new_ebones_copy = new_ebones.copy()

    if not reverse_naming:
        for n in range(number - number_to_keep):
            ebone = new_ebones_copy[-(n + 1)]
            ebones.remove(ebone)
            new_ebones.remove(ebone)
    else:
        for n in range(number - number_to_keep):
            ebone = new_ebones_copy[n]
            ebones.remove(ebone)
            new_ebones.remove(ebone)

    return [ebone.name for ebone in new_ebones]


# parent_name: 'SOURCE_BONE', any bone name, ''
def create_leaf_bone(bone_name, source_bone_name, start_middle=False, parent_name='SOURCE_BONE'):
    if bpy.context.mode != 'ARMATURE_EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    rig = bpy.context.object
    leaf_ebone = rig.data.edit_bones.new(name=bone_name)
    source_ebone = rig.data.edit_bones[source_bone_name]
    if start_middle:
        leaf_ebone.head = (source_ebone.head + source_ebone.tail) * .5
        leaf_ebone.tail = source_ebone.tail
    else:
        leaf_ebone.head = source_ebone.tail
        leaf_ebone.tail = source_ebone.tail + (source_ebone.tail - source_ebone.head) * .5
    leaf_ebone.roll = source_ebone.roll
    if parent_name != '':
        if parent_name == 'SOURCE_BONE':
            leaf_ebone.parent = source_ebone
        else:
            leaf_ebone.parent = rig.data.edit_bones[parent_name]


# bone_shape_pos: 'HEAD', 'MIDDLE', 'TAIL'
# lock_loc... expects bool or container of 3 bools
def bone_settings(bvh_tree=None, shape_collection=None, bone_name='', layer_index=0, group_name='', use_deform=False, lock_loc=False, lock_rot=False, lock_scale=False, hide_select=False, bone_shape_name='', bone_shape_pos='MIDDLE', bone_shape_manual_scale=None, bone_type=''):
    
    rig = bpy.context.object
    
    if bpy.context.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    pbones = rig.pose.bones
    bones = rig.data.bones
    pbone = pbones[bone_name]
    bone = bones[bone_name]
    
    # LAYER:
    bools = [False] * 32
    bools[layer_index] = True
    bone.layers = bools
    
    # GROUP:
    if group_name != '':
        pbone.bone_group = rig.pose.bone_groups[group_name]
    else:
        pbone.bone_group = None
        
    # USE_DEFORM:
    bone.use_deform = use_deform
    
    # TRANSFORM LOCKS:
    if type(lock_loc) == bool:
        pbone.lock_location[0] = lock_loc
        pbone.lock_location[1] = lock_loc
        pbone.lock_location[2] = lock_loc  
    else:
        pbone.lock_location[0] = lock_loc[0]
        pbone.lock_location[1] = lock_loc[1]
        pbone.lock_location[2] = lock_loc[2]
    if type(lock_rot) == bool:
        pbone.lock_rotation[0] = lock_rot
        pbone.lock_rotation[1] = lock_rot
        pbone.lock_rotation[2] = lock_rot  
    else:
        pbone.lock_rotation[0] = lock_rot[0]
        pbone.lock_rotation[1] = lock_rot[1]
        pbone.lock_rotation[2] = lock_rot[2]
    if type(lock_scale) == bool:
        pbone.lock_scale[0] = lock_scale
        pbone.lock_scale[1] = lock_scale
        pbone.lock_scale[2] = lock_scale  
    else:
        pbone.lock_scale[0] = lock_scale[0]
        pbone.lock_scale[1] = lock_scale[1]
        pbone.lock_scale[2] = lock_scale[2]
        
    # HIDE SELECT
    bone.hide_select = hide_select        
    
    # BONE TYPE:
    if bone_type != '':
        pbone['bone_type'] = bone_type
    
    # ELSE:
    bone = bones[bone_name]
    bone.hide = False
    bone.use_inherit_rotation = True
    bone.use_local_location = True
    bone.use_inherit_scale = True
    
    # BONE SHAPE:
    if bone_shape_name != '':
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        if bone_shape_manual_scale is None:
            
            # choose a point to cast rays around
            ebones = rig.data.edit_bones
            source_ebone = ebones[bone_name]
            
            if bone_shape_pos == 'HEAD':
                ray_start = source_ebone.head
            elif bone_shape_pos == 'TAIL':
                ray_start = source_ebone.tail
            else:
                """MIDDLE"""
                ray_start = (source_ebone.head + source_ebone.tail) * .5
                    
            # get check points around bone
            number_of_checks = 4
            
            mat = source_ebone.matrix
            mat.invert()

            check_points = []

            for n in range(number_of_checks):
                v = Vector((0, 0, 1))
                rot_mat = Matrix.Rotation(radians((360 / number_of_checks) * n), 4, 'Y') @ mat
                v = v @ rot_mat
                v += ray_start

                check_points.append(v)
            
            # cast rays -> look for geo
            hit_distances = []
            for p in check_points:
                hit_loc, hit_nor, hit_index, hit_dist = bvh_tree.ray_cast(ray_start, p - ray_start, 10)
                
                if hit_dist is not None:
                    hit_distances.append(hit_dist)
                    
            final_shape_scale = max(hit_distances) * Constants.bone_shape_scale_multiplier if len(hit_distances) > 0 else fallback_shape_size
            
        else:
            final_shape_scale = bone_shape_manual_scale
        
        bpy.ops.object.mode_set(mode='POSE')
    
        pbone.custom_shape_scale = final_shape_scale
        
        wgt = shape_collection.objects['GYAZ_game_rigger_WIDGET__' + bone_shape_name]
        pbone.custom_shape = wgt
        pbone.use_custom_shape_bone_size = False
        
        if bone_shape_pos != 'HEAD':
            # create shape bone
            create_leaf_bone(bone_name='shape_' + bone_name, 
                             source_bone_name=bone_name, 
                             start_middle=bone_shape_pos == 'MIDDLE'
                             )
            # use shape bone as transform of shape
            bpy.ops.object.mode_set(mode='POSE')
            pbones = rig.pose.bones
            shape_pbone = pbones['shape_' + bone_name]
            pbone.custom_shape_transform = shape_pbone
            # shape bone settings:
            bone = rig.data.bones['shape_' + bone_name]
            pbone = pbones['shape_' + bone_name]
            # layer
            bools = [False] * 32
            bools[Constants.misc_layer] = True
            bones['shape_' + bone_name].layers = bools
            # use deform
            bone.use_deform = False
            # lock transforms
            pbone.lock_location[0] = True
            pbone.lock_location[1] = True
            pbone.lock_location[2] = True
            pbone.lock_rotation[0] = True
            pbone.lock_rotation[1] = True
            pbone.lock_rotation[2] = True
            pbone.lock_scale[0] = True
            pbone.lock_scale[1] = True
            pbone.lock_scale[2] = True
            
    else:
        pbone.custom_shape = None


# parent_name: bone name or 'SOURCE_PARENT'
def duplicate_bone(source_name, new_name, parent_name, half_long=False):
    if bpy.context.mode != 'ARMATURE_EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    rig = bpy.context.object
    ebones = rig.data.edit_bones
    # transform
    ebone = ebones.new(name=new_name)
    source_ebone = rig.data.edit_bones[source_name]
    ebone.head = source_ebone.head
    ebone.tail = (source_ebone.head + source_ebone.tail) * .5 if half_long else source_ebone.tail
    ebone.roll = ebones[source_name].roll
    # parent
    if parent_name == 'SOURCE_PARENT':
        ebone.parent = ebones[source_name].parent
    elif parent_name != '':
        ebone.parent = rig.data.edit_bones[parent_name]


# point: Vector
def mirror_bone_to_point(bone_name, point):
    if bpy.context.mode != 'ARMATURE_EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    ebones = bpy.context.object.data.edit_bones
    ebone = ebones[bone_name]

    new_head = (point - ebone.head) + point
    new_tail = (point - ebone.tail) + point

    ebone.head = new_head
    ebone.tail = new_tail


def nth_point(A, B, alpha):
    return ((B - A) * alpha) + A


def create_no_twist_bone(source_bone_name):
    # used with twist_targets
    rig = bpy.context.object
    no_twist_name = 'no_twist_' + source_bone_name
    duplicate_bone(source_name=source_bone_name, 
                   new_name=no_twist_name, 
                   parent_name='SOURCE_PARENT', 
                   half_long=True
                   )
    bpy.ops.object.mode_set(mode='POSE')
    pbone = rig.pose.bones[no_twist_name]
    c = pbone.constraints.new('DAMPED_TRACK')
    c.target = rig
    c.subtarget = source_bone_name
    c.head_tail = 1
    bone_settings(bone_name=no_twist_name, 
                  layer_index=Constants.misc_layer, 
                  group_name='', 
                  use_deform=False, 
                  lock_loc=True, 
                  lock_rot=False, 
                  lock_scale=True, 
                  bone_type=None
                  )
    
    return no_twist_name


def prop_to_drive_constraint(prop_bone_name, bone_name, constraint_name, prop_name, attribute, prop_min, prop_max, prop_default, description, expression):
    
    if bpy.context.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
        
    rig = bpy.context.object
    
    # prop
    rig.pose.bones[prop_bone_name][prop_name] = prop_default

    # min, max soft_min, soft_max, description on properties
    if "_RNA_UI" not in rig.pose.bones[prop_bone_name]:
        rig.pose.bones[prop_bone_name]["_RNA_UI"] = {}

    rig.pose.bones[prop_bone_name]["_RNA_UI"][prop_name] = {"min": prop_min,
                                                       "max": prop_max,
                                                       "soft_min": prop_min, 
                                                       "soft_max": prop_max,
                                                       "description": description
                                                       }
    # driver
    d = rig.driver_add('pose.bones["' + bone_name + '"].constraints["' + constraint_name + '"].' + attribute).driver
    v1 = d.variables.new()
    v1.name = 'v1'
    v1.type = 'SINGLE_PROP'
    t = v1.targets[0]
    t.id = rig
    t.data_path = 'pose.bones["' + prop_bone_name + '"]["' + prop_name + '"]'
    d.expression = expression


def prop_to_drive_layer(prop_bone_name, layer_index, prop_name, prop_min, prop_max, prop_default, description, expression):
    
    if bpy.context.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
        
    rig = bpy.context.object
        
    # prop
    rig.pose.bones[prop_bone_name][prop_name] = prop_default

    # min, max soft_min, soft_max, description on properties
    if "_RNA_UI" not in rig.pose.bones[prop_bone_name]:
        rig.pose.bones[prop_bone_name]["_RNA_UI"] = {}

    rig.pose.bones[prop_bone_name]["_RNA_UI"][prop_name] = {"min": prop_min, 
                                                       "max": prop_max,
                                                       "soft_min": prop_min, 
                                                       "soft_max": prop_max,
                                                       "description": description
                                                       }
    # driver
    d = rig.data.driver_add('layers', layer_index).driver
    v1 = d.variables.new()
    v1.name = 'v1'
    v1.type = 'SINGLE_PROP'
    t = v1.targets[0]
    t.id = rig
    t.data_path = 'pose.bones["' + prop_bone_name + '"]["' + prop_name + '"]'
    d.expression = expression


def prop_to_drive_bone_attribute(prop_bone_name, bone_name, bone_type, prop_name, attribute, prop_min, prop_max, prop_default, description, expression):

    if bpy.context.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
        
    rig = bpy.context.object

    # prop
    rig.pose.bones[prop_bone_name][prop_name] = prop_default

    # min, max soft_min, soft_max, description on properties
    if "_RNA_UI" not in rig.pose.bones[prop_bone_name]:
        rig.pose.bones[prop_bone_name]["_RNA_UI"] = {}

    rig.pose.bones[prop_bone_name]["_RNA_UI"][prop_name] = {"min": prop_min, 
                                                       "max": prop_max,
                                                       "soft_min": prop_min, 
                                                       "soft_max": prop_max,
                                                       "description": description
                                                       }
    # driver
    if bone_type == 'PBONE':
        d = rig.driver_add('pose.bones["' + bone_name + '"].' + attribute).driver
    elif bone_type == 'BONE':
        d = rig.data.driver_add('bones["' + bone_name + '"].' + attribute).driver
    v1 = d.variables.new()
    v1.name = 'v1'
    v1.type = 'SINGLE_PROP'
    t = v1.targets[0]
    t.id = rig
    t.data_path = 'pose.bones["' + prop_bone_name + '"]["' + prop_name + '"]'
    d.expression = expression


def prop_to_drive_pbone_attribute_with_array_index(prop_bone_name, bone_name, prop_name, attribute, array_index, prop_min, prop_max, prop_default, description, expression):

    if bpy.context.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
        
    rig = bpy.context.object

    # prop
    rig.pose.bones[prop_bone_name][prop_name] = prop_default

    # min, max soft_min, soft_max, description on properties
    if "_RNA_UI" not in rig.pose.bones[prop_bone_name]:
        rig.pose.bones[prop_bone_name]["_RNA_UI"] = {}

    rig.pose.bones[prop_bone_name]["_RNA_UI"][prop_name] = {"min": prop_min, 
                                                       "max": prop_max,
                                                       "soft_min": prop_min, 
                                                       "soft_max": prop_max,
                                                       "description": description
                                                       }
    # driver
    d = rig.driver_add('pose.bones["' + bone_name + '"].' + attribute, array_index).driver
    v1 = d.variables.new()
    v1.name = 'v1'
    v1.type = 'SINGLE_PROP'
    t = v1.targets[0]
    t.id = rig
    t.data_path = 'pose.bones["' + prop_bone_name + '"]["' + prop_name + '"]'
    d.expression = expression
    

def create_mudule_prop_bone(module):
    
    if bpy.context.mode != 'ARMATURE_EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    
    rig = bpy.context.object
    
    name = 'module_props__' + module
    ebones = rig.data.edit_bones
    # create module bone if it does not exist
    if ebones.get(name) == None:
        ebone = ebones.new(name=name)
        ebone.head = Vector((0, 0, 0))
        ebone.tail = Vector((0, 0, 0.5))
        bone_settings(bone_name=name, 
                      layer_index=Constants.module_prop_layer, 
                      use_deform=False
                      )
    return name


def set_module_on_relevant_bones(relevant_bone_names, module):
    # set module name on relevant bones (used by the 'N-panel' interface)
    if bpy.context.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    
    rig = bpy.context.object
    
    for name in relevant_bone_names:
        rig.pose.bones[name]['module'] = module


def signed_angle(vector_u, vector_v, normal):
    # normal specifies orientation
    angle = vector_u.angle(vector_v)
    if vector_u.cross(vector_v).angle(normal) < 1:
        angle = -angle
    return angle


def get_pole_angle(base_bone_name, ik_bone_name, pole_bone_name):
    
    if bpy.context.mode != 'ARMATURE_EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
        
    ebones = bpy.context.object.data.edit_bones
    
    base_bone = ebones[base_bone_name]
    base_bone = ebones[ik_bone_name]
    base_bone = ebones[pole_bone_name]
    
    pole_location = pole_bone.head
    pole_normal = (ik_bone.tail - base_bone.head).cross(pole_location - base_bone.head)
    projected_pole_axis = pole_normal.cross(base_bone.tail - base_bone.head)
    return signed_angle(base_bone.x_axis, projected_pole_axis, base_bone.tail - base_bone.head)


def calculate_pole_target_location(b1, b2, b3, pole_target_distance):
    
    if bpy.context.mode != 'ARMATURE_EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    
    rig = bpy.context.object
    ebones = rig.data.edit_bones

    midpoint = (ebones[b1].head + ebones[b3].head) / 2
    difference = ebones[b2].head - midpoint
    # calculate multiplier for desired target distance
    current_distance = get_distance(Vector((0, 0, 0)), difference)
    multiplier = pole_target_distance / current_distance
    #
    pole_pos = difference * multiplier + ebones[b2].head

    return pole_pos


def calculate_pole_target_location_2(b1, b2, b3, pole_target_distance, b2_bend_axis):
    
    if bpy.context.mode != 'ARMATURE_EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    
    rig = bpy.context.object
    ebones = rig.data.edit_bones

    pole_bone = 'pole_pos_' + b2
    duplicate_bone(source_name=b2, 
                   new_name=pole_bone
                   )

    if b2_bend_axis == 'X':
        v = 0, 0, -pole_target_distance
    elif b2_bend_axis == '-X':
        v = 0, 0, pole_target_distance

    translate_ebone_local (name=pole_bone, vector=v)

    pole_pos = ebones[pole_bone].head
    rig.data['temp'] = pole_pos
    ebones.remove(ebones[pole_bone])

    return Vector((rig.data['temp']))


def get_ik_group_name(side):
    # set group
    if side == Constants.sides[0]:
        ik_group = Constants.left_ik_group
    elif side == Constants.sides[1]:
        ik_group = Constants.right_ik_group
    elif side == '_c':
        ik_group = Constants.central_ik_group
    return ik_group


# upper_or_lower_limb: 'UPPER', 'LOWER'
def create_twist_bones(bvh_tree, shape_collection, source_bone_name, count, upper_or_lower_limb, twist_target_distance, end_affector_name, influences, is_thigh):
    
    source_bone_bend_axis = '-X'
    twist_bones = []
    
    if bpy.context.mode != 'ARMATURE_EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    
    rig = bpy.context.object
    ebones = rig.data.edit_bones
    source_ebone = ebones[source_bone_name]

    twist_bones = subdivide_bone (name=source_bone_name, 
                                  number=3, 
                                  number_to_keep=count, 
                                  reverse_naming=True if upper_or_lower_limb == 'LOWER' else False, 
                                  prefix='twist', 
                                  parent_all_to_source=True,
                                  delete_source=False
                                  )

    # twist target bones
    if upper_or_lower_limb == 'UPPER':

        # create no-twist bone if it does not exist already
        no_twist_name = create_no_twist_bone(source_bone_name=source_bone_name)

        # duplicate source bone
        twist_target_name = 'twist_target_' + source_bone_name
        duplicate_bone(source_name=source_bone_name, 
                       new_name=twist_target_name, 
                       parent_name=no_twist_name
                       )
                       
        # twist target
        if source_bone_bend_axis == '-X':
            vector = 0, 0, -twist_target_distance

        translate_bone_local(name=twist_target_name, 
                             vector=vector
                             )
        ebone = ebones[twist_target_name]
        ebone.tail = ebone.head + Vector((0, 0, Constants.general_bone_size))
        
        bone_settings(bvh_tree=bvh_tree, 
                      shape_collection=shape_collection, 
                      bone_name=twist_target_name, 
                      layer_index=Constants.twist_target_layer, 
                      group_name=Constants.twist_group,
                      lock_rot=True,
                      lock_rot=(True, False, True),
                      lock_scale=True,
                      bone_shape_name='twist_target',
                      bone_shape_pos='HEAD',
                      bone_shape_manual_scale=Constants.target_shape_size,
                      bone_type=''
                      )

        # twist target line
        bpy.ops.object.mode_set(mode='EDIT')
        ebones = rig.data.edit_bones
        tt_ebone = ebones[twist_target_name]
        twist_target_line_name = 'twist_target_line_' + source_bone_name
        ttl_ebone = ebones.new(name=twist_target_line_name)
        ttl_ebone.head = ebones[source_bone_name].head
        ttl_ebone.tail = tt_ebone.head
        ttl_ebone.parent = ebones[source_bone_name]
        
        bone_settings(bvh_tree=bvh_tree, 
                      shape_collection=shape_collection, 
                      bone_name=twist_target_line_name, 
                      layer_index=Constants.twist_target_layer, 
                      group_name=Constants.twist_group,
                      lock_loc=True,
                      lock_rot=True, 
                      lock_scale=True,
                      bone_shape_name='line',
                      bone_shape_pos='HEAD',
                      bone_shape_manual_scale=1,
                      bone_type=''
                      )

    elif upper_or_lower_limb == 'LOWER':
        
        if end_affector_name != '':
            twist_target_name = 'twist_target_' + source_bone_name
            create_leaf_bone(bone_name=twist_target_name, 
                             source_bone_name=source_bone_name, 
                             start_middle=False, 
                             parent_name=''
                             )
            
            # 'Child Of' parent it to end affector (hand or foot) - the use of constraint is needed for the twist constraints to work
            bpy.ops.object.mode_set(mode='POSE')
            pbone = rig.pose.bones[twist_target_name]
            c = pbone.constraints.new('CHILD_OF')
            c.name = 'Copy End Affector'
            c.target = rig
            c.subtarget = end_affector_name
            # set inverse matrix
            rig.data.bones.active = rig.data.bones[twist_target_name]
            context_copy = bpy.context.copy()
            context_copy["constraint"] = pbone.constraints['Copy End Affector']
            bpy.ops.constraint.childof_set_inverse(context_copy, 
                                                   constraint='Copy End Affector',
                                                   owner='BONE'
                                                   )
            bone_settings(bvh_tree=bvh_tree, 
                          shape_collection=shape_collection, 
                          bone_name=twist_target_name, 
                          layer_index=Constants.twist_target_layer, 
                          group_name=Constants.twist_group, 
                          lock_loc=True, 
                          lock_rot=(True, False, True),
                          lock_scale=True, 
                          bone_shape_name='twist_target',
                          bone_shape_pos='HEAD',
                          bone_shape_manual_scale=Constants.target_shape_size, 
                          bone_type=''
                          )
    # bone settings
    for name in twist_bones:
        bone_settings(bvh_tree=bvh_tree, 
                      shape_collection=shape_collection, 
                      bone_name=name, 
                      layer_index=Constants.twist_layer, 
                      group_name=Constants.twist_group,
                      use_deform=True,
                      lock_loc=True,
                      lock_rot=(True, False, True),
                      lock_scale=True,
                      bone_type='twist'
                      )
    
    # CONSTRAINTS
    if bpy.context.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    
    pbones = rig.pose.bones
    influences = influences[count - 1]
    
    for n in range(1, count + 1):
        pbone = pbones['twist_' + str(n) + '_' + source_bone_name]

        if upper_or_lower_limb == 'UPPER':
            c = pbone.constraints.new('LOCKED_TRACK')
            c.name = 'twist'
            c.target = rig
            c.subtarget = twist_target_name
            c.head_tail = 0

            if source_bone_bend_axis == '-X':
                c.track_axis = 'TRACK_NEGATIVE_Z'

            c.lock_axis = 'LOCK_Y'
            c.influence = influences[n - 1]

        elif upper_or_lower_limb == 'LOWER':
            c = pbone.constraints.new('TRACK_TO')
            c.name = 'twist'
            c.target = rig
            c.subtarget = twist_target_name
            c.head_tail = 0
            c.track_axis = 'TRACK_Y'
            c.up_axis = 'UP_Z'
            c.use_target_z = True
            c.target_space = 'WORLD'
            c.owner_space = 'WORLD'
            c.influence = influences[n - 1]

            c = pbone.constraints.new('LIMIT_ROTATION')
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

    # twist target line
    if upper_or_lower_limb == 'UPPER':
        pbone = pbones['twist_target_line_' + source_bone_name]
        c = pbone.constraints.new('STRETCH_TO')
        c.name = 'twist target line'
        c.target = rig
        c.subtarget = 'twist_target_' + source_bone_name
        c.head_tail = 0
        c.bulge = 1
        c.use_bulge_min = False
        c.use_bulge_max = False
        c.volume = 'VOLUME_XZX'
        c.keep_axis = 'PLANE_X'
        c.influence = 1

    # twist target thigh
    if is_thigh == True:
        pbone = pbones['twist_target_' + source_bone_name]
        c = pbone.constraints.new('TRANSFORM')
        c.name = 'thigh rotation to location'
        c.use_motion_extrapolate = True
        c.target = rig
        c.subtarget = source_bone_name
        c.map_from = 'ROTATION'
        c.map_to = 'LOCATION'

        if source_bone_bend_axis == '-X':
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


bvh_tree = BVHTree.FromObject(bpy.context.object.children[0], bpy.context.depsgraph)
shape_collection = bpy.data.collections['GYAZ_game_rigger_widgets']


for side in ('_l', '_r'):   
    create_twist_bones(bvh_tree=bvh_tree,
                       shape_collection=shape_collection,
                       source_bone_name='upperarm'+side, 
                       count=3, 
                       upper_or_lower_limb='UPPER', 
                       twist_target_distance=1, 
                       end_affector_name='',
                       influences=Constants.upperarm_twist_influences, 
                       is_thigh=False
                       )
    create_twist_bones(bvh_tree=bvh_tree,
                       shape_collection=shape_collection,
                       source_bone_name='forearm'+side, 
                       count=3, 
                       upper_or_lower_limb='LOWER', 
                       twist_target_distance=1, 
                       end_affector_name='hand'+side,
                       influences=Constants.forearm_twist_influences, 
                       is_thigh=False
                       )
    create_twist_bones(bvh_tree=bvh_tree,
                       shape_collection=shape_collection,
                       source_bone_name='thigh'+side, 
                       count=3, 
                       upper_or_lower_limb='UPPER', 
                       twist_target_distance=1, 
                       end_affector_name='',
                       influences=Constants.thigh_twist_influences, 
                       is_thigh=True
                       )
    create_twist_bones(bvh_tree=bvh_tree,
                       shape_collection=shape_collection,
                       source_bone_name='shin'+side, 
                       count=1, 
                       upper_or_lower_limb='LOWER', 
                       twist_target_distance=1, 
                       end_affector_name='foot'+side,
                       influences=Constants.shin_twist_influences, 
                       is_thigh=False
                       )