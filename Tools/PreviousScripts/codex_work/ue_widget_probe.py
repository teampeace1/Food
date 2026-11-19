import unreal,json
out={}
for name in ('WidgetBlueprintFactory','WidgetBlueprint','WidgetTree','TextBlock','Border','HorizontalBox','CanvasPanel','WidgetBlueprintLibrary','EditorUtilityWidgetBlueprint'):
    c=getattr(unreal,name,None);out[name]=str(c)
    if c:out[name+'_methods']=[x for x in dir(c) if any(k in x.lower() for k in ('widget','root','create','bind'))][:80]
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_widget_probe.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
