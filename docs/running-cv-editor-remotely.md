# Running the CV Editor on a Remote Linux Machine

The Windows launcher, `CV_편집기_실행.cmd`, is not needed on Linux. Run the Python editor on the remote machine and access it from your local browser through an SSH tunnel.

The editor listens only on `127.0.0.1`, so it is not exposed directly to the internet.

## Requirements

- SSH access to the remote Linux machine
- Python 3.12 or later on the remote machine
- Google Chrome, Chromium, or Microsoft Edge on the remote machine for PDF generation
- A local web browser

## Start the Editor Through an SSH Tunnel

From your local computer, connect to the remote machine and forward local port `8886`:

```bash
ssh -L 8886:127.0.0.1:8886 USER@REMOTE_HOST
```

Replace `USER` and `REMOTE_HOST` with the remote SSH username and hostname. Then, inside the resulting SSH session, run:

```bash
cd /home/jwchoi/drive/cv-site
python3 scripts/editor_server.py --no-browser
```

The editor prints a URL containing a temporary security token, similar to:

```text
http://127.0.0.1:8886/editor/?token=...
```

Open the complete URL in a browser on your local computer. Keep the SSH connection and editor process running while editing. Press `Ctrl+C` in the SSH terminal to stop the editor.

## Use a Different Port

If port `8886` is occupied, use another port consistently in both commands. For example:

```bash
ssh -L 9876:127.0.0.1:9876 USER@REMOTE_HOST
```

Then run this on the remote machine:

```bash
cd /home/jwchoi/drive/cv-site
python3 scripts/editor_server.py --no-browser --port 9876
```

## Save and Publish the Changes

Selecting **Save and rebuild** in the editor performs the following operations on the remote machine:

1. Creates a backup in `.editor-backups/`.
2. Saves the edited JSON files.
3. Synchronizes public ORCID data.
4. Rebuilds the Korean and English websites.
5. Renders the full and one-page PDF files.
6. Validates the generated output.

After checking the result, review and publish the repository changes:

```bash
git status
git diff
git add content data
git commit -m "Update CV"
git push
```

A push to `main` triggers the GitHub Actions workflow, which rebuilds and deploys the CV through GitHub Pages.

## Troubleshooting

- **The browser cannot connect:** Confirm that the SSH session is still open and that the port number is identical in the SSH and Python commands.
- **The editor selected a different port:** Stop it and choose a free port explicitly, then update the SSH forwarding command to match.
- **PDF generation fails:** Verify that `google-chrome`, `google-chrome-stable`, `chromium`, `chromium-browser`, or `msedge` is installed on the remote machine.
- **ORCID synchronization fails:** The editor can continue with the existing ORCID snapshot, but the remote machine needs outbound internet access to retrieve current data.
- **Changes do not appear online:** Confirm that the changes were pushed to `main` and check the `Sync ORCID and deploy CV` workflow in GitHub Actions.
