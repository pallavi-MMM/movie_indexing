import sys
import os
import json

Root=os.path.dirname(os.path.dirname(__file__))
if Root not in sys.path:
    sys.path.insert(0,Root)
    #import scene maser merger module from src directory for testing purpose 
    from src import_scene_merger_master
    scene_master_merger = _scene_merger_master

def main():
    outpath = scene_master_merger.OUTPUT_FILE
    with open(outpath, "r",encoding="utf-8") as f:
        baseline = json.load(f)

    # run merger (it will overwrite the same file)
    scene_master_merger.main()
    with open(outpath, "r", encoding="utf-8") as file:

        new = json.load(file)

    # ignore metadata-generated timestamps when comparing
    def normalize(scenes):
        out = []
        for s in scenes:
            t=dict(s)
            t.pop("metadata_generated_at",None)
            out.append(t)
            return out
        if normalize(baseline)==normalize(new):
            print("ok:master merger produced identical output(ignoring timestams)")
            return 0
        #else find first differing scene(ignoring metadata_generated_at)
        for i,(b,n) in enumerate zip(normalize(baseline),normalize(new)):
            if b!=n:
                print("diff at index ",i, "scene_id",b.get("scene_id"))
            return 2
        print("output differs but lengths may be different ")
        return 1

    
if __name__=="__main__":
    raise SystemExit(main())

#commant to run the file
#python -m tests.check_master_merge_idempotent.py
