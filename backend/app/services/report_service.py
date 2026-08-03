    def _store_report(self, analysis_id: int, pdf_bytes: bytes) -> str:
        """
        Store generated PDF bytes to persistent storage using LocalFileStorage.

        The PDF will be stored under the "reports/" directory using a collision-safe
        filename that includes the analysis_id, a timestamp and a short UUID suffix.

        Args:
            analysis_id: Identifier of the analysis the report belongs to.
            pdf_bytes: PDF file content as bytes (non-empty).

        Returns:
            Relative storage path where the PDF was saved (e.g. "reports/report_123_20260803_104530_f3b2.pdf").

        Raises:
            RuntimeError: If validation fails or storage operation fails.
        """
        logger.info("Storing report PDF for analysis_id=%s", analysis_id)

        # Validate inputs
        if not isinstance(analysis_id, int) or analysis_id <= 0:
            logger.error("Invalid analysis_id provided for report storage: %s", analysis_id)
            raise RuntimeError("Invalid analysis_id provided for report storage")
        if not isinstance(pdf_bytes, (bytes, bytearray)) or len(pdf_bytes) == 0:
            logger.error("Empty PDF bytes provided for analysis_id=%s", analysis_id)
            raise RuntimeError("Empty PDF bytes provided for storage")

        try:
            from time import perf_counter
            from datetime import datetime
            from uuid import uuid4

            start = perf_counter()

            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            suffix = uuid4().hex[:6]
            filename = f"report_{analysis_id}_{ts}_{suffix}.pdf"

            # Use LocalFileStorage to save the file under 'reports' subpath
            # The LocalFileStorage.save_file API used elsewhere returns (relative_path, size)
            rel_path, size = self.storage.save_file(pdf_bytes, filename=filename, subpath="reports")

            duration = perf_counter() - start
            logger.info("Stored report for analysis_id=%s to %s (size=%d bytes) in %.2fs", analysis_id, rel_path, size, duration)

            return rel_path
        except Exception as exc:
            logger.exception("Failed to store report for analysis_id=%s: %s", analysis_id, exc)
            raise RuntimeError(f"Failed to store report for analysis {analysis_id}: {exc}")
