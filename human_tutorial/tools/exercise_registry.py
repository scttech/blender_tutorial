"""exercise_registry.py - the ONE list of exercises. Read by build_all_actions.py (inside Blender) and check_actions.py (plain Python).

To add an exercise: write its table in tools/exercises/, add one entry below, run build_all_actions.py in Blender, then
python3 tools/check_actions.py. Fields:
  name        the Blender action's name (and the exports/<name>_measure.json file, lower case)
  module      the file in tools/exercises/ that defines the table
  table       the name of the table (a list of (frame, pose)) inside that module
  keys        the keyframes to mark on charts
  extra       None, or (function in the module, argument): extra per-frame measurements for measure()
  checks      which of the OPTIONAL checks apply:
                "ankles"    the ankles must not move (feet planted)
                "contacts"  the planted contacts (ball of the foot, wrist) must not move (floor work: the ankles travel on an arc)
                "balance"   the centre of mass must stay over the feet (standing exercises)
  clearance   [(measurement key, minimum in mm)]: a prop must stay at least this far from the body on EVERY frame
  loop_key    which per-frame value to test the loop seam on (default hips_z)
  notes       limits of the checks for this exercise, shown under the table
Every exercise also gets these checks automatically: hands reach their targets, nothing sinks through the floor, the loop is seamless,
no joint sits at its IK limit, the skin does not stretch past x3, and it plays identically after any other action.
"""
EXERCISES = [
    dict(name="Squat", module="squat", table="SQUAT", keys=[1, 25, 33, 61], extra=None, checks=["ankles", "balance"], clearance=[],
         notes="balance uses the body only; the arms are held forward"),
    dict(name="Pushup", module="pushup", table="PUSHUP", keys=[1, 31, 37, 67], extra=("contact_extra", None), checks=["contacts"], clearance=[],
         notes="the ankles travel on an arc by design, so the contacts (ball of the foot, wrist) are checked instead"),
    dict(name="Situp", module="situp", table="SITUP", keys=[1, 34, 40, 79], extra=None, checks=["ankles"], clearance=[],
         notes="the crossed arms are folded as tight as the elbow limit allows"),
    dict(name="Pullup", module="pullup", table="PULLUP", keys=[1, 46, 52, 100], extra=("bar_extra", "BarOver_Grip"), checks=[],
         clearance=[("bar_clear_mm", 20)], notes="the feet hang free; the hands are held to the bar by the grab slider"),
    dict(name="Chinup", module="pullup", table="CHINUP", keys=[1, 46, 52, 100], extra=("bar_extra", "BarUnder_Grip"), checks=[],
         clearance=[("bar_clear_mm", 20)], notes="the feet hang free; mild wrist pinch in the underhand grip (Step 15)"),
    dict(name="Lunge", module="lunge", table="LUNGE", keys=[1, 25, 33, 57], extra=None, checks=["ankles", "balance"], clearance=[],
         notes="a static lunge (split squat): the feet stay put. A walking lunge needs the feet keyed from step to step"),
    dict(name="Kbswing", module="kbswing", table="KBSWING", keys=[1, 27, 53], extra=("bell_extra", None), checks=["ankles", "balance"],
         clearance=[("bell_clear_mm", 20)], notes="balance uses the body only: the bell's weight is not included"),
    dict(name="Mace10to2", module="mace", table="MACE_10_TO_2", keys=[1, 16, 31], extra=("mace_extra", None), checks=["ankles", "balance"],
         clearance=[("clear_shaft_mm", 20), ("clear_head_mm", 50)], loop_key="head_x", notes="balance uses the body only: the mace's weight is not included"),
]
