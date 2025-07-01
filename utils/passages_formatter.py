import json

def format_passages(passages, max_keys=7, maxlen=200, max_passages=4):
    """
    각 passage(dict or str)에서 key 최대 max_keys개, 각 value는 maxlen자로 자른다. 최대 max_passages개까지만.
    """
    import json

    def parse_dict(psg):
        # string이면 json/dict로 파싱 시도, 실패시 그냥 string
        if isinstance(psg, dict):
            return psg
        try:
            return json.loads(psg)
        except Exception:
            return {"text": str(psg)}
    
    out = []
    for idx, psg in enumerate(passages[:max_passages], 1):
        d = parse_dict(psg)
        if not isinstance(d, dict):
            d = {"text": str(d)}
        keys = list(d.keys())[:max_keys]
        kvs = []
        for k in keys:
            val = str(d[k])
            val = val[:maxlen] + (" ..." if len(val) > maxlen else "")
            kvs.append(f"{k}: {val}")
        out.append(f"<{idx}> " + " \n ".join(kvs) + "\n")
    return "".join(out)
