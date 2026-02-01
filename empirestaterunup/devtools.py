from pathlib import Path

import pandas

from empirestaterunup.data import load_location_lookup, location_lookup, RaceFields


def enrich_race_results(
        location_lookup_file: Path,
        race_results_file: Path
) -> list[dict]:
    ll = load_location_lookup(data_file=location_lookup_file)
    race_results = pandas.read_json(race_results_file, lines=True, encoding='utf-8').to_dict(orient='records')
    for result in race_results:
        if result[RaceFields.COUNTRY.value] == '':
            locality = result[RaceFields.CITY.value].lower()
            two_letter_code = location_lookup(lookup_data=ll, locality=locality)
            result[RaceFields.COUNTRY.value] = two_letter_code
    return race_results
