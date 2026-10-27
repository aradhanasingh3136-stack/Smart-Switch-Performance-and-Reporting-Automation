# GitHub publication and presentation

Published repository: [Smart Switch Performance and Reporting Automation](https://github.com/aradhanasingh3136-stack/Smart-Switch-Performance-and-Reporting-Automation).

The repository is public. Project commits are attributed to **Aradhana Singh** (`aradhanasingh3136-stack`).

Owner: **aradhanasingh3136-stack**<br>
Repository name: **Smart-Switch-Performance-and-Reporting-Automation**<br>
Suggested description: **Smart home switch performance analytics and reporting automation with SQL, Python, Power BI and Excel VBA. Includes reproducible synthetic IoT data and validation checks.**

The direct resume URL is:

```text
https://github.com/aradhanasingh3136-stack/Smart-Switch-Performance-and-Reporting-Automation
```

An account/profile URL is not authentication. Creating the repository and uploading require signing in through GitHub, an authenticated CLI, or a connected GitHub integration. Never paste access tokens or passwords into project files or chat.

## GitHub Desktop publication workflow

1. Extract the project package and locate the folder containing `README.md` and `run.py`.
2. Sign in to GitHub Desktop using your GitHub account.
3. Use File → Add local repository. Choose this project folder. If it is not yet a Git repository, follow the option to create a repository there.
4. Confirm the local repository root contains `README.md`, not another unnecessary outer wrapper folder.
5. Review changed files. `.gitignore` excludes the large generated facts, warehouse, local logs, macro-enabled working copy and Power BI caches.
6. In Desktop settings, use your GitHub identity for Git. Name: **Aradhana Singh**. For email, choose your verified GitHub email or the exact GitHub-provided private commit email shown under GitHub Settings → Emails. Do not guess that email address.
7. Make the first commit: `Build SmartSwitch analytics and reporting project`.
8. Choose Publish repository. Use `Smart-Switch-Performance-and-Reporting-Automation` and the description above. Make the portfolio public if you want recruiters to view it without signing in.
9. Open the repository online and perform the checks below.

## Command-line alternative

Create a new empty repository under your account at GitHub. For this route, avoid initializing a separate README, license or `.gitignore` online because those files already exist locally.

In the project folder:

```bash
git init -b main
git config user.name "Aradhana Singh"
git config user.email "YOUR_EXACT_VERIFIED_OR_GITHUB_PRIVATE_EMAIL"
git add .
git status --short
git commit -m "Build SmartSwitch analytics and reporting project"
git remote add origin https://github.com/aradhanasingh3136-stack/Smart-Switch-Performance-and-Reporting-Automation.git
git push -u origin main
```

Replace the email placeholder before running the command. Use GitHub's supported sign-in flow when authentication is requested. A GitHub account password is not a substitute for supported Git authentication.

If an unrelated repository already exists at this name, choose a new name and update documentation links rather than overwriting its history. No existing repositories or profile contents need to be deleted for this project.

On the preparation Mac, `/usr/bin/git` displayed an Xcode license prompt. If that still happens, review the license yourself before using Apple's Git, or use a functioning Git installation through GitHub Desktop.

## Browser upload alternative

Use GitHub's Add file → Upload files workflow in a new repository. Upload the **contents** of the `smartswitch-analytics` folder, preserving directories. Do not upload the ZIP as the only repository file. Browser uploads do not apply `.gitignore` for you; exclude the generated paths listed there. GitHub Desktop or Git handles this structure more reliably.

## Make the repository attractive

1. Keep the supplied README as the front page. It begins with the project purpose, a dashboard preview, concrete results and runnable instructions.
2. Add About topics: `iot`, `home-automation`, `data-analytics`, `python`, `sql`, `sqlite`, `power-bi`, `excel-vba`, `reporting-automation`, `portfolio-project`.
3. Add a social preview image using `reports/dashboard.png` if you want a consistent preview when sharing the link.
4. Pin this repository from your GitHub profile's Customize your pins interface.
5. Check the Actions tab after the first push. Only describe the cloud checks as passed after the actual workflow run succeeds.
6. After native application checks, add real Power BI screenshots in `reports/powerbi/` and link them in the README. Keep the Python dashboard labelled correctly.
7. Consider a v1.0 release after the project can be cloned and run from a clean folder. Attach the complete portable ZIP there if you want reviewers to download the pre-generated data and workbook.

This repository needs no animated badges or exaggerated claims to stand out. A visible report, clear code, reproducible results and concise explanations let a reviewer assess it quickly.

## Verify before adding the resume link

- Open the repository in a signed-out or private window.
- Confirm the README image and all relative documentation links work.
- Check that the latest commit shows your account as the author. GitHub links a Git commit to an account through its verified author email.
- Confirm the license, workbook, VBA source, SQL files and Power BI project are visible.
- Download a fresh source ZIP and run the three quick-start commands.
- Review the Actions result. Do not infer a successful hosted run from local tests alone.
- Copy the direct repository URL into the resume and test the hyperlink from the exported resume PDF.

## Optional profile introduction

If you maintain a profile README, a concise project entry could be:

> I build analytics projects with SQL, Python, Power BI and Excel. My SmartSwitch Analytics project examines synthetic home automation data with reproducible ETL, reliability metrics and reporting automation.

Use the published repository link above. A complete profile refresh is a separate edit to the repository named exactly after your username.

The workflow follows [GitHub's guide to importing local code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
