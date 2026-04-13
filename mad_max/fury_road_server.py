"""
Gastown: Fury Road MCP Server
Ucieczka z Cytadeli przez Pustynie do Zielonego Miejsca
"""

import random
import json

# ============== GAME STATE ==============

game_state = {
    "started": False,
    "act": 1,  # 1=Ucieczka, 2=Poscig, 3=Konfrontacja
    "player": None,
    "name": None,
    "location": "komnata",
    "health": 20,
    "max_health": 20,
    "inventory": [],
    "water": 2,
    "food": 2,
    "day": 1,
    "freedom": False,  # Uciekl z komnaty?
    "companions": [],  # Inne zony
    "allies": [],
    "history": [],
}

# ============== LOKACJE ==============

locations = {
    "komnata": {
        "name": "Komnata Żon",
        "description": "Metalowe ściany. Smuga księżyca przez kratę. Pięć łóżek. Cztery puste. Za drzwiami - strażnicy.",
        "exits": ["korytarz"],
        "items": [],
    },
    "korytarz": {
        "name": "Korytarz Cytadeli",
        "description": "Ciemnawy korytarz. Strażnicy przy wejściu. Jedna droga - główne wyjście.",
        "exits": ["komnata", "dziedziniec"],
        "encounter": "strażnik",
    },
    "dziedziniec": {
        "name": "Dziedziniec",
        "description": "Wielki dziedziniec. War Boysi ćwiczą. Brama główna na wschód. Mury wysokie.",
        "exits": ["korytarz", "brama"],
        "encounter": "war_boys",
        "danger": 3,
    },
    "brama": {
        "name": "Brama Główna",
        "description": "Dwie strażniczki. Jedna sprawdza. Druga pilnuje. Można przekupić, walczyć, czekać.",
        "exits": ["dziedziniec", "pustynia"],
        "encounter": "strażniczki",
        "danger": 2,
        "options": ["przekup", "walka", "czekaj"],
    },
    "pustynia": {
        "name": "Pustynia",
        "description": "Piasek. Gorąco. Żadnego cienia. Droga na wschód do Starej Stacji. Szlak na północ.",
        "exits": ["brama", "stara_stacja", "oaza", "pierwszy_postoj"],
        "encounter": "losowe",
        "danger": 1,
        "travel": True,
    },
    "stara_stacja": {
        "name": "Stara Stacja Benzynowa",
        "description": "Zardzewiała stacja. Benzyniarze siedzą. Pięciu. Broń na widoku.Handlują.",
        "exits": ["pustynia"],
        "npc": "benzyniarze",
        "trade": True,
        "danger": 1,
    },
    "oaza": {
        "name": "Oaza Miedzianek",
        "description": "Drzewa! Zielone! Woda! Miedzianki - pokojowe. Dają wodę, jedzenie, mapę. Proszą o pomoc.",
        "exits": ["pustynia"],
        "npc": "miedzianki",
        "trade": True,
        "help": True,
        "danger": 0,
    },
    "pierwszy_postoj": {
        "name": "Pierwszy Postój",
        "description": "Ruiny budynku. Punkt przerzutowy. Czasem ktoś tu czeka. Czasem nikt.",
        "exits": ["pustynia", "row"],
        "encounter": "losowe",
        "danger": 1,
    },
    "row": {
        "name": "Rów - Podziemny Szlak",
        "description": "Ciemne kanały. Stare rury.Węszą Purpuracy. Znają drogę. Pomagają w zamian za pomoc.",
        "exits": ["pierwszy_postoj", "zielone_miejsce"],
        "npc": "purpuraci",
        "danger": 2,
    },
    "zielone_miejsce": {
        "name": "Zielone Miejsca",
        "description": "DRZEWA! TRAWNI! WODA! Bezpiecznie! Koniec podróży... ale coś jest nie tak.",
        "exits": ["row"],
        "danger": 0,
        "ending": True,
    },
}

# ============== FRAKCJE ==============

factions = {
    "warlord": {
        "name": "Warlord",
        "description": "Kontroluje Cytadelę. Ma War Boysów. Chce z powrotem.",
        "enemy": True,
    },
    "war_boys": {
        "name": "War Boysi",
        "description": "Fanatycy. Chcą z powrotem do Cytadeli. Zasieka włóczniami.",
        "enemy": True,
    },
    "benzyniarze": {
        "name": "Benzyniarze",
        "description": "Handlarze paliwem. Chcą handlować. Złoto albo towar.",
        "neutral": True,
    },
    "miedzianki": {
        "name": "Miedzianki",
        "description": "Pokojowe. Pomagają uciekinierom. Dają wodę i jedzenie.",
        "ally": True,
    },
    "purpuraci": {
        "name": "Purpuraci",
        "description": "Podziemni. Przeciw Warlordovi. Znają droge. Pomagają.",
        "ally": True,
    },
}

# ============== PRZEDMIOTY ==============

items = {
    "maczet": {"type": "broń", "damage": "1d8", "price": 5},
    "pistolet": {"type": "broń", "damage": "1d10", "price": 15, "ammo": 6},
    "kilof": {"type": "broń", "damage": "1d8", "price": 3},
    "woda": {"type": "zasób", "price": 3},
    "jedzenie": {"type": "zasób", "price": 2},
    "benzyna": {"type": "zasób", "price": 5},
    "amunicja": {"type": "ammo", "price": 5},
}

# ============== POSTACIE ==============

characters = {
    "ada": {
        "name": "Ada",
        "description": "Bojowniczka. MaBroń i tarczę. Walczy na pierwszej linii.",
        "hp": 25,
        "skills": ["walka", "tarcza"],
    },
    "furia": {
        "name": "Furia",
        "description": "Zwiadowczyni. Zna pustynię. Widzi wszystko.",
        "hp": 20,
        "skills": ["zwiad", "łuki"],
    },
    "srebrna": {
        "name": "Srebrna",
        "description": "Lekarka. Uzdrawia. Chroni innych.",
        "hp": 20,
        "skills": ["leczenie", "perswazja"],
    },
    "rdzawka": {
        "name": "Rdzawka",
        "description": "Mechaniczka. Naprawia pojazdy. Otwiera zamki.",
        "hp": 18,
        "skills": ["mechanika", "skradanie"],
    },
    " huk": {
        "name": "Huk",
        "description": "Siła. Zadaje ciosy. Nikt nie stoi mu na drodze.",
        "hp": 28,
        "skills": ["walka", "siła"],
    },
}

# ============== START ==============


def start_game(player_name: str, character: str = None) -> str:
    """Rozpocznij nową grę - Fury Road"""
    global game_state

    # Wybierz postać lub losuj
    if character and character in characters:
        char = characters[character]
    else:
        char = random.choice(list(characters.values()))

    game_state = {
        "started": True,
        "act": 1,
        "player": char["name"],
        "name": player_name,
        "character": character or "losowa",
        "location": "komnata",
        "health": char["hp"],
        "max_health": char["hp"],
        "skills": char["skills"],
        "inventory": ["maczet"],
        "water": 2,
        "food": 2,
        "day": 1,
        "freedom": False,
        "companions": [],
        "allies": [],
        "history": [{"day": 1, "event": f"{player_name} budzi się w komnacie"}],
    }

    return f"""
🏜️ DUCHAŃSKA ŚCIEŻKA - Twoja historia zaczyna się!

👤 GRAESZ JAKO: {player_name}
📋 TYP: {char["name"]}
❤️ ZDROWE: {char["hp"]}
🎒 UMIEJĘTNOŚCI: {", ".join(char["skills"])}

---

📍 JESTEŚ W: {locations["komnata"]["name"]}

{locations["komnata"]["description"]}

⚠️ ZA DRZWIAMI: Dwóch strażników. Jeden ma klucze.

CO ROBISZ? Możesz:
- Spróbować skradnąć klucze
- Stworzyć rozproszenie
- Przekupić strażnika
- WALKA!
- Szukać innego wyjścia
"""


# ============== RUCH ==============


def move_to(location: str) -> str:
    """Przenieś gracza do lokacji"""
    global game_state

    current = locations[game_state["location"]]

    if location not in current.get("exits", []):
        return f"❌ Nie możesz iść stąd do {location}. Możesz: {', '.join(current['exits'])}"

    game_state["location"] = location
    loc = locations[location]

    # Dodaj do historii
    game_state["history"].append(
        {"day": game_state["day"], "event": f"Poszedł do {loc['name']}"}
    )

    # Sprawdź akt
    if game_state["act"] == 1 and location == "dziedziniec":
        game_state["act"] = 2

    return f"\n📍 {loc['name']}\n\n{loc['description']}\n"


# ============== AKCJE ==============


def attempt_escape() -> str:
    """Próba ucieczki z komnaty"""
    global game_state

    if game_state["location"] != "komnata":
        return "❌ Nie jesteś w komnacie!"

    options = {
        "1": ("Skradnij klucze", 14),
        "2": ("Rozproszenie", 12),
        "3": ("Przekup", 15),
        "4": ("WALKA!", 0),
        "5": ("Szukaj wyjścia", 12),
    }

    # Losuj opcję dla demo
    choice = random.choice(list(options.keys()))
    option, dc = options[choice]

    if choice == "4":  # WALKA
        game_state["freedom"] = True
        game_state["location"] = "korytarz"
        return """
⚔️ WALKA!

Rzucasz. Trafiasz! Pierwszy strażnik pada.
Drugi krzyczy!Alarm!

Masz klucze! Wydostajesz się do korytarza!

📍 JESTEŚ W: Korytarz Cytadeli
⏭️ Teraz musisz przejść przez dziedziniec do bramy!
"""

    roll = random.randint(1, 6) + random.randint(1, 6)

    if roll >= dc:
        game_state["freedom"] = True
        game_state["location"] = "korytarz"
        return f"""
✅ {option} - UDANE!

({roll} vs DC {dc})

Wydostajesz się z komnaty. Biegniesz korytarzem!

📍 JESTEŚ W: Korytarz Cytadeli
"""
    else:
        game_state["health"] -= 5
        return f"""
❌ {option} - NIEUDANE!

({roll} vs DC {dc})

Strażnik cię bije! -5 HP!
Twoje HP: {game_state["health"]}

Spróbuj inaczej lub uciekaj!
"""


def talk_to(npc: str) -> str:
    """Rozmowa z NPC"""
    global game_state

    if npc == "strażnik":
        return """Strażnik:
"Co tu robisz? Won!"
- Możesz: przekup (10), atak, uciekaj"""

    elif npc == "benzyniarz":
        return """Benzyniarz:
"Witaj w Gildii. Co kupujesz?
- Woda: 3, Benzyna: 5, Amunicja: 5"
- Możesz: kup, sprzedaj, targ"""

    elif npc == "miedzianka":
        return """Miedzianka (Ania):
"Witaj, uciekinierko! Potrzebujesz pomocy?"
- Daje: woda, jedzenie, mapa
- Prosi: pomoc w obronie (2 War Boysi ostatnio)
- Możesz: weź pomoc, pomóż, odpocznij"""

    elif npc == "purpurat":
        return """Purpurat (Zasłonięty):
"Idziesz do Zielonego Miejsca? Znam drogę."
- Mówi: "Idź przez Rów. Ale potrzebuję pomocy."
- Możesz: pomóż, idź dalej"""

    return f"Nie ma tu nikogo takiego: {npc}"


def buy_item(item: str, cost: int) -> str:
    """Kup przedmiot"""
    global game_state

    if game_state["money"] < cost:
        return (
            f"❌ Nie stać cię! Masz {game_state.get('money', 0)}, potrzebujesz {cost}"
        )

    if item in items:
        game_state["inventory"].append(item)
        return f"✅ Kupiłeś {item}!"

    return f"❌ Nie mam: {item}"


def search_location() -> str:
    """Przeszukaj lokację"""
    roll = random.randint(1, 6) + random.randint(1, 6)

    if roll < 8:
        return "❌ Nic nie znalazłeś."
    elif roll < 12:
        return "✅ Znalazłeś 10 jednostek!"
    else:
        game_state["inventory"].append("amunicja")
        return "✅ Znalazłeś amunicję!"


def roll_encounter() -> str:
    """Losowe spotkanie na pustyni"""
    encounters = [
        ("war_boys", "🚗 War Boysi! Trzy motocykle! Gonią!", "walka lub ucieczka"),
        ("benzyniarze", "⛽ Benzyniarze. Handlują.", "kup lub ignore"),
        ("pustka", "🏜️ Nic. Pustynia.", "idź dalej"),
        ("szkielet", "💀 Zwłoki. Może coś przy nich?", "szukaj lub idź"),
        ("wędrowiec", "🚶 Wędrowiec. Może zna drogę?", "rozmawiaj"),
        ("burza", "🌪️ Piaskowa burza! Schowaj się!", "DC 15 CON albo -2 HP"),
    ]

    encounter = random.choice(encounters)
    return f"🎲 {encounter[1]}\n({encounter[0]})\nAkcja: {encounter[2]}"


# ============== WALKA ==============


def combat(enemy: str) -> str:
    """Walka z wrogiem"""
    global game_state

    enemies = {
        "strażnik": {"hp": 20, "dmg": 8, "name": "Strażnik"},
        "war_boys": {"hp": 44, "dmg": 6, "name": "War Boysi (4)"},
        "strażniczka": {"hp": 15, "dmg": 6, "name": "Strażniczka"},
    }

    if enemy not in enemies:
        return f"Nie ma tu {enemy}"

    e = enemies[enemy]

    # Gracz atakuje
    roll = random.randint(1, 6) + random.randint(1, 6) + 4
    enemy_def = 10

    if roll >= enemy_def:
        dmg = random.randint(1, 8)
        e["hp"] -= dmg
        result = f"⚔️ TRAFIAŚ! {dmg} obrażeń! {e['name']} HP: {e['hp']}"
    else:
        result = f"❌ Pudło!"

    # Wróg atakuje
    if e["hp"] > 0:
        dmg = e["dmg"]
        game_state["health"] -= dmg
        result += f"\n{e['name']} atakuje! -{dmg} HP! Twoje HP: {game_state['health']}"

    # Sprawdź życie
    if game_state["health"] <= 0:
        return "💀 ZGINĄŁEŚ! Koniec gry."

    if e["hp"] <= 0:
        return f"✅ ZABILEŚ {e['name']}!"

    return result


def flee() -> str:
    """Ucieczka z walki"""
    roll = random.randint(1, 6) + random.randint(1, 6)

    if roll >= 10:
        game_state["location"] = "pustynia"
        return "🏃 Uciekłeś! Jesteś na pustyni!"
    else:
        dmg = random.randint(1, 4)
        game_state["health"] -= dmg
        return f"❌ Nie uciekłeś! {dmg} obrażeń! HP: {game_state['health']}"


# ============== PRZETRWANIE ==============


def next_day() -> str:
    """Następny dzień"""
    global game_state

    game_state["day"] += 1

    # Zużycie
    msg = []
    if game_state["water"] > 0:
        game_state["water"] -= 1
    else:
        game_state["health"] -= 2
        msg.append("❌ Brak wody! -2 HP!")

    if game_state["food"] > 0:
        game_state["food"] -= 1
    else:
        game_state["health"] -= 1
        msg.append("❌ Brak jedzenia! -1 HP!")

    if game_state["health"] <= 0:
        return "💀 ZGINĄŁEŚ z głodu i pragnienia!"

    msg.append(
        f"✅ Dzień {game_state['day']}. HP: {game_state['health']}/{game_state['max_health']}"
    )
    return "\n".join(msg)


def check_survival() -> str:
    """Stan przetrwania"""
    return f"""
❤️ Zdrowie: {game_state["health"]}/{game_state["max_health"]}
💧 Woda: {game_state["water"]} dni
🍖 Jedzenie: {game_state["food"]} dni
🎒 Inwentarz: {", ".join(game_state["inventory"]) if game_state["inventory"] else "pusty"}
📍 Lokacja: {game_state["location"]}
📅 Dzień: {game_state["day"]}
🎭 Akt: {game_state["act"]}
"""


# ============== GAME ==============


def get_state() -> str:
    return json.dumps(game_state, indent=2)


def reset() -> str:
    global game_state
    game_state = {"started": False}
    return "🔄 Zresetowano!"


# ============== TOOLS ==============

TOOLS = [
    {
        "name": "start_game",
        "description": "Rozpocznij nową grę w Fury Road",
        "input_schema": {
            "type": "object",
            "properties": {
                "player_name": {"type": "string", "description": "Imię gracza"},
                "character": {
                    "type": "string",
                    "enum": ["ada", "furia", "srebrna", "rdzawka", "huk"],
                    "description": "Wybierz postać lub zostaw puste",
                },
            },
            "required": ["player_name"],
        },
    },
    {
        "name": "move_to",
        "description": "Idź do innej lokacji",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
    {"name": "attempt_escape", "description": "Próba ucieczki z komnaty"},
    {
        "name": "talk_to",
        "description": "Rozmowa z NPC",
        "input_schema": {
            "type": "object",
            "properties": {"npc": {"type": "string"}},
            "required": ["npc"],
        },
    },
    {
        "name": "buy_item",
        "description": "Kup przedmiot",
        "input_schema": {
            "type": "object",
            "properties": {"item": {"type": "string"}, "cost": {"type": "integer"}},
            "required": ["item", "cost"],
        },
    },
    {"name": "roll_encounter", "description": "Losowe spotkanie na pustyni"},
    {
        "name": "combat",
        "description": "Walcz z wrogiem",
        "input_schema": {
            "type": "object",
            "properties": {"enemy": {"type": "string"}},
            "required": ["enemy"],
        },
    },
    {"name": "flee", "description": "Ucieczka z walki"},
    {"name": "next_day", "description": "Następny dzień - zużywa zasoby"},
    {"name": "check_survival", "description": "Sprawdź stan przetrwania"},
    {"name": "get_state", "description": "Pełny stan gry"},
    {"name": "reset", "description": "Zresetuj grę"},
]


def get_tools():
    return TOOLS


def handle_tool(name, args=None):
    handlers = {
        "start_game": lambda: start_game(args["player_name"], args.get("character")),
        "move_to": lambda: move_to(args["location"]),
        "attempt_escape": attempt_escape,
        "talk_to": lambda: talk_to(args["npc"]),
        "buy_item": lambda: buy_item(args["item"], args["cost"]),
        "roll_encounter": roll_encounter,
        "combat": lambda: combat(args["enemy"]),
        "flee": flee,
        "next_day": next_day,
        "check_survival": check_survival,
        "get_state": get_state,
        "reset": reset,
    }

    if name not in handlers:
        return f"Nieznane: {name}"

    if args:
        return handlers[name]()
    return handlers[name]()
