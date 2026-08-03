    def _render_html(self, data: Dict[str, Any]) -> str:
        """
        Render the report HTML using Jinja2 templates located in the project's templates directory.

        Args:
            data: payload dictionary as returned by _collect_report_data

        Returns:
            Rendered HTML string ready for PDF generation.

        Raises:
            RuntimeError: if template rendering fails.
        """
        try:
            from pathlib import Path
            from jinja2 import Environment, FileSystemLoader, select_autoescape

            # Determine templates directory (backend/app/templates)
            template_dir = Path(__file__).resolve().parent.parent / "templates"
            env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )
            template = env.get_template("report.html.jinja")

            # Provide a generation timestamp if not supplied
            from datetime import datetime
            context = {"generation_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "data_date": None}

            # Merge the collected data payload into the context
            # The template expects top-level keys: patient, study, image, analysis, media, stage_prediction, risk_analysis, existing_report
            context.update(data)

            html = template.render(**context)
            return html
        except Exception as exc:
            logger.exception("Failed to render report HTML for analysis: %s", data.get("analysis", {}).get("id"))
            raise RuntimeError(f"Report rendering failed: {exc}")
