import unittest
from unittest.mock import Mock

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery

from kernel import BigQuerySQLKernel


class FakeResult:
    schema = [bigquery.SchemaField("answer", "INT64")]
    total_rows = 1

    def __iter__(self):
        yield (42,)


class FakeJob:
    total_bytes_processed = 8

    def result(self):
        return FakeResult()


class FakeClient:
    def query(self, sql):
        if sql != "SELECT 42":
            raise AssertionError(f"Unexpected SQL: {sql}")
        return FakeJob()


class BigQuerySQLKernelTests(unittest.TestCase):
    def test_executes_sql_and_renders_results_without_cloud_access(self):
        kernel = BigQuerySQLKernel()
        kernel._client = FakeClient()
        kernel.iopub_socket = object()
        kernel.send_response = Mock()

        reply = kernel.do_execute("SELECT 42", silent=False)

        self.assertEqual(reply["status"], "ok")
        message = kernel.send_response.call_args.args[2]
        self.assertIn("42", message["data"]["text/html"])
        self.assertIn("8 bytes", message["data"]["text/plain"])

    def test_surfaces_missing_credentials_as_execution_error(self):
        class NoCredentialsClient:
            def query(self, sql):
                raise DefaultCredentialsError("No credentials available")

        kernel = BigQuerySQLKernel()
        kernel._client = NoCredentialsClient()
        kernel.iopub_socket = object()
        kernel.send_response = Mock()

        reply = kernel.do_execute("SELECT 42", silent=False)

        self.assertEqual(reply["status"], "error")
        self.assertEqual(reply["ename"], "DefaultCredentialsError")
        self.assertEqual(kernel.send_response.call_args.args[1], "error")


if __name__ == "__main__":
    unittest.main()
