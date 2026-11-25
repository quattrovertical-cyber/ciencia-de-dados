# BigQuery SQL Jupyter kernel

The `BigQuery SQL (Google Cloud)` kernel executes SQL cells through the
BigQuery Python client and Google Application Default Credentials. It is
separate from the BigQuery Studio VS Code extension.

When BigQuery Studio is authenticated with **User Login**, its gcloud login
updates Application Default Credentials and the default gcloud project. This
kernel uses those credentials and that project. Restart the kernel after
changing the extension account or default project.

Select this kernel in the notebook's kernel picker. The kernel displays query
results as a table and limits displayed rows to the first 100; this does not
limit bytes processed or BigQuery charges.

If Google credentials expire or are unavailable, authenticate with:

```powershell
gcloud auth application-default login
```

Queries run as BigQuery jobs and may incur charges.
