"""exercise_registry.py - the ONE list of exercises. Read by build_all_actions.py (inside Blender) and check_actions.py (plain Python).

To add an exercise: write its table in tools/exercises/, add one entry below, run build_all_actions.py in Blender, then
python3 tools/check_actions.py. Fields:
  name        the Blender action's name (and the exports/<name>_measure.json file, lower case)
  module      the file in tools/exercises/ that defines the table
  table       the name of the table (a list of (frame, pose)) inside that module
  file        INSTEAD of module and table: a .toml text description in tools/exercises/ (see exercise_dsl.py)
  keys        the keyframes to mark on charts
  extra       None, or (function in the module, argument): extra per-frame measurements for measure()
  checks      which of the OPTIONAL checks apply:
                "ankles"    the ankles must not move (feet planted)
                "contacts"  the planted contacts (ball of the foot, wrist) must not move (floor work: the ankles travel on an arc)
                "balance"   the centre of mass must stay over the feet (standing exercises)
  clearance   [(measurement key, minimum in mm)]: a prop must stay at least this far from the body on EVERY frame
  support_frame  the frame whose soles define the base of support for the balance check (default 1; use a later frame when the feet end up apart, as in a lunge)
  loop_key    which per-frame value to test the loop seam on (default hips_z)
  notes       limits of the checks for this exercise, shown under the table
Every exercise also gets these checks automatically: hands reach their targets, nothing sinks through the floor, the loop is seamless,
no joint sits at its IK limit, the skin does not stretch past x3, and it plays identically after any other action.
"""
EXERCISES = [
    dict(name="Squat", file="squat.toml", keys=[1, 25, 33, 61], extra=None, checks=["ankles", "balance"], clearance=[],
         notes="hands behind the head; balance uses the body only"),
    dict(name="Pushup", file="pushup.toml", keys=[1, 31, 37, 67], extra=("contact_extra", None), checks=["contacts"], clearance=[],
         notes="the ankles travel on an arc by design, so the contacts (ball of the foot, wrist) are checked instead"),
    dict(name="Situp", module="situp", table="SITUP", keys=[1, 34, 40, 79], extra=None, checks=["ankles"], clearance=[],
         notes="the crossed arms are folded as tight as the elbow limit allows"),
    dict(name="Pullup", module="pullup", table="PULLUP", keys=[1, 46, 52, 100], extra=("bar_extra", "BarOver_Grip"), checks=[],
         clearance=[("bar_clear_mm", 20)], notes="the feet hang free; the hands are held to the bar by the grab slider"),
    dict(name="Chinup", module="pullup", table="CHINUP", keys=[1, 46, 52, 100], extra=("bar_extra", "BarUnder_Grip"), checks=[],
         clearance=[("bar_clear_mm", 20)], notes="the feet hang free; mild wrist pinch in the underhand grip (Step 15)"),
    dict(name="Lunge", file="lunge.toml", keys=[1, 25, 33, 57], extra=None, checks=["ankles", "balance"], clearance=[],
         notes="a static lunge (split squat): the feet stay put. A walking lunge needs the feet keyed from step to step"),
    dict(name="Kbswing", module="kbswing", table="KBSWING", keys=[1, 27, 53], extra=("bell_extra", None), checks=["ankles", "balance"],
         clearance=[("bell_clear_mm", 20), ("arm_clear_mm", 5)], notes="balance uses the body only: the bell's weight is not included"),
    dict(name="Mace10to2", file="mace_10_to_2.toml", keys=[1, 16, 31, 46, 61], extra=("mace_extra", None), checks=["ankles", "balance"],
         clearance=[("clear_head_mm", 20)], loop_key="head_x", notes="balance uses the body only: the mace's weight is not included"),
    dict(name="HalfSquat", file="half_squat.toml", keys=[1, 25, 33, 61], extra=None, checks=["ankles", "balance"], clearance=[],
         notes="written as text, extending squat.toml: a demonstration of exercise_dsl.py, not an exercise from the app"),
    dict(name="DiamondPushup", file="diamond_pushup.toml", keys=[1, 31, 37, 67], extra=("contact_extra", None), checks=["contacts"], clearance=[],
         notes="the push-up with the hands 5 cm from the centre line"),
    dict(name="ReverseLunge", file="reverse_lunge.toml", keys=[1, 20, 32, 40, 52, 70], support_frame=32, extra=None, checks=["balance"], clearance=[],
         notes="the front foot is planted for the whole loop; the rear foot steps back and in, so only the front ankle is checked"),
    dict(name="GobletSquat", file="goblet_squat.toml", keys=[1, 25, 33, 61], extra=("bell_extra", None), checks=["ankles", "balance"], clearance=[("bell_clear_mm", 20)],
         notes="a kettlebell held at the chest; balance uses the body only (the bell's weight is not included)"),
    dict(name="MaceSquat", file="mace_squat.toml", keys=[1, 25, 33, 61], extra=("mace_extra", None), checks=["ankles", "balance"], clearance=[("clear_shaft_mm", 20), ("clear_head_mm", 50)],
         notes="the mace is held upright at the chest; balance uses the body only"),
    dict(name="KettlebellLunge", file="kettlebell_lunge.toml", keys=[1, 25, 33, 57], extra=("bell_extra", None), checks=["ankles", "balance"], clearance=[("bell_clear_mm", 20)],
         notes="a static lunge holding a kettlebell at the chest; balance uses the body only"),
    dict(name="MaceReverseLunge", file="mace_reverse_lunge.toml", keys=[1, 20, 32, 40, 52, 70], support_frame=32, extra=("mace_extra", None), checks=["balance"],
         clearance=[("clear_shaft_mm", 20), ("clear_head_mm", 50)], notes="the mace is held upright at the chest; balance uses the body only"),
    dict(name="Crunch", file="crunch.toml", keys=[1, 24, 36, 72], extra=None, checks=["ankles"], clearance=[],
         notes="the lying body of the sit-up with the pelvis flat and a 30 degree curl; hands behind the head"),
    dict(name="HangingLegRaise", file="hanging_leg_raise.toml", keys=[1, 31, 40, 76], extra=("bar_extra", "BarOver_Grip"), checks=[], clearance=[("bar_clear_mm", 20)],
         notes="the legs are kept a little short of straight so the knee stays inside its limit"),
    dict(name="KettlebellDeadlift", file="kettlebell_deadlift.toml", keys=[1, 31, 41, 71], extra=("bell_extra", None), checks=["ankles", "balance"], clearance=[("bell_clear_mm", 20), ("arm_clear_mm", 5)],
         notes="balance uses the body only; the bell's weight is not included"),
    dict(name="Plank", file="plank.toml", keys=[1, 31, 61], extra=("contact_extra", None), checks=["contacts"], clearance=[], notes="a held position with a slow sway"),
    dict(name="GluteBridge", file="glute_bridge.toml", keys=[1, 28, 40, 72], extra=None, checks=["ankles"], clearance=[], notes="the arms lie on the floor"),
    dict(name="KettlebellRussianTwist", file="kettlebell_russian_twist.toml", keys=[1, 16, 46, 61], extra=None, checks=["ankles"], clearance=[], notes="a seated twist; the bell rides on the chest"),
    dict(name="MaceRussianTwist", file="mace_russian_twist.toml", keys=[1, 16, 46, 61], extra=("mace_extra", None), checks=["ankles"], clearance=[], notes="a seated twist with the mace upright at the chest"),
    dict(name="MaceOverheadPress", file="mace_overhead_press.toml", keys=[1, 31, 36, 71], extra=("mace_extra", None), checks=["ankles", "balance"], clearance=[("clear_shaft_mm", 20), ("clear_head_mm", 50)], notes="balance uses the body only"),
    dict(name="MaceGoodMorning", file="mace_good_morning.toml", keys=[1, 31, 41, 71], extra=("mace_extra", None), checks=["ankles", "balance"], clearance=[], notes="the mace lies across the upper back, so its clearance is not checked"),
    dict(name="MaceBarbarianSquat", file="mace_barbarian_squat.toml", keys=[1, 25, 33, 61], extra=("mace_extra", None), checks=["ankles", "balance"], clearance=[], notes="the mace lies across the upper back, so its clearance is not checked"),
    dict(name="KettlebellHalo", file="kettlebell_halo.toml", keys=[1, 19, 73, 97, 100, 193], extra=("bell_extra", None), checks=["ankles", "balance"], clearance=[("bell_clear_mm", -10)], notes="the hands circle above the head and the bell hangs beside it; it grazes the head by up to 7 mm (the check allows 10)"),
    dict(name="DeadBug", file="dead_bug.toml", keys=[1, 16, 31, 46, 61], extra=None, checks=[], clearance=[], notes="the feet are in the air: no planted contacts to check"),
    dict(name="SquatHandsTogether", file="squat_hands_together.toml", keys=[1, 25, 33, 61], extra=None, checks=["ankles", "balance"], clearance=[], notes="arms at the sides standing; the hands come together in front of the chest at the bottom"),
    dict(name="CalfRaise", file="calf_raise.toml", keys=[1, 25, 37, 61], extra=None, checks=["balance"], clearance=[], notes="the heels lift; the toes stay on the floor"),
    dict(name="StandingTorsoTwist", file="standing_torso_twist.toml", keys=[1, 16, 31, 46, 61], extra=None, checks=["ankles", "balance"], clearance=[], notes="the arms swing with the chest"),
    dict(name="JumpingJack", file="jumping_jack.toml", keys=[1, 16, 31], extra=None, checks=[], clearance=[], notes="the feet leave the floor by 12 cm halfway; the legs are kept just short of straight"),
    dict(name="LegRaise", file="leg_raise.toml", keys=[1, 31, 37, 67], extra=None, checks=[], clearance=[], notes="straight legs raised to 60 degrees above the floor, feet held at one angle"),
    dict(name="FlutterKicks", file="flutter_kicks.toml", keys=[1, 7, 13, 25], extra=None, checks=[], clearance=[], notes="a fast alternating kick, keyed every 2 frames"),
    dict(name="BicycleCrunch", file="bicycle_crunch.toml", keys=[1, 16, 31, 46, 61], extra=None, checks=[], clearance=[], notes="the feet are in the air; hands behind the head"),
    dict(name="VUp", file="v_up.toml", keys=[1, 31, 37, 67], extra=None, checks=[], clearance=[], notes="the hands reach toward the ankles"),
    dict(name="StandingHipAbduction", file="standing_hip_abduction.toml", keys=[1, 25, 37, 61], extra=None, checks=["balance"], clearance=[], notes="the right hand rests on a rail 52 cm out (not modelled); balance uses both feet"),
    dict(name="RussianTwist", file="russian_twist.toml", keys=[1, 16, 46, 61], extra=None, checks=["ankles"], clearance=[], notes="seated twist, hands together"),
    dict(name="MountainClimber", file="mountain_climber.toml", keys=[1, 7, 13, 19, 25], extra=("contact_extra", None), checks=[], clearance=[], notes="the hands are planted; the feet alternate, so only the hands are checked for drift"),
    dict(name="Superman", file="superman.toml", keys=[1, 25, 37, 73], extra=None, checks=[], clearance=[], notes="lying face down"),
    dict(name="BirdDog", file="bird_dog.toml", keys=[1, 31, 61, 91, 121], extra=None, checks=[], clearance=[], notes="the planted hand and knee are on the floor; the extending limbs are in the air"),
    dict(name="JumpSquat", file="jump_squat.toml", keys=[1, 13, 19, 25, 31, 45], extra=None, checks=[], clearance=[], notes="the feet leave the floor by 30 cm"),
    dict(name="SingleLegBalance", file="single_leg_balance.toml", keys=[1, 19, 73, 94], extra=None, checks=["balance"], clearance=[], notes="the right hand rests on a rail (not modelled)"),
    dict(name="HeelDrop", file="heel_drop.toml", keys=[1, 19, 25, 28, 40], extra=None, checks=["balance"], clearance=[], notes="the drop takes 3 frames"),
    dict(name="ChinTuck", file="chin_tuck.toml", keys=[1, 19, 49, 67], extra=None, checks=["ankles", "balance"], clearance=[], notes="the head slides back about 4 cm"),
    dict(name="CatCow", file="cat_cow.toml", keys=[1, 31, 61, 91, 121], extra=None, checks=[], clearance=[], notes="the hands and knees are planted; the spine curves"),
    dict(name="ThoracicRotation", file="thoracic_rotation.toml", keys=[1, 31, 61, 91, 121], extra=None, checks=[], clearance=[], notes="the left hand is behind the head; the right hand and knees are planted"),
    dict(name="HipCircles", file="hip_circles.toml", keys=[1, 31, 61, 91, 121], extra=None, checks=[], clearance=[], notes="the right hand rests on a rail (not modelled)"),
    dict(name="HamstringStretch", file="hamstring_stretch.toml", keys=[1, 37, 101, 141], extra=None, checks=[], clearance=[], notes="the front foot is off its rest position (heel forward, toes up)"),
    dict(name="HipFlexorStretch", file="hip_flexor_stretch.toml", keys=[1, 37, 101, 141], support_frame=37, extra=None, checks=["balance"], clearance=[], notes="a half-kneeling lunge; hands on the hips"),
    dict(name="NeckShoulderRolls", file="neck_shoulder_rolls.toml", keys=[1, 46, 91, 154], extra=None, checks=["ankles", "balance"], clearance=[], notes="the shoulders roll through 9 degrees of clavicle motion"),
]
