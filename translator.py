import json

wf_file = open("schemas/wfcommons-schema.json", "r")

wf_json = json.load(wf_file)

pretty_print = json.dumps(wf_json, indent=4)

print(pretty_print)
