_ITEMS = []
_NEXT_ID = 1

def get_items():
    return _ITEMS

def add_item(item):
    global _NEXT_ID
    record = {"id": _NEXT_ID, **item.dict()}
    _ITEMS.append(record)
    _NEXT_ID += 1
    return record
