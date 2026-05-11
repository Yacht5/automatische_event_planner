import json

# Prijzen per persoon (None = op aanvraag, wordt niet in totaal meegenomen)
CATERING_PRICES = {
    'Sandwich & Soup':         14.95,
    'Lunch 2-gangen':          37.50,
    'Lunch 3-gangen':          45.50,
    'Borrelbites':              5.50,
    'Fingerfoods':             10.95,
    'Walking Dinner 4-gangen': 39.50,
    'Walking Dinner 5-gangen': 47.00,
    'Barbecue':                29.50,
    'Easy Streetfood':         None,
    'Welkomst bubbels':         6.95,
    'Drankarrangement 2u':     27.25,
    'Drankarrangement 3u':     32.25,
    'Drankarrangement 4u':     37.25,
    'Drankarrangement 5u':     42.25,
    'Drankarrangement 6u':     47.25,
    'Bierproeverij':           None,
    'Cocktailworkshop':        None,
    'Spreker':                 None,
    'Live muziek':             None,
    'DJ':                      None,
    'Unieke acts':             None,
}


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

    for item in catering_items:
        price_pp = CATERING_PRICES.get(item)
        if price_pp is None:
            on_request_items.append(item)
        else:
            cost = price_pp * guest_count
            total_catering += cost
            itemized_catering.append({
                "name":       item,
                "quantity":   guest_count,
                "unit_price": price_pp,
                "total":      cost,
            })

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
        "itemized": [
            {
                "name":       f"Zaalhuur: {location}",
                "quantity":   1,
                "unit_price": location_cost,
                "total":      location_cost,
            }
        ] + itemized_catering,
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
