# ClimateTech Qualification Rules (Appendix)

These are the rules our sales reps apply during the 10-minute qualification call. They're deterministic and driven by building data (year, wall thickness, façade type, region, building type).

The rules are written in the form *"not feasible if…"* — if a lead trips any condition, it's disqualified at phase 1. Exceptions are captured as **Sonderfaktoren** at the bottom.

Your system can (but doesn't have to) use these rules. Some of the 10 test leads are solved by rules alone; others need more than rules.

---

## Glossary (German → English)

The German terms below appear throughout the rules, the structured intake fields, and the call transcripts. Quick reference:

| Term | English |
|---|---|
| Fassadendämmung | Façade / wall insulation |
| Kerndämmung / Einblasdämmung | Cavity wall insulation (blown-in foam) |
| Obere Geschossdecke (OGD) | Upper-floor ceiling (attic floor insulation) |
| Kellerdeckendämmung | Basement ceiling insulation |
| Hohlraum | Cavity (air gap inside the wall) |
| Mauerwerk / Mauerstärke | Masonry / wall thickness (in cm) |
| Klinker (Rot- / Gelb-) | Clinker brick (red / yellow) |
| Holzständerbauweise / Fachwerkhaus | Timber-frame / half-timbered house |
| Vollgeschoss | Full storey |
| Gewölbekeller | Vaulted (arched) cellar |
| Feuchtigkeit | Moisture |
| Baujahr (Bj.) | Year built |
| EFH / DHH / RH / MFH | Single-family / semi-detached / terraced / multi-family house |
| Bedarfsanalyse | Needs analysis |
| Vor-Ort-Termin | On-site visit |
| Dämmexperte | Insulation expert (the follow-up video-call role) |
| Sonderfaktor | Special factor (positive override that can flip a disqualification) |

---

## Product: Fassadendämmung (Kerndämmung / Einblasdämmung)

### Universally disqualifying

- Holzständerbauweise / Fachwerkhaus → nicht dämmbar
- MFH mit 3 oder mehr Vollgeschossen → nicht im Produkt
- Mauerwerk < 28 cm → nicht feasible
- Mauerwerk > 50 cm → nicht feasible
- Mauerwerk exakt 38 cm → konstruktiv ausgeschlossen

### Region-specific rules

**Region: Schleswig-Holstein / nördliches Niedersachsen / Hamburg / westliches MVP / Bremen**
- Baujahr vor 1890 → nicht feasible
- Baujahr nach 1975, außer Mauerstärke = 36,5 cm
- Gelbklinkerfassade unter 41 cm Mauerstärke

**Region: ehemalige DDR (Sachsen, Brandenburg, Thüringen, östl. Sachsen-Anhalt, östl. MVP)**
- Baujahr vor 1890 → nicht feasible
- Baujahr nach 1965, außer Klinkerfassade UND Mauerstärke ≤ 32 cm

**Region: NRW / südliches Niedersachsen**
- Baujahr vor 1890 → nicht feasible
- Baujahr nach 1970, außer Mauerstärke = 36,5 cm ODER Rotklinkerfassade

**Region: Süddeutschland / Hessen / Rheinland-Pfalz**
- Baujahr vor 1880 → nicht feasible
- Alles außer Klinkerfassade UND Mauerstärke 30–33 cm UND Baujahr vor 1950 → nicht feasible

---

## Product: Obere Geschossdeckendämmung (OGD)

### Disqualifying

- Dachboden soll zukünftig als Wohnraum genutzt werden → nicht feasible
  - **Ausnahme:** Dämmung unter Bestandsboden (eigene Produktvariante)

---

## Product: Kellerdeckendämmung

### Disqualifying

- Schimmel- oder Feuchtigkeitsprobleme im Keller → müssen erst beseitigt werden
- Gewölbekeller → nicht feasible

---

## Sonderfaktoren (positive overrides)

Können bei Grenzfällen eine Disqualifikation überschreiben. Nicht automatisch anwendbar — erfordern menschliche Prüfung.

- **Maurermeister hat für sich selbst gebaut** (typisch höhere Bauqualität)
- **Norddeutsches Bauunternehmen hat in Süddeutschland gebaut** (typisch nordische Bauweise mit Hohlraum)
- **Nachbarhaus aus vergleichbarer Epoche (max. 5 Jahre Differenz) wurde bereits gedämmt** (direkte Evidenz)
- **Kunde ist Handwerker und macht verlässliche Aussagen** (erhöht Datenqualität)

---

## Rep call script (short)

Standard Einstieg, dann produkt-spezifische Datenerhebung:

**Einstieg:** Sie hatten eine Anfrage gestellt, worum geht es?

**Pro Produkt abzufragen:**

| Produkt | Zentrale Felder |
|---|---|
| Fassade | Baujahr, Fassadentyp, Mauerstärke, Hohlraum ja/nein (+ Größe), Adresse |
| OGD | Baujahr, aktuelle Nutzung Dachboden, zukünftige Wohnraumnutzung, bestehende Dämmung |
| Kellerdecke | Baujahr, Gewölbekeller ja/nein, Anzahl Räume, Rohre, Feuchtigkeit ja/nein |

**Bedarfsanalyse:** Warum dämmen? Wann Umsetzung? Wer entscheidet? Heizsystem? Heizkosten? Budget?

**Unterlagen anfordern:** Grundriss, Fotos, ggf. Baubeschreibung / ISFP.
