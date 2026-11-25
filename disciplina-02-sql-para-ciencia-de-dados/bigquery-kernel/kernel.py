from __future__ import annotations

import html
import json
from itertools import islice
from typing import Any

from google.api_core.exceptions import GoogleAPICallError
from google.auth.exceptions import DefaultCredentialsError, RefreshError
from google.cloud import bigquery
from ipykernel.kernelapp import IPKernelApp
from ipykernel.kernelbase import Kernel


class BigQuerySQLKernel(Kernel):
    implementation = "BigQuery SQL"
    implementation_version = "1.0"
    language = "sql"
    language_info = {
        "name": "sql",
        "mimetype": "text/x-sql",
        "file_extension": ".sql",
        "codemirror_mode": "sql",
    }
    banner = "BigQuery SQL kernel"
    display_limit = 100

    _client: bigquery.Client | None = None

    def do_execute(
        self,
        code: str,
        silent: bool,
        store_history: bool = True,
        user_expressions: dict[str, Any] | None = None,
        allow_stdin: bool = False,
        *,
        cell_meta: dict[str, Any] | None = None,
        cell_id: str | None = None,
    ) -> dict[str, Any]:
        del store_history, user_expressions, allow_stdin, cell_meta, cell_id
        if not code.strip():
            return {"status": "ok", "execution_count": self.execution_count}

        try:
            if self._client is None:
                self._client = bigquery.Client()
            job = self._client.query(code)
            result = job.result()
            columns = [field.name for field in result.schema]
            rows = list(islice(result, self.display_limit + 1))
            truncated = len(rows) > self.display_limit
            rows = rows[: self.display_limit]

            if not silent:
                self.send_response(
                    self.iopub_socket,
                    "display_data",
                    {
                        "data": self._result_data(
                            job,
                            columns,
                            rows,
                            result.total_rows,
                            truncated,
                        ),
                        "metadata": {},
                    },
                )
            return {"status": "ok", "execution_count": self.execution_count}
        except (
            DefaultCredentialsError,
            RefreshError,
            GoogleAPICallError,
        ) as error:
            error_name = type(error).__name__
            error_value = str(error)
            traceback = [f"{error_name}: {error_value}"]
            if not silent:
                self.send_response(
                    self.iopub_socket,
                    "error",
                    {
                        "ename": error_name,
                        "evalue": error_value,
                        "traceback": traceback,
                    },
                )
            return {
                "status": "error",
                "execution_count": self.execution_count,
                "ename": error_name,
                "evalue": error_value,
                "traceback": traceback,
            }

    def _result_data(
        self,
        job: bigquery.QueryJob,
        columns: list[str],
        rows: list[bigquery.Row],
        total_rows: int | None,
        truncated: bool,
    ) -> dict[str, str]:
        row_count = total_rows if total_rows is not None else len(rows)
        bytes_processed = job.total_bytes_processed
        bytes_label = (
            f"{bytes_processed:,} bytes"
            if bytes_processed is not None
            else "not reported"
        )
        summary = f"{row_count:,} row(s); {bytes_label} processed."
        if truncated:
            summary += f" Showing the first {self.display_limit} rows."

        if not columns:
            return {"text/plain": summary}

        header_html = "".join(f"<th>{html.escape(column)}</th>" for column in columns)
        row_html = "".join(
            "<tr>"
            + "".join(
                f"<td>{html.escape(self._format_value(row[index]))}</td>"
                for index in range(len(columns))
            )
            + "</tr>"
            for row in rows
        )
        table_html = (
            f"<p>{html.escape(summary)}</p>"
            f"<table><thead><tr>{header_html}</tr></thead>"
            f"<tbody>{row_html}</tbody></table>"
        )
        return {"text/html": table_html, "text/plain": summary}

    @staticmethod
    def _format_value(value: Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False, default=str)
        return str(value)


if __name__ == "__main__":
    IPKernelApp.launch_instance(kernel_class=BigQuerySQLKernel)
