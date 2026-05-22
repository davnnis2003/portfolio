from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="triage-cli",
    help="CLI client for the ClimateTech Lead Triage prediction API.",
    no_args_is_help=True,
)

_DEFAULT_HOST = "http://localhost:8000"


def _base_options(ctx: typer.Context, host: str) -> str:
    return host


def _post(host: str, path: str, payload: dict) -> dict:
    url = f"{host.rstrip('/')}{path}"
    try:
        resp = httpx.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        rprint(f"[red]Cannot connect to API at {url}. Is the server running?[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        rprint(f"[red]API error {e.response.status_code}:[/red] {e.response.text}")
        raise typer.Exit(1)


def _lead_payload(
    region: str,
    product: str,
    customer_segment: str,
    call_duration_min: float,
    building_year: int,
    has_hohlraum: bool,
    heating_system: str,
    lead_id: Optional[str],
    has_issues_prob: Optional[float],
    confidence_score_pred: Optional[float],
    transcript_text: Optional[str],
    n_vollgeschosse: Optional[float],
    fassaden_typ: Optional[str],
    mauerstarke_cm: Optional[float],
    is_gewoelbekeller: Optional[bool],
    feuchtigkeit: Optional[bool],
    dachboden_zukunft_wohnraum: Optional[bool],
) -> dict:
    payload: dict = {
        "region": region,
        "product": product,
        "customer_segment": customer_segment,
        "call_duration_min": call_duration_min,
        "building_year": building_year,
        "has_hohlraum": has_hohlraum,
        "heating_system": heating_system,
    }
    if lead_id is not None:
        payload["lead_id"] = lead_id
    if has_issues_prob is not None:
        payload["has_issues_prob"] = has_issues_prob
    if confidence_score_pred is not None:
        payload["confidence_score_pred"] = confidence_score_pred
    if transcript_text is not None:
        payload["transcript_text"] = transcript_text
    if n_vollgeschosse is not None:
        payload["n_vollgeschosse"] = n_vollgeschosse
    if fassaden_typ is not None:
        payload["fassaden_typ"] = fassaden_typ
    if mauerstarke_cm is not None:
        payload["mauerstarke_cm"] = mauerstarke_cm
    if is_gewoelbekeller is not None:
        payload["is_gewoelbekeller"] = is_gewoelbekeller
    if feuchtigkeit is not None:
        payload["feuchtigkeit"] = feuchtigkeit
    if dachboden_zukunft_wohnraum is not None:
        payload["dachboden_zukunft_wohnraum"] = dachboden_zukunft_wohnraum
    return payload


# ── Shared lead option definitions (re-used across commands) ──────────────────

_REGION = typer.Option(..., help="Lead region code")
_PRODUCT = typer.Option(..., help="Product type (fassade / ogd / kellerdecke)")
_SEGMENT = typer.Option(..., help="Customer segment")
_DURATION = typer.Option(..., help="Call duration in minutes")
_YEAR = typer.Option(..., help="Building year")
_HOHLRAUM = typer.Option(..., help="Has cavity wall (hohlraum)")
_HEATING = typer.Option(..., help="Heating system type")
_LEAD_ID = typer.Option(None, help="Optional lead identifier")


@app.command()
def issues(
    region: str = _REGION,
    product: str = _PRODUCT,
    customer_segment: str = _SEGMENT,
    call_duration_min: float = _DURATION,
    building_year: int = _YEAR,
    has_hohlraum: bool = _HOHLRAUM,
    heating_system: str = _HEATING,
    lead_id: Optional[str] = _LEAD_ID,
    host: str = typer.Option(_DEFAULT_HOST, envvar="TRIAGE_API_HOST", help="API base URL"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Predict issue flags for a lead."""
    payload = _lead_payload(
        region, product, customer_segment, call_duration_min,
        building_year, has_hohlraum, heating_system,
        lead_id, None, None, None, None, None, None, None, None, None,
    )
    result = _post(host, "/predict/issues", payload)
    if json_output:
        rprint(json.dumps(result, indent=2))
        return
    _print_issues(result)


@app.command()
def confidence(
    region: str = _REGION,
    product: str = _PRODUCT,
    customer_segment: str = _SEGMENT,
    call_duration_min: float = _DURATION,
    building_year: int = _YEAR,
    has_hohlraum: bool = _HOHLRAUM,
    heating_system: str = _HEATING,
    has_issues_prob: float = typer.Option(..., help="Issue probability from /predict/issues"),
    lead_id: Optional[str] = _LEAD_ID,
    host: str = typer.Option(_DEFAULT_HOST, envvar="TRIAGE_API_HOST", help="API base URL"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Predict confidence score (1–5) for a lead."""
    payload = _lead_payload(
        region, product, customer_segment, call_duration_min,
        building_year, has_hohlraum, heating_system,
        lead_id, has_issues_prob, None, None, None, None, None, None, None, None,
    )
    result = _post(host, "/predict/confidence", payload)
    if json_output:
        rprint(json.dumps(result, indent=2))
        return
    _print_confidence(result)


@app.command()
def triage(
    region: str = _REGION,
    product: str = _PRODUCT,
    customer_segment: str = _SEGMENT,
    call_duration_min: float = _DURATION,
    building_year: int = _YEAR,
    has_hohlraum: bool = _HOHLRAUM,
    heating_system: str = _HEATING,
    has_issues_prob: float = typer.Option(..., help="Issue probability from /predict/issues"),
    confidence_score_pred: float = typer.Option(..., help="Confidence score from /predict/confidence"),
    lead_id: Optional[str] = _LEAD_ID,
    transcript_text: Optional[str] = typer.Option(None, help="Call transcript"),
    n_vollgeschosse: Optional[float] = typer.Option(None, help="Number of full floors"),
    fassaden_typ: Optional[str] = typer.Option(None, help="Facade type string"),
    mauerstarke_cm: Optional[float] = typer.Option(None, help="Wall thickness in cm"),
    is_gewoelbekeller: Optional[bool] = typer.Option(None, help="Is vaulted cellar"),
    feuchtigkeit: Optional[bool] = typer.Option(None, help="Cellar moisture issues"),
    dachboden_zukunft_wohnraum: Optional[bool] = typer.Option(None, help="Attic planned as living space"),
    host: str = typer.Option(_DEFAULT_HOST, envvar="TRIAGE_API_HOST", help="API base URL"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Predict triage decision for a lead."""
    payload = _lead_payload(
        region, product, customer_segment, call_duration_min,
        building_year, has_hohlraum, heating_system,
        lead_id, has_issues_prob, confidence_score_pred, transcript_text,
        n_vollgeschosse, fassaden_typ, mauerstarke_cm,
        is_gewoelbekeller, feuchtigkeit, dachboden_zukunft_wohnraum,
    )
    result = _post(host, "/predict/triage", payload)
    if json_output:
        rprint(json.dumps(result, indent=2))
        return
    _print_triage(result)


@app.command()
def pipeline(
    region: str = _REGION,
    product: str = _PRODUCT,
    customer_segment: str = _SEGMENT,
    call_duration_min: float = _DURATION,
    building_year: int = _YEAR,
    has_hohlraum: bool = _HOHLRAUM,
    heating_system: str = _HEATING,
    lead_id: Optional[str] = _LEAD_ID,
    transcript_text: Optional[str] = typer.Option(None, help="Call transcript"),
    n_vollgeschosse: Optional[float] = typer.Option(None, help="Number of full floors"),
    fassaden_typ: Optional[str] = typer.Option(None, help="Facade type string"),
    mauerstarke_cm: Optional[float] = typer.Option(None, help="Wall thickness in cm"),
    is_gewoelbekeller: Optional[bool] = typer.Option(None, help="Is vaulted cellar"),
    feuchtigkeit: Optional[bool] = typer.Option(None, help="Cellar moisture issues"),
    dachboden_zukunft_wohnraum: Optional[bool] = typer.Option(None, help="Attic planned as living space"),
    host: str = typer.Option(_DEFAULT_HOST, envvar="TRIAGE_API_HOST", help="API base URL"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Run the full issues → confidence → triage pipeline in one call."""
    payload = _lead_payload(
        region, product, customer_segment, call_duration_min,
        building_year, has_hohlraum, heating_system,
        lead_id, None, None, transcript_text,
        n_vollgeschosse, fassaden_typ, mauerstarke_cm,
        is_gewoelbekeller, feuchtigkeit, dachboden_zukunft_wohnraum,
    )
    result = _post(host, "/predict/pipeline", payload)
    if json_output:
        rprint(json.dumps(result, indent=2))
        return
    rprint(Panel(f"[bold]Lead:[/bold] {result.get('lead_id', 'N/A')}", title="Pipeline Result"))
    _print_issues(result["issues"])
    _print_confidence(result["confidence"])
    _print_triage(result["triage"])


@app.command()
def briefing(
    transcript_file: Optional[Path] = typer.Option(None, "--transcript", "-t", help="Path to transcript.md"),
    intake_file: Optional[Path] = typer.Option(None, "--intake", "-i", help="Path to intake.json"),
    lead_dir: Optional[Path] = typer.Option(None, "--dir", "-d", help="Lead directory containing both files"),
    host: str = typer.Option(_DEFAULT_HOST, envvar="TRIAGE_API_HOST", help="API base URL"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Generate a field briefing from a transcript and intake data."""
    import os
    from pathlib import Path
    
    transcript_text = None
    intake_data = None
    
    if lead_dir:
        transcript_file = lead_dir / "transcript.md"
        intake_file = lead_dir / "intake.json"
        
    if not transcript_file or not transcript_file.exists():
        rprint("[red]Error: Transcript file not found.[/red]")
        raise typer.Exit(1)
        
    if not intake_file or not intake_file.exists():
        rprint("[red]Error: Intake file not found.[/red]")
        raise typer.Exit(1)
        
    with open(transcript_file, 'r') as f:
        transcript_text = f.read()
        
    with open(intake_file, 'r') as f:
        intake_data = json.load(f)
        
    payload = {
        "transcript_text": transcript_text,
        "intake_data": intake_data
    }
    
    result = _post(host, "/briefing/generate", payload)
    
    if json_output:
        rprint(json.dumps(result, indent=2))
        return
        
    rprint(Panel(result["briefing"], title=f"Field Briefing: {intake_data.get('lead_id', 'Unknown')}"))


@app.command()
def parse(
    transcript_file: Optional[Path] = typer.Option(None, "--transcript", "-t", help="Path to transcript.md"),
    intake_file: Optional[Path] = typer.Option(None, "--intake", "-i", help="Path to intake.json"),
    lead_dir: Optional[Path] = typer.Option(None, "--dir", "-d", help="Lead directory containing both files"),
    host: str = typer.Option(_DEFAULT_HOST, envvar="TRIAGE_API_HOST", help="API base URL"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Parse lead data using LLM to extract entities, contradictions, and risks."""
    transcript_text = None
    intake_data = None
    
    if lead_dir:
        transcript_file = lead_dir / "transcript.md"
        intake_file = lead_dir / "intake.json"
        
    if not transcript_file or not transcript_file.exists():
        rprint("[red]Error: Transcript file not found.[/red]")
        raise typer.Exit(1)
        
    if not intake_file or not intake_file.exists():
        rprint("[red]Error: Intake file not found.[/red]")
        raise typer.Exit(1)
        
    with open(transcript_file, 'r') as f:
        transcript_text = f.read()
        
    with open(intake_file, 'r') as f:
        intake_data = json.load(f)
        
    payload = {
        "transcript_text": transcript_text,
        "intake_data": intake_data
    }
    
    result = _post(host, "/llm-parser/parse", payload)
    
    if json_output:
        rprint(json.dumps(result, indent=2))
        return
        
    _print_parsed_lead(result, intake_data.get('lead_id', 'Unknown'))


@app.command()
def memory(
    transcript_file: Optional[Path] = typer.Option(None, "--transcript", "-t", help="Path to transcript.md"),
    intake_file: Optional[Path] = typer.Option(None, "--intake", "-i", help="Path to intake.json"),
    lead_dir: Optional[Path] = typer.Option(None, "--dir", "-d", help="Lead directory containing both files"),
    top_k: int = typer.Option(5, help="Number of similar projects to retrieve"),
    host: str = typer.Option(_DEFAULT_HOST, envvar="TRIAGE_API_HOST", help="API base URL"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Search for similar past projects using the Memory layer."""
    transcript_text = None
    intake_data = {}
    
    if lead_dir:
        transcript_file = lead_dir / "transcript.md"
        intake_file = lead_dir / "intake.json"
        
    if transcript_file and transcript_file.exists():
        with open(transcript_file, 'r') as f:
            transcript_text = f.read()
            
    if intake_file and intake_file.exists():
        with open(intake_file, 'r') as f:
            intake_data = json.load(f)
            
    payload = {
        "region": intake_data.get("region"),
        "product": intake_data.get("product"),
        "building_year": intake_data.get("building_year"),
        "fassaden_typ": intake_data.get("fassaden_typ"),
        "transcript_text": transcript_text,
        "top_k": top_k
    }
    
    result = _post(host, "/memory/search", payload)
    
    if json_output:
        rprint(json.dumps(result, indent=2))
        return
        
    _print_memory_result(result)


@app.command()
def decision(
    transcript_file: Optional[Path] = typer.Option(None, "--transcript", "-t", help="Path to transcript.md"),
    intake_file: Optional[Path] = typer.Option(None, "--intake", "-i", help="Path to intake.json"),
    lead_dir: Optional[Path] = typer.Option(None, "--dir", "-d", help="Lead directory containing both files"),
    host: str = typer.Option(_DEFAULT_HOST, envvar="TRIAGE_API_HOST", help="API base URL"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
):
    """Run the full Decision Engine on a lead (Rules + LLM + Memory)."""
    transcript_text = None
    intake_data = None
    
    if lead_dir:
        transcript_file = lead_dir / "transcript.md"
        intake_file = lead_dir / "intake.json"
        
    if not transcript_file or not transcript_file.exists():
        rprint("[red]Error: Transcript file not found.[/red]")
        raise typer.Exit(1)
        
    if not intake_file or not intake_file.exists():
        rprint("[red]Error: Intake file not found.[/red]")
        raise typer.Exit(1)
        
    with open(transcript_file, 'r') as f:
        transcript_text = f.read()
        
    with open(intake_file, 'r') as f:
        intake_data = json.load(f)
        
    payload = {
        "transcript_text": transcript_text,
        "intake_data": intake_data
    }
    
    result = _post(host, "/decision/evaluate", payload)
    
    if json_output:
        rprint(json.dumps(result, indent=2))
        return
        
    _print_decision_result(result, intake_data.get('lead_id', 'Unknown'))


def _print_decision_result(r: dict, lead_id: str) -> None:
    decision = r["decision"]
    conf = r["confidence_score"]
    color = {
        "pitch": "green",
        "pitch_with_flag": "yellow",
        "pitch_with_cross_sell": "blue",
        "disqualify": "red",
        "escalate": "magenta",
    }.get(decision, "white")
    
    rprint(Panel(
        f"[bold {color}]{decision.upper()}[/bold {color}]\n"
        f"[bold]Confidence Score:[/bold] {conf:.2f}",
        title=f"Decision Engine: {lead_id}"
    ))
    
    # Reasoning
    if r.get("reasoning"):
        rprint("[bold]Reasoning:[/bold]")
        for reason in r["reasoning"]:
            rprint(f"  • {reason}")
            
    # Rules
    rprint(f"\n[bold]Rule Engine Status:[/bold] {r['rule_status']}")
    if r.get("rule_reasons"):
        for reason in r["rule_reasons"]:
            rprint(f"    - {reason}")
            
    # LLM & Memory summary
    stats = r.get("memory_stats", {})
    rprint(Panel(
        f"[bold]Historical Success Rate:[/bold] {stats.get('close_rate', 0):.1%}\n"
        f"[bold]Contradictions found:[/bold] {len(r.get('llm_analysis', {}).get('contradictions', []))}",
        title="Supporting Evidence",
        style="dim"
    ))


def _print_memory_result(r: dict) -> None:
    # Stats
    stats = r.get("stats", {})
    rprint(Panel(
        f"[bold]Similar Projects Found:[/bold] {stats.get('total_similar')}\n"
        f"[bold]Close Rate:[/bold] {stats.get('close_rate'):.1%}\n"
        f"[bold]Avg Overrun:[/bold] {stats.get('avg_overrun_eur'):,.2f} EUR\n"
        f"[bold]Common Issues:[/bold] {', '.join(stats.get('common_issues', [])) or 'None'}",
        title="Memory Layer Insights",
        style="blue"
    ))
    
    # Similar Projects Table
    projects = r.get("similar_projects", [])
    if projects:
        t = Table(title="Top Similar Past Projects", show_header=True)
        t.add_column("Project ID", style="cyan")
        t.add_column("Region")
        t.add_column("Product")
        t.add_column("Stage", justify="center")
        t.add_column("Satisfaction", justify="center")
        for p in projects:
            stage = p["stage"]
            color = "green" if stage in ["signed_installed", "completed"] else "red" if "disqualified" in stage else "yellow"
            sat = str(p.get("customer_satisfaction") or "-")
            t.add_row(
                p["project_id"],
                p["region"],
                p["product"],
                f"[{color}]{stage}[/{color}]",
                sat
            )
        rprint(t)
    else:
        rprint("[yellow]No similar projects found.[/yellow]")


def _print_parsed_lead(r: dict, lead_id: str) -> None:
    rprint(Panel(f"[bold]Lead ID:[/bold] {lead_id}", title="LLM Parser Result"))
    
    # Entities
    e = r.get("entities", {})
    t_e = Table(title="Extracted Entities", show_header=True)
    t_e.add_column("Entity", style="cyan")
    t_e.add_column("Value")
    for k, v in e.items():
        t_e.add_row(k.replace("_", " ").title(), str(v) if v else "[dim]N/A[/dim]")
    rprint(t_e)
    
    # Contradictions
    c = r.get("contradictions", [])
    if c:
        t_c = Table(title="Contradictions vs Intake", show_header=True)
        t_c.add_column("Field", style="yellow")
        t_c.add_column("Transcript")
        t_c.add_column("Intake")
        t_c.add_column("Reason")
        for item in c:
            t_c.add_row(item["field"], item["transcript_value"], item["intake_value"], item["reason"])
        rprint(t_c)
    else:
        rprint("[green]No contradictions found.[/green]")
        
    # Risks
    risks = r.get("risk_factors", [])
    if risks:
        t_r = Table(title="Risk Assessment", show_header=True)
        t_r.add_column("Tag", style="magenta")
        t_r.add_column("Description")
        t_r.add_column("Severity", justify="center")
        for risk in risks:
            sev = risk["severity"].upper()
            color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(sev, "white")
            t_r.add_row(risk["tag"], risk["description"], f"[{color}]{sev}[/{color}]")
        rprint(t_r)
    else:
        rprint("[green]No risk factors identified.[/green]")


def _print_issues(r: dict) -> None:
    t = Table(title="Issue Predictions", show_header=True)
    t.add_column("Flag", style="cyan")
    t.add_column("Prediction")
    t.add_column("Probability", justify="right")
    t.add_row("has_issues", str(r["has_issues_pred"]), f"{r['has_issues_prob']:.3f}")
    t.add_row("has_scope_issue", str(r["has_scope_issue_pred"]), f"{r['has_scope_issue_prob']:.3f}")
    t.add_row("has_time_issue", str(r["has_time_issue_pred"]), f"{r['has_time_issue_prob']:.3f}")
    rprint(t)
    _print_top_features(r.get("meta", {}))


def _print_confidence(r: dict) -> None:
    score = r["confidence_score_pred"]
    t = Table(title=f"Confidence Score: {score}", show_header=True)
    t.add_column("Score", style="cyan")
    t.add_column("Probability", justify="right")
    for k, v in sorted(r.get("confidence_score_probs", {}).items()):
        t.add_row(k, f"{v:.3f}")
    rprint(t)
    _print_top_features(r.get("meta", {}))


def _print_triage(r: dict) -> None:
    decision = r["triage_decision"]
    color = {
        "pitch": "green",
        "pitch_with_flag": "yellow",
        "pitch_with_cross_sell": "blue",
        "disqualify": "red",
        "escalate": "magenta",
    }.get(decision, "white")
    rprint(Panel(f"[bold {color}]{decision.upper()}[/bold {color}]", title="Triage Decision"))
    t = Table(title="Class Probabilities", show_header=True)
    t.add_column("Class", style="cyan")
    t.add_column("Probability", justify="right")
    for k, v in sorted(r.get("probabilities", {}).items(), key=lambda x: -x[1]):
        t.add_row(k, f"{v:.3f}")
    rprint(t)
    meta = r.get("meta", {})
    rprint(f"  [dim]Source:[/dim] {meta.get('source', 'N/A')}")
    if "reason" in meta:
        rprint(f"  [dim]Reason:[/dim] {meta['reason']}")
    _print_top_features(meta)


def _print_top_features(meta: dict) -> None:
    features = meta.get("top_impact_features", [])
    if not features:
        return
    t = Table(title="Top Impact Features", show_header=True)
    t.add_column("Feature", style="cyan")
    t.add_column("SHAP Impact", justify="right")
    for f in features:
        impact = f["impact"]
        color = "green" if impact > 0 else "red"
        t.add_row(f["feature"], f"[{color}]{impact:+.4f}[/{color}]")
    rprint(t)


if __name__ == "__main__":
    app()
