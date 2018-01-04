#############################################
# LEVEL MANIFEST FILE HANDLER
#############################################
import bpy
import bmesh
import struct
import mathutils
import math
import os
import numpy
from bpy.props import *


# METHODS
#############################################

#----------------------------------------------------------------------------------
#- Writes the level manifest JSON file
#----------------------------------------------------------------------------------
def export_level_manifest_json(filename, directory, operator, level_info):
    with open(os.path.join(directory, filename + ".json"), "w") as outp:
        outp.write("{\n")
        outp.write("\t\"level_name\": \"{}\",\n".format(level_info.level_name))
        outp.write("\t\"scene_name\": \"{}\",\n".format(level_info.scene_name))
        outp.write("\t\"creator_name\": \"{}\",\n".format((level_info.creator_name if level_info.creator_name else "Unknown")))

        outp.write("\t\"level_qb\": \"levels\\\\{}\\\\{}.qb\",\n".format(level_info.scene_name, level_info.scene_name))
        outp.write("\t\"level_scripts_qb\": \"levels\\\\{}\\\\{}_scripts.qb\",\n".format(level_info.scene_name, level_info.scene_name))
        outp.write("\t\"level_sfx_qb\": \"levels\\\\{}\\\\{}_sfx.qb\",\n".format(level_info.scene_name, level_info.scene_name))
        outp.write("\t\"level_thugpro_qb\": \"levels\\\\{}\\\\{}_thugpro.qb\",\n".format(level_info.scene_name, level_info.scene_name))

        if not level_info.level_flag_noprx:
            outp.write("\t\"level_pre\": \"{}_scripts.pre\",\n".format(level_info.scene_name))
            outp.write("\t\"level_scnpre\": \"{}scn.pre\",\n".format(level_info.scene_name))
            outp.write("\t\"level_colpre\": \"{}col.pre\",\n".format(level_info.scene_name))
            
        # Export level light color & angles
        lighta = level_info.level_ambient_rgba
        lightc0 = level_info.level_light0_rgba
        lightc1 = level_info.level_light1_rgba
        lighta0 = level_info.level_light0_headpitch
        lighta1 = level_info.level_light1_headpitch
        outp.write("\t\"ambient_rgba\": [{}, {}, {}, {}],\n".format(int(lighta[0]*255), int(lighta[1]*255), int(lighta[2]*255), int(lighta[3]*255)))
        outp.write("\t\"light0_rgba\": [{}, {}, {}, {}],\n".format(int(lightc0[0]*255), int(lightc0[1]*255), int(lightc0[2]*255), int(lightc0[3]*255)))
        outp.write("\t\"light1_rgba\": [{}, {}, {}, {}],\n".format(int(lightc1[0]*255), int(lightc1[1]*255), int(lightc1[2]*255), int(lightc1[3]*255)))
        outp.write("\t\"light0_position\": [{}, {}],\n".format(lighta0[0], lighta0[1]))
        outp.write("\t\"light1_position\": [{}, {}],\n".format(lighta1[0], lighta1[1]))
        
        outp.write("\t\"FLAG_OFFLINE\": {},\n".format(("true" if level_info.level_flag_offline else "false")))
        outp.write("\t\"FLAG_INDOOR\": {},\n".format(("true" if level_info.level_flag_indoor else "false")))
        outp.write("\t\"FLAG_NOSUN\": {},\n".format(("true" if level_info.level_flag_nosun else "false")))
        outp.write("\t\"FLAG_DEFAULT_SKY\": {},\n".format(("true" if level_info.level_flag_defaultsky else "false")))
        outp.write("\t\"FLAG_ENABLE_WALLRIDE_HACK\": {},\n".format(("true" if level_info.level_flag_wallridehack else "false")))
        outp.write("\t\"FLAG_DISABLE_BACKFACE_HACK\": {},\n".format(("true" if level_info.level_flag_nobackfacehack else "false")))
        outp.write("\t\"FLAG_MODELS_IN_SCRIPT_PRX\": {},\n".format(("true" if level_info.level_flag_modelsinprx else "false")))
        outp.write("\t\"FLAG_DISABLE_GOALEDITOR\": {},\n".format(("true" if level_info.level_flag_nogoaleditor else "false")))
        outp.write("\t\"FLAG_DISABLE_GOALATTACK\": {},\n".format(("true" if level_info.level_flag_nogoalattack else "false")))
        outp.write("\t\"FLAG_NO_PRX\": {},\n".format(("true" if level_info.level_flag_noprx else "false")))

        outp.write("}\n")



# PANELS
#############################################
#----------------------------------------------------------------------------------
class THUGSceneSettings(bpy.types.Panel):
    bl_label = "TH Level Settings"
    bl_region_type = "WINDOW"
    bl_space_type = "PROPERTIES"
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        if not context.scene: return
        scene = context.scene
        self.layout.row().prop(scene.thug_level_props, "level_name")
        self.layout.row().prop(scene.thug_level_props, "scene_name")
        self.layout.row().prop(scene.thug_level_props, "creator_name")
        self.layout.row().prop(scene.thug_level_props, "level_skybox")
        
        #self.layout.row().prop(scene.thug_level_props, "default_terrain")
        #self.layout.row().prop(scene.thug_level_props, "default_terrain_rail")
        
        self.layout.row().label(text="Level Lights", icon='LAMP_DATA')
        box = self.layout.box().column(True)
        box.row().prop(scene.thug_level_props, "level_ambient_rgba")
        
        tmp_row = box.row().split()
        col = tmp_row.column()
        col.prop(scene.thug_level_props, "level_light0_rgba")
        col = tmp_row.column()
        col.prop(scene.thug_level_props, "level_light0_headpitch")
        
        tmp_row = box.row().split()
        col = tmp_row.column()
        col.prop(scene.thug_level_props, "level_light1_rgba")
        col = tmp_row.column()
        col.prop(scene.thug_level_props, "level_light1_headpitch")
        
        self.layout.row().label(text="Level Flags", icon='INFO')
        box = self.layout.box().column(True)
        box.row().prop(scene.thug_level_props, "level_flag_offline")
        box.row().prop(scene.thug_level_props, "level_flag_noprx")
        box.row().prop(scene.thug_level_props, "level_flag_indoor")
        box.row().prop(scene.thug_level_props, "level_flag_nosun")
        box.row().prop(scene.thug_level_props, "level_flag_defaultsky")
        box.row().prop(scene.thug_level_props, "level_flag_wallridehack")
        box.row().prop(scene.thug_level_props, "level_flag_nobackfacehack")
        box.row().prop(scene.thug_level_props, "level_flag_modelsinprx")
        box.row().prop(scene.thug_level_props, "level_flag_nogoaleditor")
        box.row().prop(scene.thug_level_props, "level_flag_nogoalattack")