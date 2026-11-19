import unreal,json
factory=unreal.WidgetBlueprintFactory()
out={}
try:
 bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset('WBP_TrayProbe','/Game/FoodGameplay',unreal.WidgetBlueprint,factory)
 out['bp']=str(bp)
 for prop in ('widget_tree','generated_class','parent_class'):
  try:out[prop]=str(bp.get_editor_property(prop))
  except Exception as e:out[prop]=repr(e)
except Exception as e:out['err']=repr(e)
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_widget_create_probe.json','w') as f:json.dump(out,f,indent=2)
