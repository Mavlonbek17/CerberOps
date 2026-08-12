"""CerberOps CLI — command-line interface for security scanning."""

import time

import httpx
import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    name="cerberops",
    help="CerberOps — DevSecOps Vulnerability Orchestrator CLI",
    no_args_is_help=True,
)
console = Console()

DEFAULT_API = "http://localhost:8000"


def _api_url() -> str:
    import os
    return os.environ.get("CERBEROPS_API_URL", DEFAULT_API)


def _headers() -> dict[str, str]:
    import os
    key = os.environ.get("CERBEROPS_API_KEY", "")
    if key:
        return {"X-API-Key": key}
    return {}


@app.command()
def scan(
    target: str = typer.Argument(..., help="Target URL or IP address to scan"),
    scanners: str = typer.Option(
        "nmap,nuclei,zap", "--scanners", "-s",
        help="Comma-separated scanners to use",
    ),
    allow_internal: bool = typer.Option(
        False, "--allow-internal",
        help="Allow scanning internal/private addresses",
    ),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Wait for completion"),
    api_url: str = typer.Option(None, "--api", help="CerberOps API URL"),
) -> None:
    """Start a new vulnerability scan."""
    base = api_url or _api_url()
    scanner_list = [s.strip() for s in scanners.split(",")]

    rprint(f"\n[bold blue]CerberOps[/] — Scanning [bold]{target}[/]")
    rprint(f"  Scanners: {', '.join(scanner_list)}")
    rprint(f"  API: {base}\n")

    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                f"{base}/api/v1/scan",
                json={
                    "target": target,
                    "scanners": scanner_list,
                    "allow_internal": allow_internal,
                },
                headers=_headers(),
            )
    except httpx.ConnectError as exc:
        rprint("[red]Error:[/] Cannot connect to CerberOps API. Is the server running?")
        rprint("  Try: [dim]docker compose up -d[/] or [dim]uvicorn app.main:app[/]")
        raise typer.Exit(1) from exc

    if r.status_code != 202:
        rprint(f"[red]Error ({r.status_code}):[/] {r.json().get('detail', r.text)}")
        raise typer.Exit(1)

    data = r.json()
    job_id = data["job_id"]
    rprint(f"[green]Scan queued![/] Job ID: [bold]{job_id}[/]\n")

    if not wait:
        rprint(f"Track progress: [dim]cerberops status {job_id}[/]")
        return

    # Poll for completion
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Waiting for scan to complete...", total=None)

        while True:
            time.sleep(3)
            try:
                with httpx.Client(timeout=10.0) as client:
                    sr = client.get(f"{base}/api/v1/scan/{job_id}", headers=_headers())
                    if sr.status_code != 200:
                        continue
                    scan_data = sr.json()
            except httpx.ConnectError:
                continue

            status = scan_data["status"]
            pct = scan_data.get("progress", 0)
            progress.update(task, description=f"[{status}] {pct}% complete")

            if status in ("completed", "failed", "cancelled"):
                break

    rprint()
    if status == "completed":
        _print_results(scan_data)
    elif status == "failed":
        rprint(f"[red]Scan failed:[/] {scan_data.get('error_message', 'Unknown error')}")
        raise typer.Exit(1)
    else:
        rprint(f"[yellow]Scan {status}[/]")


@app.command()
def status(
    job_id: str = typer.Argument(..., help="Scan job ID"),
    api_url: str = typer.Option(None, "--api", help="CerberOps API URL"),
) -> None:
    """Check the status of a scan."""
    base = api_url or _api_url()

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{base}/api/v1/scan/{job_id}", headers=_headers())
    except httpx.ConnectError as exc:
        rprint("[red]Error:[/] Cannot connect to CerberOps API.")
        raise typer.Exit(1) from exc

    if r.status_code == 404:
        rprint(f"[red]Scan {job_id} not found[/]")
        raise typer.Exit(1)

    _print_results(r.json())


@app.command()
def report(
    job_id: str = typer.Argument(..., help="Scan job ID"),
    regenerate: bool = typer.Option(False, "--regenerate", help="Force AI report regeneration"),
    api_url: str = typer.Option(None, "--api", help="CerberOps API URL"),
) -> None:
    """View the AI-generated remediation report."""
    base = api_url or _api_url()

    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.get(
                f"{base}/api/v1/report/{job_id}",
                params={"regenerate": regenerate},
                headers=_headers(),
            )
    except httpx.ConnectError as exc:
        rprint("[red]Error:[/] Cannot connect to CerberOps API.")
        raise typer.Exit(1) from exc

    if r.status_code != 200:
        rprint(f"[red]Error ({r.status_code}):[/] {r.json().get('detail', r.text)}")
        raise typer.Exit(1)

    data = r.json()

    rprint(Panel(
        f"[bold]AI Remediation Report[/]\n"
        f"Model: {data.get('ai_model_used', 'N/A')}\n"
        f"Generated: {data.get('generated_at', 'N/A')}",
        title="CerberOps Report",
        border_style="blue",
    ))

    rprint("\n[bold underline]Executive Summary[/]")
    rprint(data.get("executive_summary", "N/A"))

    rprint("\n[bold underline]Technical Details[/]")
    rprint(data.get("technical_details", "N/A"))

    rprint("\n[bold underline]Remediation Plan[/]")
    rprint(data.get("remediation_plan", "N/A"))


@app.command(name="list")
def list_scans(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of scans to show"),
    api_url: str = typer.Option(None, "--api", help="CerberOps API URL"),
) -> None:
    """List recent scans."""
    base = api_url or _api_url()

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(
                f"{base}/api/v1/scan",
                params={"limit": limit},
                headers=_headers(),
            )
    except httpx.ConnectError as exc:
        rprint("[red]Error:[/] Cannot connect to CerberOps API.")
        raise typer.Exit(1) from exc

    scans = r.json()
    if not scans:
        rprint("[dim]No scans found.[/]")
        return

    table = Table(title="Recent Scans")
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Target")
    table.add_column("Status")
    table.add_column("Findings")
    table.add_column("Created")

    for s in scans:
        status_style = {
            "completed": "green",
            "running": "blue",
            "queued": "yellow",
            "failed": "red",
            "cancelled": "dim",
        }.get(s["status"], "white")

        table.add_row(
            s["id"][:12],
            s["target"][:40],
            f"[{status_style}]{s['status']}[/]",
            str(s.get("findings_count", 0)),
            s["created_at"][:19],
        )

    console.print(table)


@app.command()
def health(
    api_url: str = typer.Option(None, "--api", help="CerberOps API URL"),
) -> None:
    """Check CerberOps system health."""
    base = api_url or _api_url()

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{base}/api/v1/health")
    except httpx.ConnectError as exc:
        rprint("[red]CerberOps API is not reachable[/]")
        raise typer.Exit(1) from exc

    data = r.json()

    rprint(Panel(
        f"Version: {data.get('version', '?')}\n"
        f"Status:  [green]{data.get('status', '?')}[/]",
        title="CerberOps Health",
        border_style="blue",
    ))

    table = Table(title="Component Status")
    table.add_column("Component")
    table.add_column("Status")

    for scanner, available in data.get("scanners", {}).items():
        icon = "[green]available[/]" if available else "[red]missing[/]"
        table.add_row(f"Scanner: {scanner}", icon)

    table.add_row(
        "Ollama (AI)",
        "[green]connected[/]" if data.get("ollama_available") else "[yellow]not connected[/]",
    )
    table.add_row(
        "Database",
        "[green]connected[/]" if data.get("database") else "[red]not connected[/]",
    )

    console.print(table)


def _print_results(scan_data: dict) -> None:
    """Pretty-print scan results."""
    rprint(Panel(
        f"Target: [bold]{scan_data['target']}[/]\n"
        f"Status: {scan_data['status']}\n"
        f"Scanners: {', '.join(scan_data.get('scanners', []))}\n"
        f"Findings: {scan_data.get('findings_count', 0)}",
        title=f"Scan {scan_data['id'][:12]}",
        border_style="green" if scan_data["status"] == "completed" else "yellow",
    ))

    findings = scan_data.get("findings", [])
    if not findings:
        rprint("[dim]No findings.[/]")
        return

    severity_colors = {
        "critical": "red bold",
        "high": "red",
        "medium": "yellow",
        "low": "cyan",
        "info": "dim",
    }

    table = Table(title="Findings")
    table.add_column("Severity", width=10)
    table.add_column("Title")
    table.add_column("Host")
    table.add_column("Scanner")

    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    for f in sorted(
        findings, key=lambda x: sev_order.get(x.get("severity", "info"), 5)
    ):
        sev = f.get("severity", "info")
        style = severity_colors.get(sev, "white")
        host = f.get("host", "")
        if f.get("port"):
            host += f":{f['port']}"

        table.add_row(
            f"[{style}]{sev.upper()}[/]",
            f["title"][:60],
            host[:30],
            f.get("scanner_source", "")[:20],
        )

    console.print(table)

    # Summary
    counts = scan_data.get("severity_counts", {})
    if counts:
        parts = []
        for sev in ("critical", "high", "medium", "low", "info"):
            c = counts.get(sev, 0)
            if c:
                style = severity_colors.get(sev, "white")
                parts.append(f"[{style}]{c} {sev.upper()}[/]")
        rprint(f"\nSummary: {' | '.join(parts)}")


if __name__ == "__main__":
    app()
