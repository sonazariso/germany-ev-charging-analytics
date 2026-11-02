# GitHub publication checklist

This checklist prepares a future publication review. Nothing in Batch 04 publishes or synchronizes the project.

## Documentation and analytical review

- [ ] README and all English documentation reviewed for accuracy and clarity.
- [ ] Reproducibility commands run from a clean checkout.
- [ ] All headline metrics reconcile to a named report or read-only query.
- [ ] KPI denominators, grains, and source dates reviewed.
- [ ] Provisional geographic mappings clearly marked.
- [ ] BBSR is described accurately as a separate reference only; no unapproved KBA enrichment or KPI is presented as complete.
- [ ] Dashboard and screenshot review completed.

## Security and repository hygiene

- [ ] No secrets, credentials, tokens, cookies, or private keys are present.
- [ ] No personal filesystem paths appear in tracked documentation or generated reports.
- [ ] No raw XLSX workbooks are staged.
- [ ] No DuckDB database, WAL, temporary database, virtual environment, or compiled binary is staged.
- [ ] No uncontrolled CSV exports or large query dumps are staged.
- [ ] No local machine-specific settings are staged.
- [ ] .gitignore behavior verified with git check-ignore and staged-path review.

## Source and licensing review

- [ ] BNetzA CC BY 4.0 attribution is present where required.
- [ ] KBA Datenlizenz Deutschland – Namensnennung 2.0 attribution is present where required.
- [ ] Code license and source-data licenses are kept distinct.
- [ ] Source-derived extracts, identifiers, coordinates, screenshots, and Tableau publication rights are reviewed.
- [ ] BBSR Datenlizenz Deutschland – Namensnennung – Version 2.0 attribution and change notice are retained for the tracked derived reference.
- [ ] Any future BBSR/KBA enrichment or Tableau publication license is reviewed before use.

## Code and dependency review

- [ ] Python scripts run without undocumented dependencies.
- [ ] requirements-phase03.txt matches the supported DuckDB environment.
- [ ] Read-only validation and database-lock behavior are documented.
- [ ] Source-aware joins and multi-snapshot behavior are reviewed.
- [ ] No memory, thread, or disk limits were introduced without approval.
- [ ] No destructive database operation is triggered by a standard analysis command.

## History and publication approval

- [ ] Local Git history reviewed for sensitive or unexpected files.
- [ ] Git status and staged paths are clean and intentional.
- [ ] No remote was added by an automated or local workflow.
- [ ] Final user approval obtained before creating a remote, pushing, uploading, or publishing.
