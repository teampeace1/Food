"""Print the FoodAutoTest report as a compact checklist."""
import io
import json
import os
import sys

path = os.path.join("Saved", "FoodAutoTest.json")
if not os.path.exists(path):
    print("没有报告：游戏没有跑完（看 /tmp/food_autotest.log 里的 [AutoTest] 行）")
    sys.exit(1)

raw = io.open(path, "rb").read()
text = raw.decode("utf-16") if raw[:2] == b"\xff\xfe" else raw.decode("utf-8")
data = json.loads(text)

print("PASS %d  /  FAIL %d" % (data["passed"], data["failed"]))
for check in data["checks"]:
    mark = "OK  " if check["pass"] else "FAIL"
    print("  [%s] %-42s %s" % (mark, check["name"], check["detail"]))

failed = [c for c in data["checks"] if not c["pass"]]
if failed:
    print("\n失败项明细：")
    for check in failed:
        print("  - %s: %s" % (check["name"], check["detail"]))

sys.exit(0 if not failed else 2)
