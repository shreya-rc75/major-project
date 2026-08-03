    def _generate_pdf(self, html: str) -> bytes:
        """
        Convert rendered HTML into a PDF document using WeasyPrint.

        This method does not write the PDF to disk; it returns the PDF file as bytes.

        Args:
            html: Fully rendered HTML string produced by _render_html.

        Returns:
            PDF file content as bytes.

        Raises:
            ValueError: If the provided HTML is empty or not a string.
            RuntimeError: If PDF generation fails for any reason. The original
                          exception will be logged for debugging.
        """
        logger.info("Starting PDF generation for analysis report")
        # Validate input
        if not isinstance(html, str):
            logger.error("HTML content must be a string. Got %s", type(html))
            raise ValueError("HTML content must be a string")
        if not html.strip():
            logger.error("Empty HTML content provided for PDF generation")
            raise ValueError("Empty HTML content provided")

        try:
            from time import perf_counter
            from pathlib import Path
            # WeasyPrint imports
            from weasyprint import HTML

            start = perf_counter()

            # Base URL should point to the templates directory so relative resources resolve
            template_dir = Path(__file__).resolve().parent.parent / "templates"
            base_url = str(template_dir)

            # Create PDF in memory
            html_doc = HTML(string=html, base_url=base_url)
            pdf_bytes = html_doc.write_pdf(stylesheets=None)

            duration = perf_counter() - start
            size = len(pdf_bytes) if pdf_bytes is not None else 0
            logger.info("PDF generation completed in %.2fs; size=%d bytes", duration, size)

            if not pdf_bytes:
                logger.error("WeasyPrint returned empty PDF bytes")
                raise RuntimeError("PDF generation produced empty output")

            return pdf_bytes
        except Exception as exc:
            logger.exception("PDF generation failed: %s", exc)
            raise RuntimeError(f"Failed to generate PDF: {exc}")
