# EmpireStateBuildingRunUp Changelog

Most important changes on this project, by version.

## Jan Mon 20 2025 <kodegeek.com@protonmail.com> - 0.2.0
- Switched country codes from CSV to [TOML](https://toml.io/en/) to make it easier to maintain. Changes on code to support new format.
- Removed all wave details. Data is not part of the official race results and logic is known only to the race 
  organizers, too much work for guesswork.
- Use new _JSON_ format for race results as opposed to _CSV_. 
  - Race [results](https://www.athlinks.com/event/382111?category=global&term=EmpireState)
  - Results scrapped with [athlinks-races](https://pypi.org/project/athlinks-races/)
    - [2023](https://www.athlinks.com/event/382111/results/Event/1062909/Results)
    - [2024](https://www.athlinks.com/event/382111/results/Event/1093108/Results)
- Improved search palette
- Speed and memory optimizations
- Second time running this race, 2024 results!

## Jan Sun 12 2025 <kodegeek.com@protonmail.com> - 0.1.1
- Removed creation of 3 deprecated applications: _esru_scraper, esru_csv_cleaner, esru_raw_cleaner_
- Removed all scrapping code, instead follow [athlinks-races](https://github.com/josevnz/athlinks-races)

## Mar Fri 28 2024 Jose Vicente Nunez <kodegeek.com@protonmail.com> - 0.6
- Using new version of libraries (bug-fixes and modest speed improvements)
- TUI improvements on search and notifications
- FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
- BadIdentifier: 'Count By Age' is an invalid id
- Cleaner display of dates

## Dec Fri 01 2023 Jose Vicente Nunez <kodegeek.com@protonmail.com> < 0.5
- Initial tutorial version
- First time ever running a Tower race, 2023 results!