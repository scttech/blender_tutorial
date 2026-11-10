"""make_catalog.py - build exercise-catalog.md from the app's StarterExercises.kt (a copy is kept in exports/StarterExercises.kt.txt).
    python3 -I tools/make_catalog.py [path to StarterExercises.kt]
The Kotlin file gives name, category and equipment. The CLASSIFICATION below (status, technique family, fixtures) is OUR judgement, not the app's:
edit it here and re-run. Every exercise in the file must be classified (the script stops otherwise)."""
import re, sys, os
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); HOME = os.path.dirname(HERE)
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HOME, "exports", "StarterExercises.kt.txt")
ex = re.findall(r'Exercise\(\s*name = "([^"]+)",\s*category = ExerciseCategory\.(\w+),\s*equipment = ExerciseEquipment\.(\w+)', open(SRC).read())

# status -> (meaning, list of names). "Goblet Squat" is in the app twice (dumbbell and kettlebell); one entry covers both.
G = {
 "Built": ["Pistol Squat", "Skater Hop", "Box Breathing", "Cat-Cow", "Thoracic Spine Rotation", "Hip Circles", "Hamstring Stretch", "Hip Flexor Stretch", "Neck and Shoulder Rolls", "Russian Twist", "Mountain Climber", "Superman", "Bird Dog", "Jump Squat", "Single-Leg Balance", "Heel Drop", "Chin Tuck", "Calf Raise", "Jumping Jack", "Standing Torso Twist", "Standing Hip Abduction", "Leg Raise", "Flutter Kicks", "Bicycle Crunch", "V-Up", "Plank", "Glute Bridge", "Dead Bug", "Kettlebell Russian Twist", "Mace Russian Twist", "Mace Overhead Press", "Mace Good Morning", "Mace Barbarian Squat", "Kettlebell Halo", "Diamond Push-Up", "Reverse Lunge", "Mace Reverse Lunge", "Kettlebell Lunge", "Mace Squat", "Crunch", "Hanging Leg Raise", "Goblet Squat", "Kettlebell Deadlift", "Push-Up", "Pull-Up", "Chin-Up", "Bodyweight Squat", "Air Squat", "Sit-Up", "Lunge", "Kettlebell Swing", "Mace 10-to-2 Swing"],
 "Variant": [],
 "New": ["Side Plank", "Burpee",
         "World's Greatest Stretch", "90/90 Hip Stretch",
         "Child's Pose", "Stretching / Mobility Flow",
         "Pike Push-Up", "Pelvic Floor Contraction (Kegel)",
         "Mace 360 Swing", "Mace Front Raise (Around the World)", "Mace Uppercut", "Mace Shield Cast"],
 "Fixture": ["Wall Push-Up", "Incline Push-Up", "Decline Push-Up", "Wall Sit", "Wall Angel", "Doorway Chest Stretch", "Sit-to-Stand", "Inverted Row", "Dip",
             "Box Jump", "Step-Up", "Bulgarian Split Squat", "Hip Thrust"],
 "One hand": ["Kettlebell Press", "Kettlebell Thruster", "Kettlebell Row", "Kettlebell Clean", "Kettlebell Clean and Press", "Kettlebell Snatch", "Mace Single-Arm Swing"],
 "Dumbbell": ["Farmer's Carry", "Dumbbell Bench Press", "Incline Dumbbell Press", "Dumbbell Fly", "Single-Arm Dumbbell Row", "Arnold Press", "Dumbbell Shoulder Press",
              "Lateral Raise", "Front Raise", "Rear Delt Fly", "Dumbbell Shrug", "Dumbbell Bicep Curl", "Hammer Curl", "Concentration Curl",
              "Overhead Tricep Extension", "Walking Lunge", "Man Maker", "Devil's Press"],
 "Barbell": ["Back Squat", "Deadlift", "Overhead Press", "Bent-Over Row", "Barbell Bench Press", "Incline Barbell Bench Press", "Romanian Deadlift", "Sumo Deadlift",
             "Pendlay Row", "Good Morning", "Upright Row", "Barbell Curl", "Skull Crusher", "Close-Grip Bench Press", "Front Squat", "Clean and Press", "Thruster"],
 "Machine": ["Machine Chest Press", "Pec Deck Fly", "Cable Crossover", "Seated Cable Row", "Lat Pulldown", "T-Bar Row", "Preacher Curl", "Tricep Pushdown", "Leg Press",
             "Leg Extension", "Leg Curl", "Row (Erg/Rower)", "Treadmill Run", "Stationary Cycling", "Assault Bike", "Stair Climber", "Elliptical"],
 "Small prop": ["Face Pull", "Band Pull-Apart", "Band Curl", "Band Shoulder Dislocate", "Pallof Press", "Jump Rope", "Ab Wheel Rollout", "Wall Ball", "Battle Ropes", "Foam Rolling"],
 "Technique": ["Bear Crawl", "Handstand Push-Up", "Turkish Get-Up", "Kettlebell Farmer's Carry", "Outdoor Run", "Brisk Walk", "Shuttle Runs", "High Knees", "Marching in Place",
               "Tandem Walk", "Hip Escape (Shrimp)", "Technical Stand-Up", "Bridge and Roll (Upa)", "Granby Roll", "Forward and Backward Break-Fall Roll", "Guard Walk Sit-Up"],
 "Partner": ["Leg Pummeling"],   # plus every GRAPPLING_DUMMY exercise, added below
}
MEANING = {
 "Built": "done: an action exists in the Blender file and passes the checks (from the text files in tools/exercises/ or the earlier Python tables)",
 "Variant": "an existing table with changed numbers or one changed grab; no new technique",
 "New": "a new table, using techniques and props we already have",
 "Fixture": "the motion is easy; it needs a bench, box, wall, chair or parallel bars modelled first (a static prop with no bones)",
 "One hand": "needs a one-handed grip on the prop: the grab sliders drive BOTH hands, so a single-arm press, row, clean or snatch needs a per-hand grab added to the rig first",
 "Dumbbell": "needs a dumbbell prop with grips (two hands, or one), and a bench for some",
 "Barbell": "needs a barbell prop with a two-hand grip, plus a rack or bench for most",
 "Machine": "needs a machine or cable fixture modelled; the person mostly sits or stands still",
 "Small prop": "needs a band, rope, wheel, ball or roller; bands and ropes bend, which a rigid prop bone cannot do",
 "Technique": "needs something the animation library cannot do yet: travel across the floor (root motion), a gait cycle, inversion, or rolling and floor-to-standing transitions",
 "Partner": "needs a second figure (a grappling dummy or a training partner), which means a second rig",
}
status = {}
for s, names in G.items():
    for n in names:
        assert n not in status, f"{n} classified twice"; status[n] = s
for n, c, e in ex:
    if e == "GRAPPLING_DUMMY": status[n] = "Partner"
missing = sorted({n for n, _, _ in ex} - set(status)); extra = sorted(set(status) - {n for n, _, _ in ex})
assert not missing, f"unclassified: {missing}"; assert not extra, f"not in the app file: {extra}"

order = list(MEANING); cats = ["CHEST", "BACK", "SHOULDERS", "ARMS", "LEGS", "CORE", "FULL_BODY", "CARDIO", "MOBILITY", "MARTIAL_ARTS"]
cnt = Counter(status[n] for n, _, _ in ex)
out = ["# Exercise catalogue", "",
       f"The {len(ex)} exercises in the app's [StarterExercises.kt](https://github.com/scttech/open_fitness/blob/main/app/src/main/java/com/scttech/android/kotlin/openfitness/domain/template/StarterExercises.kt) "
       "(a copy is in `exports/StarterExercises.kt.txt`), each with what it would take to animate with the library from [Step 17](17-the-exercise-recipe.md).", "",
       "The name, category and equipment come from the app. **The status column is our judgement, made from the exercise names and without trying them.** "
       "Treat it as a first sort; it is generated by `tools/make_catalog.py`, so correct it there.", "",
       "## Status", "", "| Status | Count | Meaning |", "|---|---|---|"]
out += [f"| **{s}** | {cnt[s]} | {MEANING[s]} |" for s in order]
out += ["", f"Total {sum(cnt.values())}. The app lists *Goblet Squat* twice (dumbbell and kettlebell), so it counts twice here and shares one classification.", "",
        "## Suggested order", "",
        "1. **Variants** (7): done.",
        "2. **New** (the remaining ones): no new modelling. Plank, glute bridge, dead bug, the Russian twists, the mace press, good morning and barbarian squat and the kettlebell halo are done.",
        "3. **Dumbbell, then barbell** (35): one prop each with grips, then many exercises. These are the biggest payoff per prop.",
        "4. **Fixtures** (13) and **small props** (10): a bench, box and wall unlock many at once.",
        "5. **Technique** (16): each needs a new library feature first (root motion, a gait cycle, rolling). Do them last, one feature at a time.",
        "6. **Machines** (17) and **Partner** (16): the most modelling for the least variety. Decide later whether the app needs them animated at all.", ""]
by = defaultdict(list)
for n, c, e in ex: by[c].append((n, e))
for c in cats:
    out += [f"## {c.replace('_', ' ').title()} ({len(by[c])})", "", "| Exercise | Equipment | Status |", "|---|---|---|"]
    out += [f"| {n} | {e.replace('_', ' ').title()} | {status[n]} |" for n, e in by[c]]
    out.append("")
out += ["---", "", "[Contents](README.md)"]
open(os.path.join(HOME, "exercise-catalog.md"), "w").write("\n".join(out) + "\n")
print(len(ex), dict(cnt))
