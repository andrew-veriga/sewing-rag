# Google Drive Setup Guide

## Issue: "File not found" or "0 PDF files found"

If you're getting errors like "File not found" or finding 0 PDF files, it's likely a permissions issue. The service account needs explicit access to your Google Drive folder.

## Step-by-Step Setup

### 1. Get Your Service Account Email

Run the test script to see your service account email:

```bash
python test_drive_access.py
```

Or check it programmatically:
```python
from auth_service import auth_service
print(auth_service.get_service_account_email())
```

### 2. Share the Folder with Service Account

1. Open Google Drive in your browser
2. Navigate to the folder containing your PDF files
3. **Right-click** on the folder → **Share**
4. In the "Add people and groups" field, paste your **service account email**
5. Set permission to **Viewer** (or Editor if you need write access)
6. Click **Send** (you can uncheck "Notify people" if you want)

### 3. Verify Access

Run the test script again:

```bash
python test_drive_access.py
```

You should now see:
- ✓ Folder accessible
- List of files in the folder
- PDF files count

## Common Issues

### Issue: "File not found: [folder-id]"

**Solution**: The service account doesn't have access to the folder.
- Share the folder with the service account email (see step 2 above)
- Make sure you're using the correct folder ID

### Issue: "Found 0 PDF files"

**Possible causes**:
1. **Folder is empty** - Check that PDF files are actually in the folder
2. **PDFs are in subfolders** - The current implementation only searches the top level of the folder
3. **Wrong folder ID** - Verify the folder ID in your `.env` file matches the actual folder

### Issue: "Permission denied"

**Solution**: 
- Make sure the service account has at least "Viewer" access
- Check that the service account email is correct
- Verify the service account key file is valid

## Testing Folder Access

Use the provided test script:

```bash
python test_drive_access.py
```

This will:
- Show your service account email
- Test folder access
- List all files in the folder
- Show file type breakdown
- List PDF files specifically

## Finding Your Folder ID

1. Open the folder in Google Drive
2. Look at the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
3. Copy the `FOLDER_ID_HERE` part
4. Add it to your `.env` file: `GOOGLE_DRIVE_FOLDER_ID=FOLDER_ID_HERE`

## Next Steps

Once access is working:
1. Verify you can see files with `python test_drive_access.py`
2. Start the API server: `python -m app.main`
3. Test with the CLI: `python -m client.main list-drive`

