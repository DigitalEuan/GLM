"""
ubp_py_lang.py v2.0
===========================================
Date updated: 31 march 2026
Author: E R A Craig, New Zealand
"""
import shlex
from ubp_py_runtime import UBPPyVM
from ubp_viz import save_scene_3d

def execute_program(vm, text):
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
    
    for line in lines:
        tokens = shlex.split(line)
        if not tokens: continue
        op = tokens[0].upper()

        try:
            if op == "LET":
                # LET <label> <value> [TIER <n>] [CAT <cat>]
                tier = 0
                cat = "QUANTITY"
                if "TIER" in tokens: tier = int(tokens[tokens.index("TIER")+1])
                if "CAT" in tokens: cat = tokens[tokens.index("CAT")+1]
                vm.let(tokens[1], tokens[2], tier, cat)
                
            elif op == "STATE":
                # STATE <label> PARAMS k=v,k=v SCHEMA k=min:max:bits,k=min:max:bits [CAT cat]
                label = tokens[1]
                params_str = tokens[tokens.index("PARAMS")+1]
                schema_str = tokens[tokens.index("SCHEMA")+1]
                cat = "SUBSTANCE"
                if "CAT" in tokens: cat = tokens[tokens.index("CAT")+1]

                # Parse Params: "ox=2.0,en=0.4" -> {"ox": 2.0, "en": 0.4}
                params = {}
                for pair in params_str.split(','):
                    k, v = pair.split('=')
                    params[k.strip()] = float(v)

                # Parse Schema: "ox=0:3:6,en=0:1:6" -> {"ox": {"min": 0, "max": 3, "bits": 6}}
                schema = {}
                for entry in schema_str.split(','):
                    k, val = entry.split('=')
                    mi, ma, bi = val.split(':')
                    schema[k.strip()] = {"min": float(mi), "max": float(ma), "bits": int(bi)}

                vm.state(label, params, schema, cat)

            elif op == "IMPORT":
                alias = None
                if "AS" in tokens: alias = tokens[tokens.index("AS")+1]
                vm.import_atom(tokens[1], alias)

            elif op == "SYNTH":
                # SYNTH <out> FROM <recipe> [U_SCORE <n>]
                out_label = tokens[1]
                recipe_idx = tokens.index("FROM") + 1
                # Find where recipe ends (either end of tokens or before U_SCORE)
                end_idx = tokens.index("U_SCORE") if "U_SCORE" in tokens else len(tokens)
                recipe = " ".join(tokens[recipe_idx:end_idx])
                
                u_score = 1.0
                if "U_SCORE" in tokens:
                    u_score = float(tokens[tokens.index("U_SCORE")+1])
                
                vm.synth(out_label, recipe, u_score=u_score)

            elif op == "SPIRAL":
                # SPIRAL <label> <count> TRANSFORM <name> [PREFIX <p>]
                label = tokens[1]
                count = int(tokens[2])
                trans = tokens[tokens.index("TRANSFORM")+1]
                prefix = tokens[tokens.index("PREFIX")+1] if "PREFIX" in tokens else label
                vm.spiral(label, count, trans, prefix)

            elif op == "REFLEX":
                threshold = float(tokens[1])
                vm.reflex(threshold)

            elif op == "AUDIT":
                label = tokens[1]
                if label in vm.env:
                    a = vm.env[label]
                    print(f"--- AUDIT: {a.label} ---")
                    print(f"  Tax:  {float(a.tax):.4f}")
                    print(f"  NRCI: {float(a.nrci):.4f}")
                    print(f"  DQI:  {a.dqi:.4f}")
                    print(f"  Tilt: {a.tilt:.2f}°")

            elif op == "VISUALIZE":
                save_scene_3d(vm.to_scene_3d())
                print("[Visual] Scene updated.")

        except Exception as e:
            print(f"Error executing '{line}': {e}")

    return {"status": "done"}