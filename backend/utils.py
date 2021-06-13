def dictify(obj):
    if isinstance(obj, dict):
        ret = {}
        for k in obj:
            ret[k] = dictify(obj[k])
    elif isinstance(obj, list):
        ret = []
        for item in obj:
            ret.append(dictify(item))
    elif "to_dict" in list(obj.__dir__()):
        ret = obj.to_dict()
    elif obj.__class__.__name__ == "Player":
        ret = obj.uid
    elif obj.__class__.__name__ == "Team":
        ret = str(obj)
    else:
        ret = obj

    return ret


