import json

# Prijzen per persoon (None = op aanvraag, wordt niet in totaal meegenomen)
CATERING_PRICES = {
    'Sandwich & Soup':              14.95,
    'Lunch 2-gangen':               37.50,
    'Lunch 3-gangen':               45.50,
    'Borrelbites':                   5.50,
    'Fingerfoods':                  10.95,
    'Walking Dinner 4-gangen':      39.50,
    'Walking Dinner 5-gangen':      47.00,
    'Barbecue':                     29.50,
    'Vlees/vis barbecue':                 32.50,
    'Buffet':                       35.55,
    'Borrelplank':                   6.95,
    'Welkomst bubbels':              6.95,
    'Koffie & thee met vlaai':       None,
    'Koffie & thee met zoetigheden': None,
    'Grand dessert':                 None,
    'Drankarrangement 2u':          27.25,
    'Drankarrangement 3u':          32.25,
    'Drankarrangement 4u':          37.25,
    'Drankarrangement 5u':          42.25,
    'Drankarrangement 6u':          47.25,
    'Drankarrangement 7u':          52.50,
    'Drankarrangement 8u':          57.75,
    'Na calculatie van dranken':    None,
    'Bierproeverij':                None,
    'Cocktailworkshop':             None,
    'Spreker':                      None,
    'Live muziek':                  None,
    'DJ':                           None,
    'Unieke acts':                  None,
}

# Vaste volgorde op de offerte
ITEM_ORDER = [
    # 1. Drank
    'Welkomst bubbels',
    'Drankarrangement 2u',
    'Drankarrangement 3u',
    'Drankarrangement 4u',
    'Drankarrangement 5u',
    'Drankarrangement 6u',
    'Na calculatie van dranken',
    # 2. Eten
    'Sandwich & Soup',
    'Lunch 2-gangen',
    'Lunch 3-gangen',
    'Walking Dinner 4-gangen',
    'Walking Dinner 5-gangen',
    'Barbecue',
    'Vlees/vis barbecue',
    'Fingerfoods',
    'Borrelbites',
    'Koffie & thee met vlaai',
    'Koffie & thee met zoetigheden',
    'Grand dessert',
    # 3. Acts (op aanvraag)
    'Bierproeverij',
    'Cocktailworkshop',
    'Spreker',
    'Live muziek',
    'DJ',
    'Unieke acts',
]


def get_location_cost(location: str, guests: int) -> float:
    location_lower = location.lower()
    if 'boven' in location_lower:
        return 800.0 if guests <= 70 else 1000.0
    if 'beneden' in location_lower or 'onder' in location_lower:
        return 2500.0
    if 'pand' in location_lower or 'geheel' in location_lower:
        return 3000.0
    return 800.0 if guests <= 70 else 1000.0


def calculate_quote(event_data: dict) -> dict:
    event_type  = event_data.get("category", "Particulier")
    guest_count = int(event_data.get("guests", 1))
    location    = event_data.get("location", "")

    location_cost     = get_location_cost(location, guest_count)
    catering_items    = event_data.get("catering", [])
    total_catering    = 0.0
    itemized_catering = []
    on_request_items  = []

    # Items die geen prijs hebben maar wél in de vaste volgorde moeten blijven
    INLINE_ON_REQUEST = {'Na calculatie van dranken'}

    catering_lookup = {}
    for item in catering_items:
        price_pp = CATERING_PRICES.get(item)
        if price_pp is None and item not in INLINE_ON_REQUEST:
            catering_lookup[item] = None
        elif price_pp is None:
            catering_lookup[item] = {
                "name":       item,
                "quantity":   1,
                "unit_price": 0.0,
                "total":      0.0,
                "on_request": True,
            }
        else:
            cost = price_pp * guest_count
            total_catering += cost
            catering_lookup[item] = {
                "name":       item,
                "quantity":   guest_count,
                "unit_price": price_pp,
                "total":      cost,
            }

    # Sorteer op vaste volgorde; onbekende items achteraan
    def sort_key(item):
        try:
            return ITEM_ORDER.index(item)
        except ValueError:
            return len(ITEM_ORDER)

    for item in sorted(catering_items, key=sort_key):
        entry = catering_lookup[item]
        if entry is None:
            on_request_items.append(item)
        else:
            itemized_catering.append(entry)

    zaalhuur = {
        "name":       f"Zaalhuur: {location}",
        "quantity":   1,
        "unit_price": location_cost,
        "total":      location_cost,
    }

    # Volgorde: drank → eten → zaalhuur → acts (op aanvraag apart)
    DRINK_ITEMS = {'Welkomst bubbels', 'Drankarrangement 2u', 'Drankarrangement 3u',
                   'Drankarrangement 4u', 'Drankarrangement 5u', 'Drankarrangement 6u',
                   'Drankarrangement 7u', 'Drankarrangement 8u', 'Na calculatie van dranken'}
    ACT_ITEMS   = {'Bierproeverij', 'Cocktailworkshop', 'Spreker', 'Live muziek', 'DJ', 'Unieke acts'}

    drink_lines = [e for e in itemized_catering if e["name"] in DRINK_ITEMS]
    food_lines  = [e for e in itemized_catering if e["name"] not in DRINK_ITEMS and e["name"] not in ACT_ITEMS]
    act_lines   = [e for e in itemized_catering if e["name"] in ACT_ITEMS]

    itemized = drink_lines + food_lines + [zaalhuur] + act_lines

    subtotal   = location_cost + total_catering
    vat_amount = subtotal * 0.21
    total      = subtotal + vat_amount

    return {
        "event_summary": {
            "type":     event_type,
            "guests":   guest_count,
            "location": location,
            "date":     event_data.get("date", "N.v.t."),
        },
        "itemized":   itemized,
        "on_request": on_request_items,
        "totals": {
            "subtotal":   subtotal,
            "vat_rate":   "21%",
            "vat_amount": vat_amount,
            "total":      total,
        },
    }


if __name__ == "__main__":
    test_data = {
        "category": "Zakelijk",
        "guests":   40,
        "date":     "2026-07-15",
        "location": "Boven binnen",
        "catering": ["Barbecue", "Welkomst bubbels", "Drankarrangement 3u", "DJ"],
    }
    print(json.dumps(calculate_quote(test_data), indent=2))
