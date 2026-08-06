# Site Intelligence v3.23.7.2 Validation Repair

The original v3.23.7.2 installer stopped before promotion because its headless-Chrome gate assumed that pressing Home and End on a closed native `<select>` would change the selected value on every operating system.

The failed result itself showed that the application contract was working: the country catalog loaded, focus remained on `countrySelect`, Brazil was selected, and the Data Truth badge changed to `BRA`. The nonportable assertion was the only failure.

The repaired gate now verifies the cross-platform contract:

- at least 170 unique country choices are present;
- Kenya and Brazil are both present;
- the selector is enabled, visible, and accepts pointer interaction;
- wheel events are not cancelled by the application;
- background workspace updates do not steal focus;
- the first, last, and Brazil options can each be selected;
- Data Truth follows every selection;
- the same checks pass directly and inside the WordPress iframe.

The internal release remains v3.23.7.2 because the failed installer never reached GitHub, Render, or the WordPress handoff.
