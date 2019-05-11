import bpy
from mathutils.bvhtree import BVHTree
from mathutils import Vector, Matrix
from math import radians
from .constants import Constants

#shape_layer = 24
#bvh_tree = BVHTree.FromObject(bpy.context.object.children[0], bpy.context.depsgraph)
#shape_collection = bpy.data.collections['GYAZ_game_rigger_widgets']


def vis_point(loc):
    v = bpy.data.objects.new('fwd', None)
    v.empty_display_size = .05
    v.location = loc
    bpy.context.scene.collection.objects.link(v)


def create_leaf_ebone(bone_name, source_bone_name, start_middle):
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
    leaf_ebone.parent = source_ebone


# bone_shape_mode: 'HEAD', 'MIDDLE', 'TAIL'
# lock_loc... expects bool or container of 3 bools
def bone_settings(bvh_tree, shape_collection, bone_name, layer_index=0, group_name='', use_deform=False, lock_loc=False, lock_rot=False, lock_scale=False, bone_shape_name='', bone_shape_mode='MIDDLE', bone_type=''):
    
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
            
        # choose a point to cast rays around
        ebones = rig.data.edit_bones
        source_ebone = ebones[bone_name]
        
        if bone_shape_mode == 'HEAD':
            ray_start = source_ebone.head
        elif bone_shape_mode == 'TAIL':
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
                
        if len(hit_distances) > 0:
        
            bpy.ops.object.mode_set(mode='POSE')
        
            pbone.custom_shape_scale = max(hit_distances) * 1.5
            
            wgt = shape_collection.objects['GYAZ_game_rigger_WIDGET__' + bone_shape_name]
            pbone.custom_shape = wgt
            pbone.use_custom_shape_bone_size = False
            
            if bone_shape_mode != 'HEAD':
                # create shape bone
                create_leaf_ebone(bone_name='shape_'+bone_name, source_bone_name=bone_name, start_middle=bone_shape_mode == 'MIDDLE')
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


def create_no_twist_bone(bvh_tree, shape_collection, source_name):
    # used with twist_targets
    rig = bpy.context.object
    no_twist_name = 'no_twist_' + source_name
    duplicate_bone(source_name=source_name, new_name=no_twist_name, parent_name='SOURCE_PARENT', half_long=True)
    bpy.ops.object.mode_set(mode='POSE')
    pbone = rig.pose.bones[no_twist_name]
    c = pbone.constraints.new('DAMPED_TRACK')
    c.target = rig
    c.subtarget = source_name
    c.head_tail = 1
    bone_settings(bvh_tree, shape_collection, bone_name=no_twist_name, layer_index=0, group_name='', use_deform=False, lock_loc=True, lock_rot=False, lock_scale=True, bone_type=None)
    return no_twist_name
