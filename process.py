#!/usr/bin/env python3

import json

from datetime import datetime, date
from pathlib import Path
from typing import Any

import requests

from git import Repo


def get_data_stop(stop_id: str) -> dict[str, Any]:
    r = requests.get('https://data.bordeaux-metropole.fr/geojson/process/saeiv_arret_passages',
                     params={'key': '258BILMNYZ', 'datainputs': json.dumps({'ARRET_ID': stop_id})})
    r.raise_for_status()
    data = r.json()
    to_return = {}
    for entry in data['features']:
        if tram_id := entry['properties']['rs_sv_vehic_p']:
            theo_time = entry['properties']['hor_theo']
            expected_time = entry['properties']['hor_estime']
            name = entry['properties']['libelle']
        else:
            # not initialized
            continue
        dt_theo = datetime.fromisoformat(theo_time)
        dt_expected = datetime.fromisoformat(expected_time)
        # NOTE: not sure the tram id is unique per day or not, assuming it's not
        to_return[theo_time] = {'tram_id': tram_id, 'name': name, 'real_time': expected_time, 'diff': (dt_expected - dt_theo).total_seconds()}
    return to_return


def run(stop_id):
    today = date.today().isoformat()
    dump_dir = Path('data') / today
    dump_dir.mkdir(parents=True, exist_ok=True)
    dump_file = dump_dir / stop_id
    if dump_file.exists():
        with dump_file.open() as f:
            old_data = json.load(f)
    else:
        old_data = {}
    cur_data = get_data_stop(stop_id)

    to_dump = old_data | cur_data
    with dump_file.open('w') as f:
        json.dump(to_dump, f)


def update_repo() -> None:
    repo = Repo('./')
    to_add = ['data']
    repo.index.add(to_add)
    repo.index.commit(f"Add data up to {datetime.now()}")
    origin = repo.remote(name='origin')
    origin.push()


if __name__ == "__main__":
    to_capture = [
        "T_FLEURI_A",  # bois fleuri -> Downtown
        "T_FLEURI_R",  # bois fleuri -> EOL
        "T_BUTINI_A",  # Buttiniere -> Downtown
        "T_BUTINI_R",  # Buttiniere -> EOLs
        "T_BOU_A_A",  # Bourgogne from rive droite
        "T_BOU_A_R",  # Bourgogne -> rive droite
        "T_BOU_C_A",  # Bourgogne -> Hotel Ville (from train station)
        "T_BOU_C_R",  # Bourgogne -> train station
        "T_QUINCB_A",  # Quinconce -> NW
        "T_QUINCB_R",  # Quinconce -> SE
        "T_QUINCC_A",  # Quinconce -> NE
        "T_QUINCC_R",  # Quinconce -> SW
    ]
    for stop_id in to_capture:
        run(stop_id)
    update_repo()
