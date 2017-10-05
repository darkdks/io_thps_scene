import bpy
import bgl
from bpy.props import *
from . constants import *
from . helpers import *
from . autorail import *
from . collision import *
from . material import *
from . ui_draw import *
from . import_nodes import THUGImportNodeArray

# METHODS
#############################################
def _gap_props_end_object_changed(gap_props, context):
    eo = bpy.data.objects.get(gap_props.end_object)
    if not eo:
        return
    eo.thug_triggerscript_props.triggerscript_type = "None"
    eo.thug_triggerscript_props.gap_props.reserved_by = gap_props.id_data.name

# PROPERTIES
#############################################

#----------------------------------------------------------------------------------
#- Defines the Class of an empty
#----------------------------------------------------------------------------------
class THUGEmptyProps(bpy.types.PropertyGroup):
    empty_type = EnumProperty(items=(
        ("None", "None", ""),
        ("Restart", "Restart", "Player restarts."),
        ("GenericNode", "Generic Node", "KOTH crown and other objects."),
        ("Pedestrian", "Pedestrian", "Not currently implemented."),
        ("Vehicle", "Vehicle", "Not currently implemented."),
        ("ProximNode", "Proximity Node", "Node that can fire events when objects are inside its radius."),
        ("GameObject", "Game Object", "CTF Flags, COMBO letters, etc."),
        ("BouncyObject", "Bouncy Object", "Legacy node type, not used, only for identification in imported levels."),
        ("Custom", "Custom", ""),
        ), name="Node Type", default="None")


#----------------------------------------------------------------------------------
#- Currently unused
#----------------------------------------------------------------------------------
class THUGGapProps(bpy.types.PropertyGroup):
    flags = {
        "CANCEL_GROUND": 0x00000001,
        "CANCEL_AIR": 0x00000002,
        "CANCEL_RAIL": 0x00000004,
        "CANCEL_WALL": 0x00000008,
        "CANCEL_LIP": 0x00000010,
        "CANCEL_WALLPLANT": 0x00000020,
        "CANCEL_MANUAL": 0x00000040,
        "CANCEL_HANG": 0x00000080,
        "CANCEL_LADDER": 0x00000100,
        "CANCEL_SKATE": 0x00000200,
        "CANCEL_WALK": 0x00000400,
        "CANCEL_DRIVE": 0x00000800,
        "REQUIRE_GROUND": 0x00010000,
        "REQUIRE_AIR": 0x00020000,
        "REQUIRE_RAIL": 0x00040000,
        "REQUIRE_WALL": 0x00080000,
        "REQUIRE_LIP": 0x00100000,
        "REQUIRE_WALLPLANT": 0x00200000,
        "REQUIRE_MANUAL": 0x00400000,
        "REQUIRE_HANG": 0x00800000,
        "REQUIRE_LADDER": 0x01000000,
        "REQUIRE_SKATE": 0x02000000,
        "REQUIRE_WALK": 0x04000000,
        "REQUIRE_DRIVE": 0x08000000,
    }

    CANCEL_MASK = 0x0000FFFF
    REQUIRE_MASK = 0xFFFF0000

    CANCEL_GROUND = BoolProperty(name="CANCEL_GROUND", default=True)
    CANCEL_AIR = BoolProperty(name="CANCEL_AIR", default=False)
    CANCEL_RAIL = BoolProperty(name="CANCEL_RAIL", default=False)
    CANCEL_WALL = BoolProperty(name="CANCEL_WALL", default=False)
    CANCEL_LIP = BoolProperty(name="CANCEL_LIP", default=False)
    CANCEL_WALLPLANT = BoolProperty(name="CANCEL_WALLPLANT", default=False)
    CANCEL_MANUAL = BoolProperty(name="CANCEL_MANUAL", default=False)
    CANCEL_HANG = BoolProperty(name="CANCEL_HANG", default=False)
    CANCEL_LADDER = BoolProperty(name="CANCEL_LADDER", default=False)
    CANCEL_SKATE = BoolProperty(name="CANCEL_SKATE", default=False)
    CANCEL_WALK = BoolProperty(name="CANCEL_WALK", default=False)
    CANCEL_DRIVE = BoolProperty(name="CANCEL_DRIVE", default=False)
    REQUIRE_GROUND = BoolProperty(name="REQUIRE_GROUND", default=False)
    REQUIRE_AIR = BoolProperty(name="REQUIRE_AIR", default=False)
    REQUIRE_RAIL = BoolProperty(name="REQUIRE_RAIL", default=False)
    REQUIRE_WALL = BoolProperty(name="REQUIRE_WALL", default=False)
    REQUIRE_LIP = BoolProperty(name="REQUIRE_LIP", default=False)
    REQUIRE_WALLPLANT = BoolProperty(name="REQUIRE_WALLPLANT", default=False)
    REQUIRE_MANUAL = BoolProperty(name="REQUIRE_MANUAL", default=False)
    REQUIRE_HANG = BoolProperty(name="REQUIRE_HANG", default=False)
    REQUIRE_LADDER = BoolProperty(name="REQUIRE_LADDER", default=False)
    REQUIRE_SKATE = BoolProperty(name="REQUIRE_SKATE", default=False)
    REQUIRE_WALK = BoolProperty(name="REQUIRE_WALK", default=False)
    REQUIRE_DRIVE = BoolProperty(name="REQUIRE_DRIVE", default=False)

    name = StringProperty(name="Gap Name", default="Gap")
    score = IntProperty(name="Score", min=0, max=2**30, default=100)
    """
    trickstring = StringProperty(name="Trick", default="")
    spin = IntProperty(name="Required Spin", min=0, max=2**31, default=0, description="Should be a multiple of 180.")
    """
    end_object = StringProperty(
        name="End",
        description="The trigger object that that will end the gap.",
        default="",
        update=_gap_props_end_object_changed)
    two_way = BoolProperty(name="Two way", default=False)

    reserved_by = StringProperty() # the start gap object this object's reserved by

    def draw(self, panel, context):
        col = panel.layout.box().column()
        col.prop(self, "name")
        col.prop(self, "score")
        col.prop_search(self, "end_object", context.scene, "objects")
        col.prop(self, "two_way")

        for flag in sorted(self.flags):
            col.prop(self, flag)

#----------------------------------------------------------------------------------
class THUGObjectTriggerScriptProps(bpy.types.PropertyGroup):
    triggerscript_type = EnumProperty(items=(
        ("None", "None", ""),
        ("Killskater", "Killskater", "Bail the skater and restart them at the given node."),
        ("Killskater_Water", "Killskater (Water)", "Bail the skater and restart them at the given node."),
        ("Teleport", "Teleport", "Teleport the skater to a given node without breaking their combo."),
        ("Custom", "Custom", "Runs a custom script."),
        # ("Gap", "Gap", "Gap."),
        ), name="TriggerScript Type", default="None")
    target_node = StringProperty(name="Target Node")
    custom_name = StringProperty(name="Custom Script Name")
    # gap_props = PointerProperty(type=THUGGapProps)


#----------------------------------------------------------------------------------
#- Proximity node properties
#----------------------------------------------------------------------------------
class THUGProximNodeProps(bpy.types.PropertyGroup):
    proxim_type = EnumProperty(items=(
        ("Camera", "Camera", ""), 
        ("Other", "Other", "")), 
    name="Proximity Type",
    default="Camera")
    radius = IntProperty(name="Radius", min=0, max=1000000, default=150)
    

#----------------------------------------------------------------------------------
#- If you know of another thing GenericNode is used for, let me know!
#----------------------------------------------------------------------------------
class THUGGenericNodeProps(bpy.types.PropertyGroup):
    generic_type = EnumProperty(items=(
        ("Crown", "KOTH Crown", ""), 
        ("Other", "Other", "")) 
    ,name="Node Type",default="Crown")
    

#----------------------------------------------------------------------------------
#- Game objects - models with collision that affect gameplay
#----------------------------------------------------------------------------------
class THUGGameObjectProps(bpy.types.PropertyGroup):
    go_type = EnumProperty(items=(
        ("Ghost", "Ghost", "No model, used for game logic."), 
        ("Flag_Red", "CTF Flag - Red", "Red team flag for CTF."), 
        ("Flag_Red_Base", "CTF Base - Red", "Red team base for CTF."), 
        ("Flag_Yellow", "CTF Flag - Yellow", "Yellow team flag for CTF."), 
        ("Flag_Yellow_Base", "CTF Base - Yellow", "Yellow team base for CTF."), 
        ("Flag_Green", "CTF Flag - Green", "Green team flag for CTF."), 
        ("Flag_Green_Base", "CTF Base - Green", "Green team base for CTF."), 
        ("Flag_Blue", "CTF Flag - Blue", "Blue team flag for CTF."), 
        ("Flag_Blue_Base", "CTF Base - Blue", "Blue team base for CTF."), 
        ("Secret_Tape", "Secret Tape", ""), 
        ("Combo_C", "Combo Letter C", ""), 
        ("Combo_O", "Combo Letter O", ""), 
        ("Combo_M", "Combo Letter M", ""), 
        ("Combo_B", "Combo Letter B", "")), 
    name="Type", default="Ghost")
    go_model = StringProperty(name="Model path", description="Path to the model, relative to Data/Models/.")
    go_suspend = IntProperty(name="Suspend Distance", description="Distance at which the logic/motion of the object pauses.", min=0, max=1000000, default=0)
    
#----------------------------------------------------------------------------------
#- Properties for individual nodes along a path (rail, ladder, waypoints)
#----------------------------------------------------------------------------------
class THUGPathNodeProps(bpy.types.PropertyGroup):
    name = StringProperty(name="Node Name")
    script_name = StringProperty(name="TriggerScript Name")
    
    def register():
        print("adding new path node struct")
        
#----------------------------------------------------------------------------------
#- Restart properties
#----------------------------------------------------------------------------------
class THUGRestartProps(bpy.types.PropertyGroup):

    restart_p1 = BoolProperty(name="Player 1", default=False)
    restart_p2 = BoolProperty(name="Player 2", default=False)
    restart_gen = BoolProperty(name="Generic", default=False)
    restart_multi = BoolProperty(name="Multiplayer", default=False)
    restart_team = BoolProperty(name="Team", default=False)
    restart_horse = BoolProperty(name="Horse", default=False)
    restart_ctf = BoolProperty(name="CTF", default=False)
    restart_type = EnumProperty(items=(
        ("Player1", "Player 1", ""),
        ("Player2", "Player 2", ""),
        ("Generic", "Generic", ""),
        ("Team", "Team", ""),
        ("Multiplayer", "Multiplayer", ""),
        ("Horse", "Horse", ""),
        ("CTF", "CTF", "")),
    name="Primary Type", default="Player1")
    restart_name = StringProperty(name="Restart Name", description="Name that appears in restart menu.")
    

#----------------------------------------------------------------------------------
#- Pedestrian properties, there's a lot of them!
#----------------------------------------------------------------------------------
class THUGPedestrianProps(bpy.types.PropertyGroup):
    ped_type = EnumProperty(items=(
        ("Ped_From_Profile", "From Profile", "Generic pedestrian with a skin from a profile."),
        ("CrowdC_01", "CrowdC_01", "Test")),
    name="Type", default="Ped_From_Profile")
    ped_skeleton = EnumProperty(items=(
        ("THPS5_human", "THPS5 Human", "Most commonly-used skeleton."),
        ("MonsterPed", "MonsterPed", "Test2")),
    name="Skeleton", default="THPS5_human")
    
    ped_profile = EnumProperty(items=(
        ("random_male_profile", "random_male_profile", ""),
        ("random_female_profile", "random_female_profile", ""),
        ("Ped_Skateboard_a", "Ped_Skateboard_a", ""),
        ("Ped_MultiStage_Skateboard_A", "Ped_MultiStage_Skateboard_A", ""),
        ("Ped_MultiStage_Skateboard_B", "Ped_MultiStage_Skateboard_B", ""),
        ("Ped_MultiStage_Skateboard_C", "Ped_MultiStage_Skateboard_C", ""),
        ("Ped_MultiStage_A", "Ped_MultiStage_A", ""),
        ("Ped_MultiStage_B", "Ped_MultiStage_B", ""),
        ("Ped_MultiStage_C", "Ped_MultiStage_C", ""),
        ("Ped_F_MultiStage_Skateboard_A", "Ped_F_MultiStage_Skateboard_A", ""),
        ("Ped_F_MultiStage_Skateboard_B", "Ped_F_MultiStage_Skateboard_B", ""),
        ("Ped_F_MultiStage_Skateboard_C", "Ped_F_MultiStage_Skateboard_C", ""),
        ("Ped_F_MultiStage_A", "Ped_F_MultiStage_A", ""),
        ("Ped_F_MultiStage_B", "Ped_F_MultiStage_B", ""),
        ("Ped_F_MultiStage_C", "Ped_F_MultiStage_C", ""),
        ("Ped_Kid_Skateboard_a", "Ped_Kid_Skateboard_a", ""),
        ("Ped_Skeezo", "Ped_Skeezo", ""),
        ("Ped_Ralphie", "Ped_Ralphie", ""),
        ("Ped_Bender", "Ped_Bender", ""),
        ("Ped_Furlow", "Ped_Furlow", ""),
        ("Ped_Kozar", "Ped_Kozar", ""),
        ("Ped_Hough", "Ped_Hough", ""),
        ("Ped_Meat", "Ped_Meat", ""),
        ("Ped_Jordan", "Ped_Jordan", ""),
        ("Ped_Eric", "Ped_Eric", ""),
        ("Ped_Bum_01", "Ped_Bum_01", ""),
        ("Ped_Crackhead_01", "Ped_Crackhead_01", ""),
        ("Ped_Drugdealer_01", "Ped_Drugdealer_01", ""),
        ("Ped_Drugdealer_02", "Ped_Drugdealer_02", ""),
        ("Ped_Drugdealer_03", "Ped_Drugdealer_03", ""),
        ("Ped_FactoryWorker_01", "Ped_FactoryWorker_01", ""),
        ("Ped_FactoryWorker_02", "Ped_FactoryWorker_02", ""),
        ("Ped_Security_Train", "Ped_Security_Train", ""),
        ("Ped_Street_Warrior_01", "Ped_Street_Warrior_01", ""),
        ("Ped_Street_Warrior_02", "Ped_Street_Warrior_02", ""),
        ("Ped_Street_Warrior_03", "Ped_Street_Warrior_03", ""),
        ("Ped_Tombstone", "Ped_Tombstone", ""),
        ("Ped_Businesswoman_01", "Ped_Businesswoman_01", ""),
        ("Ped_M_NYPD_01", "Ped_M_NYPD_01", ""),
        ("Ped_F_NYPD_01", "Ped_F_NYPD_01", ""),
        ("Ped_Construction_Jhammer", "Ped_Construction_Jhammer", ""),
        ("Ped_Construction_Manhole", "Ped_Construction_Manhole", ""),
        ("Ped_Skater_NY1", "Ped_Skater_NY1", ""),
        ("Ped_Skater_NY2", "Ped_Skater_NY2", ""),
        ("Ped_Peralta", "Ped_Peralta", ""),
        ("Ped_Chef", "Ped_Chef", ""),
        ("Ped_BusinessMan_01", "Ped_BusinessMan_01", ""),
        ("Ped_BusinessMan_02", "Ped_BusinessMan_02", ""),
        ("Ped_BusinessMan_03", "Ped_BusinessMan_03", ""),
        ("Ped_BlkKid_01", "Ped_BlkKid_01", ""),
        ("Ped_BlkKid_02", "Ped_BlkKid_02", ""),
        ("Ped_BlkKid_03", "Ped_BlkKid_03", ""),
        ("Ped_Trooper", "Ped_Trooper", ""),
        ("Ped_Todd", "Ped_Todd", ""),
        ("Ped_F_Dancer_01", "Ped_F_Dancer_01", ""),
        ("Ped_F_Dancer_02", "Ped_F_Dancer_02", ""),
        ("Ped_Clemens", "Ped_Clemens", ""),
        ("Ped_AfroJim", "Ped_AfroJim", ""),
        ("Ped_Doorman_01", "Ped_Doorman_01", ""),
        ("Ped_Deskclerk_01", "Ped_Deskclerk_01", ""),
        ("Ped_F_Deskclerk_01", "Ped_F_Deskclerk_01", ""),
        ("Ped_Leafblower", "Ped_Leafblower", ""),
        ("Ped_Security_01", "Ped_Security_01", ""),
        ("Ped_Security_02", "Ped_Security_02", ""),
        ("Ped_Security_03", "Ped_Security_03", ""),
        ("Ped_F_Security", "Ped_F_Security", ""),
        ("Ped_Gardener_01", "Ped_Gardener_01", ""),
        ("Ped_Gardener_02", "Ped_Gardener_02", ""),
        ("Ped_F_Gardener", "Ped_F_Gardener", ""),
        ("Ped_F_MCeleb", "Ped_F_MCeleb", ""),
        ("Ped_F_KGB", "Ped_F_KGB", ""),
        ("Ped_KGB_01", "Ped_KGB_01", ""),
        ("Ped_KGB_02", "Ped_KGB_02", ""),
        ("Ped_RGuard_01", "Ped_RGuard_01", ""),
        ("Ped_RGuard_02", "Ped_RGuard_02", ""),
        ("Ped_F_Babushka", "Ped_F_Babushka", ""),
        ("Ped_Cameraman", "Ped_Cameraman", ""),
        ("Ped_Official_SC_01", "Ped_Official_SC_01", ""),
        ("Ped_Official_SC_02", "Ped_Official_SC_02", ""),
        ("Ped_Monsterped_A_01", "Ped_Monsterped_A_01", ""),
        ("Ped_Monsterped_A_01B", "Ped_Monsterped_A_01B", ""),
        ("Ped_Monsterped_B_01", "Ped_Monsterped_B_01", ""),
        ("Ped_Monsterped_C_01", "Ped_Monsterped_C_01", ""),
        ("Ped_Monsterped_A_02", "Ped_Monsterped_A_02", ""),
        ("Ped_Monsterped_B_02", "Ped_Monsterped_B_02", ""),
        ("Ped_Monsterped_C_02", "Ped_Monsterped_C_02", ""),
        ("Ped_Monsterped_A_03", "Ped_Monsterped_A_03", ""),
        ("Ped_Monsterped_B_03", "Ped_Monsterped_B_03", ""),
        ("Ped_Monsterped_C_03", "Ped_Monsterped_C_03", ""),
        ("Ped_Monsterped_A_04", "Ped_Monsterped_A_04", ""),
        ("Ped_Monsterped_B_04", "Ped_Monsterped_B_04", ""),
        ("Ped_Monsterped_C_04", "Ped_Monsterped_C_04", ""),
        ("Ped_QBert", "Ped_QBert", ""),
        ("Ped_Video", "Ped_Video", ""),
        ("Ped_Photo", "Ped_Photo", ""),
        ("Ped_SCJ_Worker", "Ped_SCJ_Worker", ""),
        ("Ped_SCJ_Judge_01", "Ped_SCJ_Judge_01", ""),
        ("Ped_SCJ_Judge_02", "Ped_SCJ_Judge_02", ""),
        ("Ped_SCJ_Judge_03", "Ped_SCJ_Judge_03", ""),
        ("Ped_SCJ_Judge_04", "Ped_SCJ_Judge_04", ""),
        ("Ped_SCJ_Judge_05", "Ped_SCJ_Judge_05", ""),
        ("Ped_SCJ_Judge_06", "Ped_SCJ_Judge_06", ""),
        ("Ped_Hula", "Ped_Hula", ""),
        ("Ped_Hula2", "Ped_Hula2", ""),
        ("Ped_Bartender", "Ped_Bartender", ""),
        ("Ped_Film", "Ped_Film", ""),
        ("Ped_Bikini_1", "Ped_Bikini_1", ""),
        ("Ped_Bikini_2", "Ped_Bikini_2", ""),
        ("Ped_Bikini_3", "Ped_Bikini_3", ""),
        ("Ped_Bride", "Ped_Bride", ""),
        ("Ped_Surfer", "Ped_Surfer", ""),
        ("Ped_KISS_Paul", "Ped_KISS_Paul", ""),
        ("Ped_KISS_Peter", "Ped_KISS_Peter", ""),
        ("Ped_KISS_Ace", "Ped_KISS_Ace", ""),
        ("Ped_KISS_Gene", "Ped_KISS_Gene", ""),
        ("Ped_Freak_Sledge", "Ped_Freak_Sledge", ""),
        ("Ped_Freak_Sword", "Ped_Freak_Sword", ""),
        ("Skate_KISS_Paul", "Skate_KISS_Paul", ""),
        ("Skate_KISS_Peter", "Skate_KISS_Peter", ""),
        ("Skate_KISS_Ace", "Skate_KISS_Ace", ""),
        ("PedPro_Hawk", "PedPro_Hawk", ""),
        ("PedPro_Koston", "PedPro_Koston", ""),
        ("PedPro_Burnquist", "PedPro_Burnquist", ""),
        ("PedPro_Lasek", "PedPro_Lasek", ""),
        ("PedPro_Mullen", "PedPro_Mullen", ""),
        ("PedPro_Muska", "PedPro_Muska", ""),
        ("PedPro_Margera", "PedPro_Margera", ""),
        ("PedPro_Rodrigez", "PedPro_Rodrigez", ""),
        ("PedPro_Reynolds", "PedPro_Reynolds", ""),
        ("PedPro_Vallely", "PedPro_Vallely", ""),
        ("pedpro_Hawk_profile", "pedpro_Hawk_profile", ""),
        ("pedpro_Burnquist_profile", "pedpro_Burnquist_profile", ""),
        ("pedpro_Caballero_profile", "pedpro_Caballero_profile", ""),
        ("pedpro_Campbell_profile", "pedpro_Campbell_profile", ""),
        ("pedpro_Koston_profile", "pedpro_Koston_profile", ""),
        ("pedpro_Glifberg_profile", "pedpro_Glifberg_profile", ""),
        ("pedpro_Lasek_profile", "pedpro_Lasek_profile", ""),
        ("pedpro_Margera_profile", "pedpro_Margera_profile", ""),
        ("pedpro_Mullen_profile", "pedpro_Mullen_profile", ""),
        ("pedpro_Muska_profile", "pedpro_Muska_profile", ""),
        ("pedpro_Reynolds_profile", "pedpro_Reynolds_profile", ""),
        ("pedpro_Rowley_profile", "pedpro_Rowley_profile", ""),
        ("pedpro_Steamer_profile", "pedpro_Steamer_profile", ""),
        ("pedpro_Thomas_profile", "pedpro_Thomas_profile", ""),
        ("pedpro_Neversoft_profile", "pedpro_Neversoft_profile", ""),
        ("Ped_Fratjacket_a", "Ped_Fratjacket_a", ""),
        ("Ped_FratGuy_a", "Ped_FratGuy_a", ""),
        ("Ped_FratGuy_b", "Ped_FratGuy_b", ""),
        ("Ped_Basketball_b", "Ped_Basketball_b", ""),
        ("Ped_Basketball_c", "Ped_Basketball_c", ""),
        ("Ped_Basketball_d", "Ped_Basketball_d", ""),
        ("Ped_Tennis_a", "Ped_Tennis_a", ""),
        ("Ped_Tennis_b", "Ped_Tennis_b", ""),
        ("Ped_London_cop_a", "Ped_London_cop_a", ""),
        ("Ped_London_Bikecop_a", "Ped_London_Bikecop_a", ""),
        ("Ped_Protestor_a", "Ped_Protestor_a", ""),
        ("Ped_Protestor_b", "Ped_Protestor_b", ""),
        ("Ped_Protestor_c", "Ped_Protestor_c", ""),
        ("Ped_Skank_a", "Ped_Skank_a", ""),
        ("Ped_Mechanic_a", "Ped_Mechanic_a", ""),
        ("Ped_Fisherman_a", "Ped_Fisherman_a", ""),
        ("Ped_Kid_grommit_a", "Ped_Kid_grommit_a", ""),
        ("Ped_Jogger_Female_a", "Ped_Jogger_Female_a", ""),
        ("Ped_Kid_grommit_b", "Ped_Kid_grommit_b", ""),
        ("Ped_DockWorker_a", "Ped_DockWorker_a", ""),
        ("Ped_DockWorker_b", "Ped_DockWorker_b", ""),
        ("Ped_DockWorker_c", "Ped_DockWorker_c", ""),
        ("Ped_Foreman_a", "Ped_Foreman_a", ""),
        ("Ped_Foreman_b", "Ped_Foreman_b", ""),
        ("Ped_DeliveryGuy", "Ped_DeliveryGuy", ""),
        ("Ped_Stroller_a", "Ped_Stroller_a", ""),
        ("Ped_Zooemployee_b", "Ped_Zooemployee_b", ""),
        ("Ped_Elephant_Trainer_a", "Ped_Elephant_Trainer_a", ""),
        ("Ped_Liontamer_a", "Ped_Liontamer_a", ""),
        ("Ped_Clown", "Ped_Clown", ""),
        ("Ped_Rasta", "Ped_Rasta", ""),
        ("Ped_VanGuy", "Ped_VanGuy", ""),
        ("Ped_Mob_rifle", "Ped_Mob_rifle", ""),
        ("Ped_Kid_a", "Ped_Kid_a", ""),
        ("Ped_Girl", "Ped_Girl", ""),
        ("Ped_Kid_Balloon_a", "Ped_Kid_Balloon_a", ""),
        ("sample_pedestrian_a", "sample_pedestrian_a", ""),
        ("sample_pedestrian_b", "sample_pedestrian_b", "")),

    name="Profile Name", default="random_male_profile")
    ped_animset = StringProperty(name="Anim Set", description="Anim set to load for this pedestrian. Leave empty to use the default anim set.")
    ped_extra_anims = StringProperty(name="Extra Anims", description="Additional anim sets to load.")



# METHODS
#############################################
#----------------------------------------------------------------------------------
def __init_wm_props():
    def make_updater(flag):
        return lambda wm, ctx: update_collision_flag_mesh(wm, ctx, flag)

    FLAG_NAMES = {
        "mFD_VERT": ("Vert", "Vert. This face is a vert (used for ramps)."),
        "mFD_WALL_RIDABLE": ("Wallridable", "Wallridable. This face is wallridable"),
        "mFD_NON_COLLIDABLE": ("Non-Collidable", "Non-Collidable. The skater won't collide with this face. Used for triggers."),
        "mFD_NO_SKATER_SHADOW": ("No Skater Shadow", "No Skater Shadow"),
        "mFD_NO_SKATER_SHADOW_WALL": ("No Skater Shadow Wall", "No Skater Shadow Wall"),
        "mFD_TRIGGER": ("Trigger", "Trigger. The object's TriggerScript will be called when a skater goes through this face. Caution: if the object doesn't have a triggerscript defined the game will crash!"),
    }

    for ff in SETTABLE_FACE_FLAGS:
        fns = FLAG_NAMES.get(ff)
        if fns:
            fn, fd = fns
        else:
            fn = ff
            fd = ff
        setattr(bpy.types.WindowManager,
                "thug_face_" + ff,
                BoolProperty(name=fn,
                             description=fd,
                             update=make_updater(ff)))

    bpy.types.WindowManager.thug_autorail_terrain_type = EnumProperty(
        name="Autorail Terrain Type",
        items=[(t, t, t) for t in ["None", "Auto"] + [tt for tt in TERRAIN_TYPES if tt.lower().startswith("grind")]],
        update=update_autorail_terrain_type)

    bpy.types.WindowManager.thug_face_terrain_type = EnumProperty(
        name="Terrain Type",
        items=[(t, t, t) for t in ["Auto"] + TERRAIN_TYPES],
        update=update_terrain_type_mesh)

    bpy.types.WindowManager.thug_show_face_collision_colors = BoolProperty(
        name="Colorize faces and edges",
        description="Colorize faces and edges in the 3D view according to their collision flags and autorail settings.",
        default=True)
#----------------------------------------------------------------------------------
def register_props():
    __init_wm_props()
    bpy.types.Object.thug_object_class = EnumProperty(
        name="Object Class",
        description="Object Class.",
        items=[
            ("LevelGeometry", "LevelGeometry", "LevelGeometry. Use for static geometry."),
            ("LevelObject", "LevelObject", "LevelObject. Use for dynamic objects.")],
        default="LevelGeometry")
    bpy.types.Object.thug_do_autosplit = BoolProperty(
        name="Autosplit Object on Export",
        description="Split object into multiple smaller objects of sizes suitable for the THUG engine. Note that this will create multiple objects, which might cause issues with scripting. Using this for LevelObjects or objects used in scripts is not advised.",
        default=False)
    bpy.types.Object.thug_node_expansion = StringProperty(
        name="Node Expansion",
        description="The struct with this name will be merged to this node's definition in the NodeArray.",
        default="")
    bpy.types.Object.thug_do_autosplit_faces_per_subobject = IntProperty(
        name="Faces Per Subobject",
        description="The max amount of faces for every created subobject.",
        default=300, min=50, max=6000)
    bpy.types.Object.thug_do_autosplit_max_radius = FloatProperty(
        name="Max Radius",
        description="The max radius of for every created subobject.",
        default=2000, min=100, max=5000)
    """
    bpy.types.Object.thug_do_autosplit_preserve_normals = BoolProperty(
        name="Preserve Normals",
        description="Preserve the normals of the ",
        default=True)
    """
    bpy.types.Object.thug_col_obj_flags = IntProperty()
    bpy.types.Object.thug_created_at_start = BoolProperty(name="Created At Start", default=True)
    bpy.types.Object.thug_network_option = EnumProperty(
        name="Network Options",
        items=[
            ("Default", "Default", "Appears in network games."),
            ("AbsentInNetGames", "Offline Only", "Only appears in single-player."),
            ("NetEnabled", "Online (Broadcast)", "Appears in network games, events/scripts appear on all clients.")],
        default="Default")
    bpy.types.Object.thug_export_collision = BoolProperty(name="Export to Collisions", default=True)
    bpy.types.Object.thug_export_scene = BoolProperty(name="Export to Scene", default=True)
    bpy.types.Object.thug_always_export_to_nodearray = BoolProperty(name="Always Export to Nodearray", default=False)
    bpy.types.Object.thug_occluder = BoolProperty(name="Occluder", description="Occludes (hides) geometry behind this mesh. Used for performance improvements.", default=False)
    bpy.types.Object.thug_is_trickobject = BoolProperty(
        name="Is a TrickObject",
        default=False,
        description="This must be checked if you want this object to be taggable in Graffiti.")
    bpy.types.Object.thug_cluster_name = StringProperty(
        name="TrickObject Cluster",
        description="The name of the graffiti group this object belongs to. If this is empty and this is a rail with a mesh object parent this will be set to the parent's name. Otherwise it will be set to this object's name.")
    bpy.types.Object.thug_path_type = EnumProperty(
        name="Path Type",
        items=[
            ("None", "None", "None"),
            ("Rail", "Rail", "Rail"),
            ("Ladder", "Ladder", "Ladder"),
            ("Waypoint", "Waypoint", "Navigation path for pedestrians/vehicles/AI skaters."),
            ("Custom", "Custom", "Custom")],
        default="None")
    bpy.types.Object.thug_rail_terrain_type = EnumProperty(
        name="Rail Terrain Type",
        items=[(t, t, t) for t in ["Auto"] + TERRAIN_TYPES],
        default="Auto")
    bpy.types.Object.thug_rail_connects_to = StringProperty(name="Linked To", description="Path this object links to (must be a rail/ladder/waypoint).")

    bpy.types.Object.thug_triggerscript_props = PointerProperty(type=THUGObjectTriggerScriptProps)

    bpy.types.Object.thug_empty_props = PointerProperty(type=THUGEmptyProps)
    
    bpy.types.Object.thug_proxim_props = PointerProperty(type=THUGProximNodeProps)
    bpy.types.Object.thug_generic_props = PointerProperty(type=THUGGenericNodeProps)
    bpy.types.Object.thug_restart_props = PointerProperty(type=THUGRestartProps)
    bpy.types.Object.thug_go_props = PointerProperty(type=THUGGameObjectProps)
    bpy.types.Object.thug_ped_props = PointerProperty(type=THUGPedestrianProps)
    
    bpy.types.Curve.thug_pathnode_triggers = CollectionProperty(type=THUGPathNodeProps)
    
    bpy.types.Image.thug_image_props = PointerProperty(type=THUGImageProps)

    bpy.types.Material.thug_material_props = PointerProperty(type=THUGMaterialProps)
    bpy.types.Texture.thug_material_pass_props = PointerProperty(type=THUGMaterialPassProps)

    bpy.types.WindowManager.thug_all_rails = CollectionProperty(type=bpy.types.PropertyGroup)
    bpy.types.WindowManager.thug_all_restarts = CollectionProperty(type=bpy.types.PropertyGroup)

    # bpy.utils.unregister_class(ExtractRail)
    # bpy.utils.register_class(ExtractRail)
    bpy.utils.unregister_class(THUGImportNodeArray)
    bpy.utils.register_class(THUGImportNodeArray)
    
    #_update_pathnodes_collections()
    
    global draw_handle
    draw_handle = bpy.types.SpaceView3D.draw_handler_add(draw_stuff, (), 'WINDOW', 'POST_VIEW')
    # bpy.app.handlers.scene_update_pre.append(draw_stuff_pre_update)
    bpy.app.handlers.scene_update_post.append(draw_stuff_post_update)
    bpy.app.handlers.scene_update_post.append(update_collision_flag_ui_properties)

    bpy.app.handlers.load_pre.append(draw_stuff_pre_load_cleanup)
    
    
#----------------------------------------------------------------------------------
def unregister_props():
    bgl.glDeleteLists(draw_stuff_display_list_id, 1)

    # bpy.utils.unregister_class(ExtractRail)
    bpy.utils.unregister_class(THUGImportNodeArray)

    global draw_handle
    if draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handle, 'WINDOW')
        draw_handle = None

    """
    if draw_stuff_pre_update in bpy.app.handlers.scene_update_pre:
        bpy.app.handlers.scene_update_pre.remove(draw_stuff_pre_update)
    """

    if update_collision_flag_ui_properties in bpy.app.handlers.scene_update_post:
        bpy.app.handlers.scene_update_post.remove(update_collision_flag_ui_properties)

    if draw_stuff_post_update in bpy.app.handlers.scene_update_post:
        bpy.app.handlers.scene_update_post.remove(draw_stuff_post_update)

    if draw_stuff_pre_load_cleanup in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(draw_stuff_pre_load_cleanup)
