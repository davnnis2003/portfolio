from typing import Any, Dict, List, Optional, Tuple


class RuleEngine:
    """
    Evaluates lead qualification rules against intake data.
    Rules are based on docs/qualification_rules.md.
    """

    def evaluate(self, intake_data: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Main entry point for rule evaluation.
        Returns (status, reasons).
        Status can be "QUALIFIED", "DISQUALIFIED", or "NEEDS_REVIEW".
        """
        product = intake_data.get("product", "").lower()
        fields = intake_data.get("fields", {})
        region = intake_data.get("address", {}).get("region", "")

        reasons = []

        if product == "fassade":
            reasons = self._evaluate_fassade(fields, region)
        elif product == "ogd":
            reasons = self._evaluate_ogd(fields)
        elif product == "kellerdecke":
            reasons = self._evaluate_kellerdecke(fields)
        else:
            return "NEEDS_REVIEW", [f"Unknown product: {product}"]

        if reasons:
            return "DISQUALIFIED", reasons
        
        return "QUALIFIED", []

    def _evaluate_fassade(self, fields: Dict[str, Any], region: str) -> List[str]:
        reasons = []

        # 1. Universal Rules
        building_type = fields.get("building_type", "")
        # Holzständerbauweise / Fachwerkhaus
        if any(term in building_type.lower() for term in ["holzständer", "fachwerk"]):
            reasons.append("Holzständerbauweise / Fachwerkhaus nicht dämmbar")

        # MFH mit 3 oder mehr Vollgeschossen
        n_vollgeschosse = fields.get("n_vollgeschosse", 0)
        if building_type == "MFH" and n_vollgeschosse >= 3:
            reasons.append("MFH mit 3 oder mehr Vollgeschossen nicht im Produkt")

        # Wall thickness checks
        mauerstarke = fields.get("mauerstarke_cm")
        if mauerstarke is not None:
            if mauerstarke < 28:
                reasons.append(f"Mauerwerk {mauerstarke} cm < 28 cm nicht feasible")
            elif mauerstarke > 50:
                reasons.append(f"Mauerwerk {mauerstarke} cm > 50 cm nicht feasible")
            elif mauerstarke == 38:
                reasons.append("Mauerwerk exakt 38 cm konstruktiv ausgeschlossen")

        # 2. Region-specific rules
        year = fields.get("building_year")
        fassade_typ = fields.get("fassaden_typ", "").lower()

        if region == "SH_NordNieder_HH":
            if year and year < 1890:
                reasons.append(f"Region {region}: Baujahr {year} < 1890 nicht feasible")
            if year and year > 1975 and mauerstarke != 36.5:
                reasons.append(f"Region {region}: Baujahr {year} > 1975 und Mauerstärke {mauerstarke} != 36.5 cm")
            if "gelbklinker" in fassade_typ and mauerstarke and mauerstarke < 41:
                reasons.append(f"Region {region}: Gelbklinkerfassade unter 41 cm Mauerstärke")

        elif region == "DDR_Ost":
            if year and year < 1890:
                reasons.append(f"Region {region}: Baujahr {year} < 1890 nicht feasible")
            if year and year > 1965:
                is_klinker = "klinker" in fassade_typ
                if not (is_klinker and mauerstarke and mauerstarke <= 32):
                    reasons.append(f"Region {region}: Baujahr {year} > 1965 ohne passende Klinkerfassade/Mauerstärke")

        elif region == "NRW_SudNieder":
            if year and year < 1890:
                reasons.append(f"Region {region}: Baujahr {year} < 1890 nicht feasible")
            if year and year > 1970:
                is_klinker = "klinker" in fassade_typ
                if not (mauerstarke == 36.5 or is_klinker):
                    reasons.append(f"Region {region}: Baujahr {year} > 1970 ohne 36.5cm Mauerstärke oder Klinker")

        elif region == "Sud_Hessen_RLP":
            if year and year < 1880:
                reasons.append(f"Region {region}: Baujahr {year} < 1880 nicht feasible")
            
            # Alles außer Klinkerfassade UND Mauerstärke 30–33 cm UND Baujahr vor 1950 → nicht feasible
            is_klinker = "klinker" in fassade_typ
            mauer_ok = mauerstarke is not None and 30 <= mauerstarke <= 33
            year_ok = year is not None and year < 1950
            
            if not (is_klinker and mauer_ok and year_ok):
                reasons.append(f"Region {region}: Nur Klinker, 30-33cm Mauerstärke, Baujahr < 1950 erlaubt")

        return reasons

    def _evaluate_ogd(self, fields: Dict[str, Any]) -> List[str]:
        reasons = []
        if fields.get("dachboden_zukunft_wohnraum"):
            reasons.append("Dachboden soll zukünftig als Wohnraum genutzt werden")
        return reasons

    def _evaluate_kellerdecke(self, fields: Dict[str, Any]) -> List[str]:
        reasons = []
        if fields.get("feuchtigkeit"):
            reasons.append("Schimmel- oder Feuchtigkeitsprobleme im Keller")
        if fields.get("is_gewoelbekeller"):
            reasons.append("Gewölbekeller nicht feasible")
        return reasons
