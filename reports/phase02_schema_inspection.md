# Phase 02 — Excel schema inspection

**Scope:** complete BNetzA September 2026 + all 3 KBA FZ 27 releases in 2026.

This report shows ONLY early Excel rows to identify title/header/subheader positions.
The full source workbooks are untouched and no records are discarded.

Do not interpret these preview row counts as equipment/point/vehicle totals.

## Source inventory

| Source | Sheets inspected | Status |
|---|---:|---|
| bnetza_charging_2026_09_30 | 1 | ok |
| kba_fz27_2026_01 | 20 | ok |
| kba_fz27_2026_04 | 20 | ok |
| kba_fz27_2026_07 | 20 | ok |

## bnetza_charging_2026_09_30

### Ladesäulenregister

```text
A1 = Ladesäulenregister Bundesnetzagentur
A3 = Hinweis:
A4 = Die Liste beinhaltet die Ladeeinrichtungen aller Betreiberinnen und Betreiber, die das Anzeigeverfahren der Bundesnetzagentur
A5 = zum Zeitpunkt der Aktualisierung vollständig abgeschlossen haben.
A6 = Die Zahl der öffentlich zugänglichen Ladeeinrichtungen in Deutschland ist daher größer als hier dargestellt.
A8 = Letzte Aktualisierung vom: 30.09.2026
A10 = Allgemeine Informationen | X10 = 1. Ladepunkt | AB10 = 2. Ladepunkt | AF10 = 3. Ladepunkt | AJ10 = 4. Ladepunkt | AN10 = 5. Ladepunkt | AR10 = 6. Ladepunkt
A11 = Ladeeinrichtungs-ID | B11 = Betreiber | C11 = Anzeigename (Karte) | D11 = Status | E11 = Art der Ladeeinrichtung | F11 = Anzahl Ladepunkte | G11 = Nennleistung Ladeeinrichtung [kW] | H11 = Inbetriebnahmedatum | I11 = Straße | J11 = Hausnummer | K11 = Adresszusatz | L11 = Postleitzahl | M11 = Ort | N11 = Kreis/kreisfreie Stadt | O11 = Bundesland | P11 = Breitengrad | Q11 = Längengrad | R11 = Standortbezeichnung | S11 = Informationen zum Parkraum | T11 = Bezahlsysteme | U11 = Öffnungszeiten | V11 = Öffnungszeiten: Wochentage | W11 = Öffnungszeiten: Tageszeiten | X11 = Steckertypen1 | Y11 = Nennleistung Stecker1 | Z11 = EVSE-ID1 | AA11 = Public Key1 | AB11 = Steckertypen2 | AC11 = Nennleistung Stecker2 | AD11 = EVSE-ID2 | AE11 = Public Key2 | AF11 = Steckertypen3 | AG11 = Nennleistung Stecker3 | AH11 = EVSE-ID3 | AI11 = Public Key3 | AJ11 = Steckertypen4 | AK11 = Nennleistung Stecker4 | AL11 = EVSE-ID4 | AM11 = Public Key4 | AN11 = Steckertypen5 | AO11 = Nennleistung Stecker5 | AP11 = EVSE-ID5 | AQ11 = Public Key5 | AR11 = Steckertypen6 | AS11 = Nennleistung Stecker6 | AT11 = EVSE-ID6 | AU11 = Public Key6
A12 = 1010338 | B12 = Albwerk Elektro- und Kommunikationstechnik GmbH | C12 = Albwerk Elektro- und Kommunikationstechnik GmbH | D12 = In Betrieb | E12 = Normalladeeinrichtung | F12 = 2 | G12 = 22 | H12 = 43841 | I12 = Am Berg | J12 = 1 | L12 = 72535 | M12 = Heroldstatt | N12 = Landkreis Alb-Donau-Kreis | O12 = Baden-Württemberg | P12 = 48.442397999999997 | Q12 = 9.6590749999999996 | S12 = Keine Beschränkung | T12 = RFID-Karte;Onlinezahlungsverfahren | U12 = 247 | V12 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W12 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X12 = AC Typ 2 Steckdose | Y12 = 22 | Z12 = DEAEWE002501 | AA12 = CA49E2E0941DA7B788E787D6E500C316D6A2084FEB651A270FFC64F51F5A73EC70CAEEEF55A6FA3EA91B766B8A7D32C2 | AB12 = AC Typ 2 Steckdose | AC12 = 22 | AD12 = DEAEWE002502 | AE12 = AC676D2E2A2F799F0E7D0F5207A146E4199501D54C3C12C61F4DCEA8056276434702184508C6649F97302F924E631F34
A13 = 1160637 | B13 = Albwerk Elektro- und Kommunikationstechnik GmbH | C13 = Albwerk Elektro- und Kommunikationstechnik GmbH | D13 = In Betrieb | E13 = Normalladeeinrichtung | F13 = 1 | G13 = 22 | H13 = 46212 | I13 = Lange Str. | J13 = 53 | L13 = 72535 | M13 = Heroldstatt | N13 = Landkreis Alb-Donau-Kreis | O13 = Baden-Württemberg | P13 = 48.446066999999999 | Q13 = 9.6684079999999994 | S13 = Keine Beschränkung | T13 = Onlinezahlungsverfahren;RFID-Karte | U13 = 247 | V13 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W13 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X13 = AC Typ 2 Steckdose | Y13 = 22 | Z13 = DEAEWE011101 | AA13 = 3059 3013 0607 2A86 48CE 3D02 0106 082A 8648 CE3D 0301 0703 4200 047C 484E FB19 60CC 2934 712F 64A9 DC7E 0901 1A86 335E 85CB 7C7C 509A 21A6 6E39 DF35 EC76 15F5
A14 = 1160638 | B14 = Albwerk Elektro- und Kommunikationstechnik GmbH | C14 = Albwerk Elektro- und Kommunikationstechnik GmbH | D14 = In Betrieb | E14 = Normalladeeinrichtung | F14 = 1 | G14 = 22 | H14 = 46212 | I14 = Lange Str. | J14 = 53 | L14 = 72535 | M14 = Heroldstatt | N14 = Landkreis Alb-Donau-Kreis | O14 = Baden-Württemberg | P14 = 48.446066999999999 | Q14 = 9.6684079999999994 | S14 = Keine Beschränkung | T14 = Onlinezahlungsverfahren;RFID-Karte | U14 = 247 | V14 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W14 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X14 = AC Typ 2 Steckdose | Y14 = 22 | Z14 = DEAEWE011102 | AA14 = 3059 3013 0607 2A86 48CE 3D02 0106 082A 8648 CE3D 0301 0703 4200 043E 14E3 02E0 DE25 B5BA 01C5 96F6 0B72 F52E 8291 CE08 3401 7FE3 BFA8 62BA 6FC1 052B 111C CEED
A15 = 1160639 | B15 = Albwerk Elektro- und Kommunikationstechnik GmbH | C15 = Albwerk Elektro- und Kommunikationstechnik GmbH | D15 = In Betrieb | E15 = Normalladeeinrichtung | F15 = 1 | G15 = 22 | H15 = 46212 | I15 = Lange Str. | J15 = 53 | L15 = 72535 | M15 = Heroldstatt | N15 = Landkreis Alb-Donau-Kreis | O15 = Baden-Württemberg | P15 = 48.446066999999999 | Q15 = 9.6684079999999994 | S15 = Keine Beschränkung | T15 = Onlinezahlungsverfahren;RFID-Karte | U15 = 247 | V15 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W15 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X15 = AC Typ 2 Steckdose | Y15 = 22 | Z15 = DEAEWE011103 | AA15 = 3059 3013 0607 2A86 48CE 3D02 0106 082A 8648 CE3D 0301 0703 4200 04FA 39BC B001 0E19 D305 FA37 A16F 7F05 1B63 D45C 7B9F B548 DBA9 528A 9E7D 3B25 9377 5788 561F
A16 = 1063962 | B16 = smopi® - Multi Chargepoint Solution GmbH | C16 = smopi | D16 = In Betrieb | E16 = Normalladeeinrichtung | F16 = 4 | G16 = 22 | H16 = 44888 | I16 = Albstraße | J16 = 15 | L16 = 72535 | M16 = Heroldstatt | N16 = Landkreis Alb-Donau-Kreis | O16 = Baden-Württemberg | P16 = 48.449424 | Q16 = 9.6722009999999994 | T16 = Onlinezahlungsverfahren;RFID-Karte | U16 = Keine Angabe | X16 = AC Typ 2 Steckdose | Y16 = 22 | AB16 = AC Typ 2 Steckdose | AC16 = 22 | AF16 = AC Typ 2 Steckdose | AG16 = 22 | AJ16 = AC Typ 2 Steckdose | AK16 = 22
A17 = 1063963 | B17 = smopi® - Multi Chargepoint Solution GmbH | C17 = smopi | D17 = In Betrieb | E17 = Normalladeeinrichtung | F17 = 4 | G17 = 22 | H17 = 44888 | I17 = Albstraße | J17 = 15 | L17 = 72535 | M17 = Heroldstatt | N17 = Landkreis Alb-Donau-Kreis | O17 = Baden-Württemberg | P17 = 48.449424 | Q17 = 9.6722009999999994 | T17 = Onlinezahlungsverfahren;RFID-Karte | U17 = Keine Angabe | X17 = AC Typ 2 Steckdose | Y17 = 22 | AB17 = AC Typ 2 Steckdose | AC17 = 22 | AF17 = AC Typ 2 Steckdose | AG17 = 22 | AJ17 = AC Typ 2 Steckdose | AK17 = 22
A18 = 1063964 | B18 = smopi® - Multi Chargepoint Solution GmbH | C18 = smopi | D18 = In Betrieb | E18 = Normalladeeinrichtung | F18 = 2 | G18 = 22 | H18 = 44888 | I18 = Albstraße | J18 = 15 | L18 = 72535 | M18 = Heroldstatt | N18 = Landkreis Alb-Donau-Kreis | O18 = Baden-Württemberg | P18 = 48.449424 | Q18 = 9.6722009999999994 | T18 = Onlinezahlungsverfahren;RFID-Karte | U18 = Keine Angabe | X18 = AC Typ 2 Steckdose | Y18 = 22 | AB18 = AC Typ 2 Steckdose | AC18 = 22
A19 = 1010329 | B19 = Albwerk Elektro- und Kommunikationstechnik GmbH | C19 = Albwerk Elektro- und Kommunikationstechnik GmbH | D19 = In Betrieb | E19 = Normalladeeinrichtung | F19 = 2 | G19 = 22 | H19 = 43472 | I19 = Beim Campingplatz | J19 = 1 | L19 = 72589 | M19 = Westerheim | N19 = Landkreis Alb-Donau-Kreis | O19 = Baden-Württemberg | P19 = 48.5105 | Q19 = 9.609 | S19 = Keine Beschränkung | T19 = RFID-Karte;Onlinezahlungsverfahren | U19 = 247 | V19 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W19 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X19 = AC Typ 2 Steckdose | Y19 = 22 | Z19 = DEAEWE001501 | AA19 = 54A7C55ED7A52040168B4D58AA08B5BA5EBA9DFEA71343BA3E07AE305279D20D8F3A1D7C6E067B3C3D708091B72B66C1 | AB19 = AC Typ 2 Steckdose | AC19 = 22 | AD19 = DEAEWE001502 | AE19 = 5B5F67506F7286C21830088EDDB3AB797FC9BFE4ED8BCAB0DC0F249300BD6A43CCC73BF77B4670205E0D4175DBFD2ED2
A20 = 1158224 | B20 = EnBW mobility+ AG und Co.KG  | D20 = In Betrieb | E20 = Schnellladeeinrichtung | F20 = 2 | G20 = 100 | H20 = 46182 | I20 = Hauptstraße | J20 = 91 | L20 = 73340 | M20 = Amstetten | N20 = Landkreis Alb-Donau-Kreis | O20 = Baden-Württemberg | P20 = 48.578533 | Q20 = 9.8748400000000007 | R20 = 73340 Amstetten, Hauptstraße 91c | S20 = Keine Beschränkung | T20 = Onlinezahlungsverfahren;RFID-Karte;Debitkarte (Lesegerät);Debitkarte (NFC);Kreditkarte (Lesegerät);Kreditkarte (NFC);Sonstige | U20 = 247 | V20 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W20 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X20 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | Y20 = 100 | Z20 = DE*EBW*E912316*1 | AA20 = 3056301006072A8648CE3D020106052B8104000A03420004F9488513F8C94A9B8CB07F1F2486D2C367AA76B9F494A10BCA2A07D364F33F9E6705B74A523A78C7E4CDD418FAEE909E27E6EE766CEB7D4D | AB20 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | AC20 = 100 | AD20 = DE*EBW*E912316*2 | AE20 = 3056301006072A8648CE3D020106052B8104000A03420004EE031A32371602C9EEF50A5BB7CD1BFF6291F6DA2434F9F63856BBBF5DD0AB36260C0C73738E8AEA4578756EE0F1EC64E3353E9A4187DB57
A21 = 1120617 | B21 = Gasthaus & Albhotel zum Bahnhöfle | D21 = In Betrieb | E21 = Normalladeeinrichtung | F21 = 2 | G21 = 22 | H21 = 45723 | I21 = Bräunisheimer Str. | J21 = 22 | K21 = Parkplatz Albhotel | L21 = 73340 | M21 = Amstetten | N21 = Landkreis Alb-Donau-Kreis | O21 = Baden-Württemberg | P21 = 48.595016000000001 | Q21 = 9.9218539999999997 | R21 = Albhotel Bahnhöfle | S21 = Keine Beschränkung | T21 = Kreditkarte (NFC);Debitkarte (NFC);Onlinezahlungsverfahren;RFID-Karte | U21 = 247 | V21 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W21 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X21 = AC Typ 2 Steckdose | Y21 = 22 | Z21 = DE CSA 24D 006 | AA21 = G92147*1 | AB21 = AC Typ 2 Steckdose | AC21 = 22 | AE21 = G92147*2
A22 = 1121121 | B22 = Gasthaus & Albhotel zum Bahnhöfle | D22 = In Betrieb | E22 = Normalladeeinrichtung | F22 = 2 | G22 = 22 | H22 = 45723 | I22 = Bräunisheimer Str. | J22 = 22 | K22 = Parkplatz Albhotel Bahnhoefle | L22 = 73340 | M22 = Amstetten | N22 = Landkreis Alb-Donau-Kreis | O22 = Baden-Württemberg | P22 = 48.595016000000001 | Q22 = 9.9218539999999997 | R22 = Albhotel Bahnhöfle | S22 = Keine Beschränkung | T22 = Kreditkarte (NFC);Debitkarte (NFC) | U22 = 247 | V22 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W22 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X22 = AC Typ 2 Steckdose | Y22 = 22 | AA22 = G92146*1 | AB22 = AC Typ 2 Steckdose | AC22 = 22 | AE22 = G92146*2
A23 = 1033071 | B23 = SWU Energie GmbH | D23 = In Betrieb | E23 = Normalladeeinrichtung | F23 = 2 | G23 = 44 | H23 = 44682 | I23 = Sterngasse | J23 = 6 | L23 = 88481 | M23 = Balzheim | N23 = Landkreis Alb-Donau-Kreis | O23 = Baden-Württemberg | P23 = 48.179958999999997 | Q23 = 10.076976999999999 | S23 = Keine Beschränkung | T23 = Onlinezahlungsverfahren;RFID-Karte | U23 = 247 | V23 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W23 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X23 = AC Typ 2 Steckdose | Y23 = 22 | AA23 = 303D9D089B1B71BDB4022397D16C4256340D87C39CC1B29DBC796D1F0A558C37D4C5AA53B26878B8D9DE33B33AD422A4 | AB23 = AC Typ 2 Steckdose | AC23 = 22 | AE23 = 44F05AA564C6660A3F00B44249E08A34E16E6ACC5092AD63438E887AA07AB540501AD4678ED25DE43106C1B3CF9ECE5D
A24 = 1033011 | B24 = SWU Energie GmbH | D24 = In Betrieb | E24 = Normalladeeinrichtung | F24 = 1 | G24 = 22 | H24 = 44105 | I24 = Herwigstraße | J24 = 21 | L24 = 89129 | M24 = Langenau | N24 = Landkreis Alb-Donau-Kreis | O24 = Baden-Württemberg | P24 = 48.485239999999997 | Q24 = 10.028290999999999 | U24 = Keine Angabe | X24 = AC Typ 2 Steckdose | Y24 = 22
A25 = 1033009 | B25 = SWU Energie GmbH | D25 = In Betrieb | E25 = Normalladeeinrichtung | F25 = 1 | G25 = 22 | H25 = 44105 | I25 = Osterstetter Straße | J25 = 14 | L25 = 89129 | M25 = Langenau | N25 = Landkreis Alb-Donau-Kreis | O25 = Baden-Württemberg | P25 = 48.484729999999999 | Q25 = 10.061164 | U25 = Keine Angabe | X25 = AC Typ 2 Steckdose | Y25 = 22
A26 = 1085137 | B26 = Christian  Dillschneider | D26 = In Betrieb | E26 = Normalladeeinrichtung | F26 = 1 | G26 = 11 | H26 = 44825 | I26 = Hasenbergle  | J26 = 22 | L26 = 89129 | M26 = Langenau | N26 = Landkreis Alb-Donau-Kreis | O26 = Baden-Württemberg | P26 = 48.486795000000001 | Q26 = 10.063402999999999 | T26 = Kostenlos | U26 = Keine Angabe | X26 = AC Typ 2 Steckdose | Y26 = 11
A27 = 1057183 | B27 = LAN1 Hotspots GmbH | C27 = LAN1 Hotspots GmbH | D27 = In Betrieb | E27 = Normalladeeinrichtung | F27 = 3 | G27 = 33 | H27 = 45182 | I27 = Magirusstraße | J27 = 16 | L27 = 89129 | M27 = Langenau | N27 = Landkreis Alb-Donau-Kreis | O27 = Baden-Württemberg | P27 = 48.500942999999999 | Q27 = 10.082036 | T27 = Onlinezahlungsverfahren;RFID-Karte | U27 = Keine Angabe | X27 = AC Typ 2 Steckdose | Y27 = 11 | AB27 = AC Typ 2 Steckdose | AC27 = 11 | AF27 = AC Typ 2 Steckdose | AG27 = 11
A28 = 1135370 | B28 = Thomas Decker | D28 = In Betrieb | E28 = Normalladeeinrichtung | F28 = 1 | G28 = 11 | H28 = 45268 | I28 = Auf der Höhe | J28 = 11 | L28 = 89129 | M28 = Langenau | N28 = Landkreis Alb-Donau-Kreis | O28 = Baden-Württemberg | P28 = 48.476367000000003 | Q28 = 10.085020999999999 | S28 = Keine Beschränkung | T28 = Kostenlos | U28 = Keine Angabe | X28 = AC Typ 2 Steckdose | Y28 = 11
A29 = 1033010 | B29 = SWU Energie GmbH | D29 = In Betrieb | E29 = Normalladeeinrichtung | F29 = 1 | G29 = 22 | H29 = 44105 | I29 = Hallenweg | J29 = 32 | L29 = 89129 | M29 = Langenau | N29 = Landkreis Alb-Donau-Kreis | O29 = Baden-Württemberg | P29 = 48.474798 | Q29 = 10.085578999999999 | U29 = Keine Angabe | X29 = AC Typ 2 Steckdose | Y29 = 22
A30 = 1009242 | B30 = Shell Deutschland GmbH | D30 = In Betrieb | E30 = Schnellladeeinrichtung | F30 = 2 | G30 = 300 | H30 = 45132 | I30 = Kiesgräble | J30 = 2 | L30 = 89129 | M30 = Langenau | N30 = Landkreis Alb-Donau-Kreis | O30 = Baden-Württemberg | P30 = 48.493389999999998 | Q30 = 10.10783 | T30 = Kreditkarte (NFC);Debitkarte (NFC);Onlinezahlungsverfahren;RFID-Karte | U30 = Keine Angabe | X30 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | Y30 = 150 | AB30 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | AC30 = 150
A31 = 1096831 | B31 = autohaus Langenau GmbH | D31 = In Betrieb | E31 = Normalladeeinrichtung | F31 = 2 | G31 = 33 | H31 = 44251 | I31 = Kiesgräble | J31 = 1 | L31 = 89129 | M31 = Langenau | N31 = Landkreis Alb-Donau-Kreis | O31 = Baden-Württemberg | P31 = 48.493378 | Q31 = 10.108722999999999 | T31 = Onlinezahlungsverfahren;RFID-Karte;Sonstige | U31 = Keine Angabe | X31 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | Y31 = 22 | AB31 = AC Typ 2 Steckdose | AC31 = 11
A32 = 1033007 | B32 = SWU Energie GmbH | D32 = In Betrieb | E32 = Normalladeeinrichtung | F32 = 1 | G32 = 22 | H32 = 44105 | I32 = Beethovenstraße | J32 = 40 | L32 = 89129 | M32 = Langenau | N32 = Landkreis Alb-Donau-Kreis | O32 = Baden-Württemberg | P32 = 48.493191000000003 | Q32 = 10.113215 | U32 = Keine Angabe | X32 = AC Typ 2 Steckdose | Y32 = 22
A33 = 1051143 | B33 = EnBW Ostwürttemberg DonauRies AG | C33 = EnBW ODR AG | D33 = In Betrieb | E33 = Normalladeeinrichtung | F33 = 4 | G33 = 44 | H33 = 45038 | I33 = Hindenburgstraße | J33 = 3 | K33 = Volksbank Alb eG Langenau Besucherparkplatz | L33 = 89129 | M33 = Langenau | N33 = Landkreis Alb-Donau-Kreis | O33 = Baden-Württemberg | P33 = 48.498966000000003 | Q33 = 10.120977999999999 | T33 = Onlinezahlungsverfahren;RFID-Karte | U33 = Keine Angabe | X33 = AC Typ 2 Fahrzeugkupplung | Y33 = 11 | AA33 = 3059 3013 0607 2A86 48CE 3D02 0106 082A 8648 CE3D 0301 0703 4200 049B 18D3 E937 B068 29BD 19B1 BED2 63AF 3D55 2D46 E5C0 19BD 40C8 FBCC 1B1B F8E4 5300 CB3E 44FB  | AB33 = AC Typ 2 Fahrzeugkupplung | AC33 = 11 | AE33 = 3059 3013 0607 2A86 48CE 3D02 0106 082A 8648 CE3D 0301 0703 4200 04D3 87DA 7FE1 75A9 48AB 45C1 A863 C026 1E2A 0035 9089 AE3B 8445 BFBA B22B 51CC B8FE AA17 9A17  | AF33 = AC Typ 2 Fahrzeugkupplung | AG33 = 11 | AI33 = 3059 3013 0607 2A86 48CE 3D02 0106 082A 8648 CE3D 0301 0703 4200 04C1 E79A E128 09FA 8140 49C8 F37A 0A2B 35C8 41B5 4C09 882B B02C 3F54 044C CD94 19DC A743 ACC4  | AJ33 = AC Typ 2 Fahrzeugkupplung | AK33 = 11 | AM33 = 3059 3013 0607 2A86 48CE 3D02 0106 082A 8648 CE3D 0301 0703 4200 0414 31CE 5977 F9A8 C908 AB2F D98B E194 A53E 6F3B 0B31 680E BA8D EB12 9506 65DF A1B1 9EAC B713
A34 = 1033006 | B34 = SWU Energie GmbH | D34 = In Betrieb | E34 = Normalladeeinrichtung | F34 = 1 | G34 = 22 | H34 = 44105 | I34 = Sonnenstraße | J34 = 4 | L34 = 89129 | M34 = Langenau | N34 = Landkreis Alb-Donau-Kreis | O34 = Baden-Württemberg | P34 = 48.500211 | Q34 = 10.121083 | U34 = Keine Angabe | X34 = AC Typ 2 Steckdose | Y34 = 22
A35 = 1033008 | B35 = SWU Energie GmbH | D35 = In Betrieb | E35 = Normalladeeinrichtung | F35 = 1 | G35 = 22 | H35 = 44105 | I35 = Kuftenstraße | J35 = 4 | L35 = 89129 | M35 = Langenau | N35 = Landkreis Alb-Donau-Kreis | O35 = Baden-Württemberg | P35 = 48.497368999999999 | Q35 = 10.121542 | U35 = Keine Angabe | X35 = AC Typ 2 Steckdose | Y35 = 22
A36 = 1068689 | B36 = Physiotherapie im Stadtgarten | D36 = In Betrieb | E36 = Normalladeeinrichtung | F36 = 2 | G36 = 11 | H36 = 42649 | I36 = Lange Strasse | J36 = 15 | L36 = 89129 | M36 = Langenau | N36 = Landkreis Alb-Donau-Kreis | O36 = Baden-Württemberg | P36 = 48.501099000000004 | Q36 = 10.122168 | T36 = Kostenlos | U36 = Keine Angabe | X36 = AC Typ 2 Steckdose | Y36 = 11 | AB36 = AC Schuko | AC36 = 3,7
A37 = 1026233 | B37 = EnBW mobility+ AG und Co.KG  | D37 = In Betrieb | E37 = Normalladeeinrichtung | F37 = 2 | G37 = 30 | H37 = 44154 | I37 = Parkplatz Burghof | J37 = 0 | L37 = 89129 | M37 = Langenau | N37 = Landkreis Alb-Donau-Kreis | O37 = Baden-Württemberg | P37 = 48.500056999999998 | Q37 = 10.123939 | T37 = Onlinezahlungsverfahren;RFID-Karte | U37 = Keine Angabe | X37 = AC Typ 2 Steckdose; AC Schuko | Y37 = 22; 22 | AB37 = AC Typ 2 Steckdose; AC Schuko | AC37 = 22; 22
A38 = 1086250 | B38 = Joachim Stader | D38 = In Betrieb | E38 = Normalladeeinrichtung | F38 = 2 | G38 = 11 | H38 = 44980 | I38 = Kuftenstraße  | J38 = 54 | L38 = 89129 | M38 = Langenau | N38 = Landkreis Alb-Donau-Kreis | O38 = Baden-Württemberg | P38 = 48.498206000000003 | Q38 = 10.124506999999999 | T38 = Bargeld;RFID-Karte | U38 = Keine Angabe | X38 = AC Typ 2 Fahrzeugkupplung | Y38 = 11 | AB38 = AC Typ 2 Fahrzeugkupplung | AC38 = 11
A39 = 1033005 | B39 = SWU Energie GmbH | D39 = In Betrieb | E39 = Normalladeeinrichtung | F39 = 1 | G39 = 22 | H39 = 43831 | I39 = Keplerstraße | J39 = 16 | L39 = 89129 | M39 = Langenau | N39 = Landkreis Alb-Donau-Kreis | O39 = Baden-Württemberg | P39 = 48.505090000000003 | Q39 = 10.128138999999999 | U39 = Keine Angabe | X39 = AC Typ 2 Steckdose | Y39 = 22
A40 = 1157322 | B40 = MVV Energie AG | D40 = In Betrieb | E40 = Schnellladeeinrichtung | F40 = 2 | G40 = 300 | H40 = 46153 | I40 = Benzstr. | J40 = 7 | K40 = Parkplatzfläche Müller | L40 = 89129 | M40 = Langenau | N40 = Landkreis Alb-Donau-Kreis | O40 = Baden-Württemberg | P40 = 48.498739999999998 | Q40 = 10.133653000000001 | R40 = MaLIS_Mueller_Langenau | S40 = Keine Beschränkung | T40 = Kreditkarte (Lesegerät);Kreditkarte (NFC);Debitkarte (Lesegerät);Debitkarte (NFC);Onlinezahlungsverfahren;RFID-Karte | U40 = 247 | V40 = Montag; Dienstag; Mittwoch; Donnerstag; Freitag; Samstag; Sonntag | W40 = 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59; 00:00-23:59 | X40 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | Y40 = 300 | Z40 = DE*MVV*E00670*L1 | AA40 = 3059 3013 0607 2a86 48ce 3d02 0106 082a 8648 ce3d 0301 0703 4200 0400 0f39 5d98 ff52 afd8 78b7 f7a9 0cb8 0a5d 264b 76ae 03c4 8076 cadd 071a 179f 74da 3fd6 7e7e  | AB40 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | AC40 = 300 | AD40 = DE*MVV*E00670*R1 | AE40 = 3059 3013 0607 2a86 48ce 3d02 0106 082a 8648 ce3d 0301 0703 4200 04cc ac4c 0091 6f8a 0ed4 80a1 da8e feb0 7fad 0460 0c8f 44fa 1967 1830 beaf 6a4d 0a51 f2aa 6721
A41 = 1027213 | B41 = EnBW mobility+ AG und Co.KG  | D41 = In Betrieb | E41 = Schnellladeeinrichtung | F41 = 2 | G41 = 150 | H41 = 44924 | I41 = Benzstraße | J41 = 3 | L41 = 89129 | M41 = Langenau | N41 = Landkreis Alb-Donau-Kreis | O41 = Baden-Württemberg | P41 = 48.499749999999999 | Q41 = 10.13395 | T41 = Onlinezahlungsverfahren;RFID-Karte;Sonstige | U41 = Keine Angabe | X41 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | Y41 = 150 | AB41 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | AC41 = 150
A42 = 1068690 | B42 = Solarcollect | D42 = In Betrieb | E42 = Normalladeeinrichtung | F42 = 2 | G42 = 11 | H42 = 44484 | I42 = Eichlesstrasse | J42 = 18 | L42 = 89129 | M42 = Langenau | N42 = Landkreis Alb-Donau-Kreis | O42 = Baden-Württemberg | P42 = 48.505685999999997 | Q42 = 10.138781 | T42 = Bargeld | U42 = Keine Angabe | X42 = AC Typ 2 Fahrzeugkupplung | Y42 = 11 | AB42 = AC Schuko | AC42 = 3,7
A43 = 1085129 | B43 = Christian Uhlrich | D43 = In Betrieb | E43 = Normalladeeinrichtung | F43 = 1 | G43 = 6 | H43 = 44886 | I43 = Eichlesstraße  | J43 = 10 | L43 = 89129 | M43 = Langenau | N43 = Landkreis Alb-Donau-Kreis | O43 = Baden-Württemberg | P43 = 48.505091 | Q43 = 10.139106999999999 | T43 = Kostenlos | U43 = Keine Angabe | X43 = AC Typ 2 Fahrzeugkupplung | Y43 = 6
A44 = 1025445 | B44 = EnBW mobility+ AG und Co.KG  | D44 = In Betrieb | E44 = Schnellladeeinrichtung | F44 = 2 | G44 = 300 | H44 = 43532 | I44 = Flurstück | J44 = 313 | L44 = 89129 | M44 = Langenau/Seligweiler | N44 = Landkreis Alb-Donau-Kreis | O44 = Baden-Württemberg | P44 = 48.456817000000001 | Q44 = 10.029648999999999 | T44 = Onlinezahlungsverfahren;RFID-Karte | U44 = Keine Angabe | X44 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | Y44 = 300 | AB44 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | AC44 = 300
A45 = 1025446 | B45 = EnBW mobility+ AG und Co.KG  | D45 = In Betrieb | E45 = Schnellladeeinrichtung | F45 = 2 | G45 = 300 | H45 = 43532 | I45 = Flurstück | J45 = 313 | L45 = 89129 | M45 = Langenau/Seligweiler | N45 = Landkreis Alb-Donau-Kreis | O45 = Baden-Württemberg | P45 = 48.456817000000001 | Q45 = 10.029648999999999 | T45 = Onlinezahlungsverfahren;RFID-Karte | U45 = Keine Angabe | X45 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | Y45 = 300 | AB45 = DC Fahrzeugkupplung Typ Combo 2 (CCS) | AC45 = 300
A46 = 1025447 | B46 = EnBW mobility+ AG und Co.KG  | D46 = In Betrieb | E46 = Schnellladeeinrichtung | F46 = 2 | G46 = 172 | H46 = 43817 | I46 = Flurstück | J46 = 313 | L46 = 89129 | M46 = Langenau/Seligweiler | N46 = Landkreis Alb-Donau-Kreis | O46 = Baden-Württemberg | P46 = 48.456817000000001 | Q46 = 10.029648999999999 | T46 = Onlinezahlungsverfahren;RFID-Karte | U46 = Keine Angabe | X46 = DC Fahrzeugkupplung Typ Combo 2 (CCS); DC CHAdeMO | Y46 = 150; 150 | AB46 = AC Typ 2 Steckdose | AC46 = 22
A47 = 1025448 | B47 = EnBW mobility+ AG und Co.KG  | D47 = In Betrieb | E47 = Schnellladeeinrichtung | F47 = 2 | G47 = 172 | H47 = 43452 | I47 = Flurstück | J47 = 313 | L47 = 89129 | M47 = Langenau/Seligweiler | N47 = Landkreis Alb-Donau-Kreis | O47 = Baden-Württemberg | P47 = 48.456817000000001 | Q47 = 10.029648999999999 | T47 = Onlinezahlungsverfahren;RFID-Karte | U47 = Keine Angabe | X47 = DC Fahrzeugkupplung Typ Combo 2 (CCS); DC CHAdeMO | Y47 = 150; 150 | AB47 = AC Typ 2 Steckdose | AC47 = 22
A48 = 1033004 | B48 = SWU Energie GmbH | D48 = In Betrieb | E48 = Normalladeeinrichtung | F48 = 2 | G48 = 44 | H48 = 43769 | I48 = Schulstraße | J48 = 8 | L48 = 89129 | M48 = Nerenstetten | N48 = Landkreis Alb-Donau-Kreis | O48 = Baden-Württemberg | P48 = 48.529837999999998 | Q48 = 10.098277 | U48 = Keine Angabe | X48 = AC Typ 2 Steckdose | Y48 = 22 | AB48 = AC Typ 2 Steckdose | AC48 = 22
A49 = 1032985 | B49 = SWU Energie GmbH | D49 = In Betrieb | E49 = Normalladeeinrichtung | F49 = 2 | G49 = 22 | H49 = 43603 | I49 = Hausener Straße | J49 = 13 | L49 = 89129 | M49 = Setzingen | N49 = Landkreis Alb-Donau-Kreis | O49 = Baden-Württemberg | P49 = 48.538896000000001 | Q49 = 10.129616 | U49 = Keine Angabe | X49 = AC Typ 2 Steckdose | Y49 = 22 | AB49 = AC Typ 2 Steckdose | AC49 = 22
A50 = 1086303 | B50 = Johannes Stängle | D50 = In Betrieb | E50 = Normalladeeinrichtung | F50 = 2 | G50 = 22 | H50 = 44825 | I50 = Ortsstr. | J50 = 7 | L50 = 89129 | M50 = Wettingen | N50 = Landkreis Alb-Donau-Kreis | O50 = Baden-Württemberg | P50 = 48.518329000000001 | Q50 = 10.119319000000001 | S50 = Keine Beschränkung | T50 = Bargeld;Sonstige | U50 = Keine Angabe | X50 = AC Typ 2 Steckdose | Y50 = 11 | AB50 = AC Typ 2 Steckdose | AC50 = 11
```

## kba_fz27_2026_07

### FZ 27.1

```text
B2 = zurück zum Inhaltsverzeichnis
B4 = Fahrzeugzulassungen (FZ)
B5 = Bestand an Kraftfahrzeugen und Kraftfahrzeuganhängern nach Bundesländern, Fahrzeugarten und ausgewählten Merkmalen
B6 = FZ 27.1 Bestand an Kraftfahrzeugen und Kraftfahrzeuganhängern am 1. Juli 2026 nach Bundesländern und Fahrzeugarten
B8 = Land | C8 = Krafträder | D8 = Personenkraftwagen | E8 = Kraftomnibusse | F8 = Lastkraftwagen | G8 = Zugmaschinen insgesamt | H8 = davon  Sattelzugmaschinen | I8 = davon  sonstige Zugmaschinen | J8 = davon  land-/ forstwirtschaftliche  Zugmaschinen | K8 = Sonstige Kfz | L8 = Kraftfahrzeug-anhänger | M8 = Fahrzeuge  insgesamt
B9 = Baden-Württemberg | C9 = 799690 | D9 = 7015759 | E9 = 10196 | F9 = 471828 | G9 = 404262 | H9 = 26834 | I9 = 93416 | J9 = 284012 | K9 = 40185 | L9 = 1178000 | M9 = 9919920
B10 = Bayern | C10 = 1104300 | D10 = 8527085 | E10 = 15845 | F10 = 636957 | G10 = 740016 | H10 = 36638 | I10 = 134806 | J10 = 568572 | K10 = 64018 | L10 = 1591111 | M10 = 12679332
B11 = Berlin | C11 = 124955 | D11 = 1219191 | E11 = 2456 | F11 = 117507 | G11 = 7838 | H11 = 3838 | I11 = 303 | J11 = 3697 | K11 = 9642 | L11 = 101332 | M11 = 1582921
B12 = Brandenburg | C12 = 167470 | D12 = 1507218 | E12 = 2971 | F12 = 165430 | G12 = 59410 | H12 = 7843 | I12 = 3805 | J12 = 47762 | K12 = 14930 | L12 = 399400 | M12 = 2316829
B13 = Bremen | C13 = 21466 | D13 = 302050 | E13 = 513 | F13 = 21749 | G13 = 3646 | H13 = 2001 | I13 = 296 | J13 = 1349 | K13 = 2375 | L13 = 37228 | M13 = 389027
B14 = Hamburg | C14 = 62040 | D14 = 829662 | E14 = 2790 | F14 = 66510 | G14 = 8121 | H14 = 3599 | I14 = 384 | J14 = 4138 | K14 = 5686 | L14 = 78078 | M14 = 1052887
B15 = Hessen | C15 = 374480 | D15 = 3937917 | E15 = 5937 | F15 = 281578 | G15 = 159891 | H15 = 13787 | I15 = 29319 | J15 = 116785 | K15 = 25986 | L15 = 525693 | M15 = 5311482
B16 = Mecklenburg-Vorpommern | C16 = 88024 | D16 = 893769 | E16 = 2010 | F16 = 98636 | G16 = 42080 | H16 = 5547 | I16 = 1494 | J16 = 35039 | K16 = 10129 | L16 = 267297 | M16 = 1401945
B17 = Niedersachsen | C17 = 471319 | D17 = 5025325 | E17 = 8469 | F17 = 384788 | G17 = 281153 | H17 = 32301 | I17 = 33198 | J17 = 215654 | K17 = 39993 | L17 = 1133204 | M17 = 7344251
B18 = Nordrhein-Westfalen | C18 = 963333 | D18 = 10694681 | E18 = 18556 | F18 = 819009 | G18 = 285264 | H18 = 53276 | I18 = 34351 | J18 = 197637 | K18 = 62044 | L18 = 1443727 | M18 = 14286614
B19 = Rheinland-Pfalz | C19 = 284003 | D19 = 2664247 | E19 = 6571 | F19 = 191645 | G19 = 162301 | H19 = 12221 | I19 = 30465 | J19 = 119615 | K19 = 17561 | L19 = 484776 | M19 = 3811104
B20 = Saarland | C20 = 67536 | D20 = 654875 | E20 = 1184 | F20 = 44508 | G20 = 20429 | H20 = 1899 | I20 = 3702 | J20 = 14828 | K20 = 3620 | L20 = 115417 | M20 = 907569
```

### FZ 27.2

```text
B2 = zurück zum Inhaltsverzeichnis
B4 = Fahrzeugzulassungen (FZ)
B5 = Bestand an Kraftfahrzeugen und Kraftfahrzeuganhängern nach Bundesländern, Fahrzeugarten und ausgewählten Merkmalen
B6 = FZ 27.2 Bestand an Kraftfahrzeugen am 1. Juli 2026 nach Bundesländern, Kraftstoffarten und Fahrzeugarten
B8 = Land | C8 = Kraftstoffart | D8 = Krafträder | E8 = Personenkraftwagen | F8 = Kraftomnibusse | G8 = Lastkraftwagen | H8 = Zugmaschinen insgesamt | I8 = davon  Sattelzugmaschinen | J8 = davon  sonstige Zugmaschinen | K8 = davon  land-/ forstwirtschaftliche  Zugmaschinen | L8 = Sonstige Kfz | M8 = Kraftfahrzeuge  insgesamt
B9 = Baden-Württemberg | C9 = Benzin | D9 = 787640 | E9 = 4052886 | F9 = 13 | G9 = 23311 | H9 = 25949 | I9 = 7 | J9 = 801 | K9 = 25141 | L9 = 1515 | M9 = 4891314
C10 = Diesel | D10 = 975 | E10 = 1859208 | F10 = 8234 | G10 = 431246 | H10 = 376977 | I10 = 26085 | J10 = 92467 | K10 = 258425 | L10 = 37921 | M10 = 2714561
C11 = Gas insgesamt | D11 = 14 | E11 = 37238 | F11 = 24 | G11 = 4558 | H11 = 289 | I11 = 263 | J11 = 5 | K11 = 21 | L11 = 145 | M11 = 42268
C12 = Elektro (BEV) | D12 = 10120 | E12 = 369574 | F12 = 562 | G12 = 10837 | H12 = 637 | I12 = 399 | J12 = 20 | K12 = 218 | L12 = 312 | M12 = 392042
C13 = Hybrid insgesamt | D13 = 313 | E13 = 695642 | F13 = 1346 | G13 = 1747 | H13 = 19 | I13 = 1 | J13 = 4 | K13 = 14 | L13 = 219 | M13 = 699286
C14 = darunter Plug-in | D14 = 5 | E14 = 193186 | F14 = 56 | G14 = 1232 | H14 = 2 | I14 = - | J14 = - | K14 = 2 | L14 = 54 | M14 = 194535
C15 = Sonstige | D15 = 628 | E15 = 1211 | F15 = 17 | G15 = 129 | H15 = 391 | I15 = 79 | J15 = 119 | K15 = 193 | L15 = 73 | M15 = 2449
B16 = Baden-Württemberg zusammen | D16 = 799690 | E16 = 7015759 | F16 = 10196 | G16 = 471828 | H16 = 404262 | I16 = 26834 | J16 = 93416 | K16 = 284012 | L16 = 40185 | M16 = 8741920
B17 = Bayern | C17 = Benzin | D17 = 1086100 | E17 = 4745532 | F17 = 10 | G17 = 29081 | H17 = 53543 | I17 = 3 | J17 = 1244 | K17 = 52296 | L17 = 2768 | M17 = 5917034
C18 = Diesel | D18 = 1870 | E18 = 2411229 | F18 = 13255 | G18 = 583076 | H18 = 684846 | I18 = 35618 | J18 = 133484 | K18 = 515744 | L18 = 58639 | M18 = 3752915
C19 = Gas insgesamt | D19 = 27 | E19 = 42004 | F19 = 189 | G19 = 5390 | H19 = 513 | I19 = 492 | J19 = 4 | K19 = 17 | L19 = 209 | M19 = 48332
C20 = Elektro (BEV) | D20 = 14102 | E20 = 459811 | F20 = 840 | G20 = 16726 | H20 = 731 | I20 = 402 | J20 = 23 | K20 = 306 | L20 = 380 | M20 = 492590
```

### FZ 27.5

```text
B2 = zurück zum Inhaltsverzeichnis
B4 = Fahrzeugzulassungen (FZ)
B5 = Bestand an Kraftfahrzeugen und Kraftfahrzeuganhängern nach Bundesländern, Fahrzeugarten und ausgewählten Merkmalen
B6 = FZ 27.5 Bestand an Personenkraftwagen am 1. Juli 2026 nach Bundesländern, gewerblichen und privaten Halterinnen und Haltern und Kraftstoffarten
B8 = Land | C8 = Haltergruppe | D8 = Benzin | E8 = Diesel | F8 = Gas insgesamt | G8 = Elektro (BEV) | H8 = Hybrid  insgesamt | I8 = darunter  Plug-in | J8 = Sonstige | K8 = Personenkraftwagen insgesamt
B9 = Baden-Württemberg | C9 = Gewerbliche Halterinnen und Halter | D9 = 211211 | E9 = 275410 | F9 = 2640 | G9 = 153570 | H9 = 233871 | I9 = 95653 | J9 = 114 | K9 = 876816
C10 = Private Halterinnen und Halter | D10 = 3841391 | E10 = 1583529 | F10 = 34596 | G10 = 215792 | H10 = 461521 | I10 = 97422 | J10 = 1097 | K10 = 6137926
B11 = Baden-Württemberg zusammen | D11 = 4052886 | E11 = 1859208 | F11 = 37238 | G11 = 369574 | H11 = 695642 | I11 = 193186 | J11 = 1211 | K11 = 7015759
B12 = Bayern | C12 = Gewerbliche Halterinnen und Halter | D12 = 291915 | E12 = 338677 | F12 = 2919 | G12 = 179112 | H12 = 313549 | I12 = 100855 | J12 = 230 | K12 = 1126402
C13 = Private Halterinnen und Halter | D13 = 4453443 | E13 = 2072453 | F13 = 39082 | G13 = 280677 | H13 = 553523 | I13 = 110796 | J13 = 1182 | K13 = 7400360
B14 = Bayern zusammen | D14 = 4745532 | E14 = 2411229 | F14 = 42004 | G14 = 459811 | H14 = 867097 | I14 = 211656 | J14 = 1412 | K14 = 8527085
B15 = Berlin | C15 = Gewerbliche Halterinnen und Halter | D15 = 52563 | E15 = 44685 | F15 = 652 | G15 = 28004 | H15 = 49471 | I15 = 16612 | J15 = 59 | K15 = 175434
C16 = Private Halterinnen und Halter | D16 = 712542 | E16 = 193407 | F16 = 9544 | G16 = 26325 | H16 = 100986 | I16 = 18058 | J16 = 313 | K16 = 1043117
B17 = Berlin zusammen | D17 = 765306 | E17 = 238237 | F17 = 10200 | G17 = 54437 | H17 = 150639 | I17 = 34743 | J17 = 372 | K17 = 1219191
B18 = Brandenburg | C18 = Gewerbliche Halterinnen und Halter | D18 = 37746 | E18 = 47256 | F18 = 697 | G18 = 12552 | H18 = 25534 | I18 = 7865 | J18 = 42 | K18 = 123827
C19 = Private Halterinnen und Halter | D19 = 892011 | E19 = 335218 | F19 = 10857 | G19 = 36549 | H19 = 108314 | I19 = 21925 | J19 = 417 | K19 = 1383366
B20 = Brandenburg zusammen | D20 = 929768 | E20 = 382483 | F20 = 11554 | G20 = 49103 | H20 = 133851 | I20 = 29791 | J20 = 459 | K20 = 1507218
```

### FZ 27.9

```text
B2 = zurück zum Inhaltsverzeichnis
B4 = Fahrzeugzulassungen (FZ)
B5 = Bestand an Kraftfahrzeugen und Kraftfahrzeuganhängern nach Bundesländern, Fahrzeugarten und ausgewählten Merkmalen
B6 = FZ 27.9 Bestand an Personenkraftwagen nach Quartalen sowie nach ausgewählten Kraftstoffarten bzw. Energiequellen
B8 = Quartal | C8 = Anzahl insgesamt | D8 = Darunter mit alternativem Antrieb
D9 = Anzahl insgesamt | E9 = Anteil in % | F9 = davon
F10 = Elektro-Antriebe | K10 = Hybrid (ohne Plug-in-Hybrid) | N10 = Gas insgesamt | O10 = Wasserstoff
F11 = Anzahl insgesamt | G11 = Anteil in % | H11 = davon | K11 = Anzahl insgesamt | L11 = darunter
H12 = Elektro (BEV) | I12 = Brennstoffzelle  (Wasserstoff) | J12 = Plug-in-Hybrid | L12 = Benzin-Hybrid | M12 = Diesel-Hybrid
B13 = 01.07.2026 | C13 = 49696710 | D13 = 7518224 | E13 = 15.1 | F13 = 3593451 | G13 = 47.8 | H13 = 2365047 | I13 = 1541 | J13 = 1226863 | K13 = 3580166 | L13 = 2746325 | M13 = 830849 | N13 = 344598 | O13 = 9
B14 = 01.04.2026 | C14 = 49546014 | D14 = 7095118 | E14 = 14.3 | F14 = 3338673 | G14 = 47.1 | H14 = 2169717 | I14 = 1522 | J14 = 1167434 | K14 = 3411187 | L14 = 2596348 | M14 = 813914 | N14 = 345249 | O14 = 9
B15 = 01.01.2026 | C15 = 49486487 | D15 = 6749257 | E15 = 13.6385858224287 | F15 = 3158793 | G15 = 46.802085029507701 | H15 = 2034260 | I15 = 1575 | J15 = 1122958 | K15 = 3239605 | L15 = 2448955 | M15 = 790538 | N15 = 350851 | O15 = 8
B16 = 01.10.2025 | C16 = 49574729 | D16 = 6466581 | E16 = 13 | F16 = 3017121 | G16 = 46.7 | H16 = 1929651 | I16 = 1569 | J16 = 1085901 | K16 = 3093219 | L16 = 2322812 | M16 = 770303 | N16 = 356232 | O16 = 9
B17 = 01.07.2025 | C17 = 49525608 | D17 = 6169212 | E17 = 12.5 | F17 = 2878689 | G17 = 46.7 | H17 = 1835578 | I17 = 1638 | J17 = 1041473 | K17 = 2928281 | L17 = 2180731 | M17 = 747454 | N17 = 362235 | O17 = 7
B18 = 01.04.2025 | C18 = 49360831 | D18 = 5853500 | E18 = 11.9 | F18 = 2733615 | G18 = 46.7 | H18 = 1735021 | I18 = 1669 | J18 = 996925 | K18 = 2752659 | L18 = 2033481 | M18 = 719081 | N18 = 367219 | O18 = 7
B19 = 01.01.2025 | C19 = 49339166 | D19 = 5583452 | E19 = 11.3 | F19 = 2620868 | G19 = 46.9 | H19 = 1651643 | I19 = 1802 | J19 = 967423 | K19 = 2589533 | L19 = 1897379 | M19 = 692054 | N19 = 373045 | O19 = 6
B20 = 01.10.2024 | C20 = 49415217 | D20 = 5360888 | E20 = 10.8 | F20 = 2545576 | G20 = 47.5 | H20 = 1588313 | I20 = 1978 | J20 = 955285 | K20 = 2436751 | L20 = 1775358 | M20 = 661293 | N20 = 378555 | O20 = 6
```

### FZ 27.15

```text
B2 = zurück zum Inhaltsverzeichnis
B4 = Fahrzeugzulassungen (FZ)
B5 = Bestand an Kraftfahrzeugen und Kraftfahrzeuganhängern nach Bundesländern, Fahrzeugarten und ausgewählten Merkmalen
B6 = FZ 27.15 Bestand an Personenkraftwagen am 1. Juli 2026 nach Bundesländern und Zulassungsbezirken sowie nach ausgewählten Kraftstoffarten bzw. Energiequellen
B8 = Land | C8 = Statistische  Kennziffer | D8 = Zulassungsbezirk | E8 = Anzahl insgesamt | F8 = Darunter mit alternativem Antrieb (ohne Brennstoffzelle (Wasserstoff) und Wasserstoff)
F9 = Anzahl insgesamt | G9 = Anteil in % | H9 = davon
H10 = Elektro-Antriebe (ohne Brennstoffzelle (Wasserstoff)) | L10 = Hybrid (ohne Plug-in-Hybrid) | O10 = Gas insgesamt
H11 = Anzahl insgesamt | I11 = Anteil in % | J11 = davon | L11 = Anzahl insgesamt | M11 = darunter
J12 = Elektro (BEV) | K12 = Plug-in-Hybrid | M12 = Benzin-Hybrid | N12 = Diesel-Hybrid
B13 = Baden-Württemberg | C13 = 08111 | D13 = STUTTGART,STADT | E13 = 301767 | F13 = 74218 | G13 = 24.6 | H13 = 42158 | I13 = 56.8 | J13 = 25035 | K13 = 17123 | L13 = 30470 | M13 = 21443 | N13 = 9017 | O13 = 1590
C14 = 08115 | D14 = BOEBLINGEN | E14 = 267836 | F14 = 61893 | G14 = 23.1 | H14 = 34126 | I14 = 55.1 | J14 = 21110 | K14 = 13016 | L14 = 26417 | M14 = 20491 | N14 = 5917 | O14 = 1350
C15 = 08116 | D15 = ESSLINGEN | E15 = 345417 | F15 = 60037 | G15 = 17.399999999999999 | H15 = 31095 | I15 = 51.8 | J15 = 19641 | K15 = 11454 | L15 = 27159 | M15 = 20702 | N15 = 6439 | O15 = 1783
C16 = 08117 | D16 = GOEPPINGEN | E16 = 172961 | F16 = 25368 | G16 = 14.7 | H16 = 11843 | I16 = 46.7 | J16 = 7670 | K16 = 4173 | L16 = 12229 | M16 = 9582 | N16 = 2634 | O16 = 1296
C17 = 08118 | D17 = LUDWIGSBURG | E17 = 343091 | F17 = 55445 | G17 = 16.2 | H17 = 27701 | I17 = 50 | J17 = 17517 | K17 = 10184 | L17 = 26030 | M17 = 20617 | N17 = 5400 | O17 = 1714
C18 = 08119 | D18 = REMS-MURR-KREIS | E18 = 276271 | F18 = 41852 | G18 = 15.1 | H18 = 20644 | I18 = 49.3 | J18 = 13243 | K18 = 7401 | L18 = 19636 | M18 = 15518 | N18 = 4100 | O18 = 1572
C19 = 08121 | D19 = HEILBRONN,STADT | E19 = 70791 | F19 = 10962 | G19 = 15.5 | H19 = 4842 | I19 = 44.2 | J19 = 2798 | K19 = 2044 | L19 = 5779 | M19 = 3891 | N19 = 1887 | O19 = 341
C20 = 08125 | D20 = HEILBRONN | E20 = 260932 | F20 = 46164 | G20 = 17.7 | H20 = 19710 | I20 = 42.7 | J20 = 13311 | K20 = 6399 | L20 = 25274 | M20 = 14356 | N20 = 10912 | O20 = 1180
```

### FZ 27.16

```text
B2 = zurück zum Inhaltsverzeichnis
B4 = Fahrzeugzulassungen (FZ)
B5 = Bestand an Kraftfahrzeugen und Kraftfahrzeuganhängern nach Bundesländern, Fahrzeugarten und ausgewählten Merkmalen
B6 = FZ 27.16 Bestand an Personenkraftwagen am 1. Juli 2026 nach Postleitzahlen sowie nach gewerblichen und privaten Halterinnen
B7 = und Haltern und den Antriebsarten Elektro (BEV) und Plug-in-Hybrid
B9 = Postleitzahl | C9 = gewerbliche Halterinnen und Halter | F9 = private Halterinnen und Halter
C10 = insgesamt | D10 = darunter | F10 = insgesamt | G10 = darunter
D11 = Elektro (BEV) | E11 = Plug-in-Hybrid | G11 = Elektro (BEV) | H11 = Plug-in-Hybrid
B12 = 01067 | C12 = 3084 | D12 = 378 | E12 = 306 | F12 = 4135 | G12 = 113 | H12 = 73
B13 = 01069 | C13 = 2146 | D13 = 472 | E13 = 209 | F13 = 6555 | G13 = 100 | H13 = 79
B14 = 01097 | C14 = 2034 | D14 = 188 | E14 = 162 | F14 = 4543 | G14 = 114 | H14 = 68
B15 = 01099 | C15 = 2212 | D15 = 277 | E15 = 173 | F15 = 8280 | G15 = 179 | H15 = 87
B16 = 01108 | C16 = 304 | D16 = 35 | E16 = 20 | F16 = 3108 | G16 = 97 | H16 = 61
B17 = 01109 | C17 = 1591 | D17 = 256 | E17 = 246 | F17 = 9413 | G17 = 233 | H17 = 124
B18 = 01127 | C18 = 632 | D18 = 49 | E18 = 48 | F18 = 4540 | G18 = 80 | H18 = 32
B19 = 01129 | C19 = 1646 | D19 = 145 | E19 = 178 | F19 = 7218 | G19 = 128 | H19 = 69
B20 = 01139 | C20 = 1287 | D20 = 198 | E20 = 94 | F20 = 7659 | G20 = 123 | H20 = 96
```

### FZ 27.17

```text
B2 = zurück zum Inhaltsverzeichnis
B4 = Fahrzeugzulassungen (FZ)
B5 = Bestand an Kraftfahrzeugen und Kraftfahrzeuganhängern nach Bundesländern, Fahrzeugarten und ausgewählten Merkmalen
B6 = FZ 27.17 Bestand an Personenkraftwagen am 1. Juli 2026 nach Bundesländern, Zulassungsbezirken und Gemeinden sowie nach gewerblichen und privaten Halterinnen und
B7 = Elektro (BEV) und Plug-in-Hybrid
B9 = Land | C9 = Zulassungsbezirk | D9 = Gemeinde | E9 = gewerbliche Halterinnen und Halter | H9 = private Halterinnen und Halter
E10 = insgesamt | F10 = darunter | H10 = insgesamt | I10 = darunter
F11 = Elektro (BEV) | G11 = Plug-in-Hybrid | I11 = Elektro (BEV) | J11 = Plug-in-Hybrid
B12 = Baden-Württemberg | C12 = 08111 STUTTGART,STADT | D12 = STUTTGART,LANDESHAUPTSTADT | E12 = 79714 | F12 = 16623 | G12 = 12327 | H12 = 222053 | I12 = 8412 | J12 = 4796
C13 = 08115 BOEBLINGEN | D13 = AIDLINGEN | E13 = 289 | F13 = 31 | G13 = 9 | H13 = 6110 | I13 = 335 | J13 = 148
D14 = ALTDORF | E14 = 102 | F14 = 8 | G14 = 17 | H14 = 2943 | I14 = 159 | J14 = 57
D15 = BOEBLINGEN,ST. | E15 = 5957 | F15 = 992 | G15 = 943 | H15 = 26153 | I15 = 1070 | J15 = 583
D16 = BONDORF | E16 = 194 | F16 = 38 | G16 = 24 | H16 = 3747 | I16 = 200 | J16 = 74
D17 = DECKENPFRONN | E17 = 184 | F17 = 34 | G17 = 9 | H17 = 2059 | I17 = 124 | J17 = 58
D18 = EHNINGEN | E18 = 719 | F18 = 108 | G18 = 130 | H18 = 5268 | I18 = 332 | J18 = 155
D19 = GAERTRINGEN | E19 = 632 | F19 = 84 | G19 = 57 | H19 = 7174 | I19 = 383 | J19 = 174
D20 = GAEUFELDEN | E20 = 292 | F20 = 48 | G20 = 43 | H20 = 5764 | I20 = 300 | J20 = 127
```

## Review needed before ETL

- Locate the actual BNetzA header row; do not treat title and legal notes as data.
- Identify repeated charging-point field groups; one equipment row may hold multiple points.
- Retain all original data and distinguish raw, normalized, and dashboard layers.
- Treat KBA table subtotals and district/ZIP/municipality reports as ALTERNATIVE breakdowns (never blindly sum them together).
- Match geography and snapshot dates before comparing vehicles to charging points.
