import sys
import json

new_obj = json.loads(sys.argv[1])[0]
print(f'Parameter entered: {new_obj}');
