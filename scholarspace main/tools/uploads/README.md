# Student uploads (upload → review → publish)

Students upload files on the **Contribute** page. Each file is saved **privately** in your Google Drive and you get
an email. You open the review page, check the file and click **Approve** (it goes live on the site within about
5 minutes) or **Reject** (it goes to your Drive trash).

Everything runs in your own Google account with [Google Apps Script](https://script.google.com), for free.
The code is [`Code.gs`](Code.gs).

## One-time setup (about 10 minutes)

1. Sign in to Google with the account that owns the **ScholarSpace Data** Drive folder.
2. Open <https://script.google.com> → **New project**. Name it `ScholarSpace Uploads`.
3. Delete the sample code, paste in everything from `Code.gs`, and press **Save** (Ctrl+S).
4. In the function list at the top, choose **`setup`** and press **Run**.
   - Google asks for permission. Click **Review permissions**, pick your account, then
     **Advanced → Go to ScholarSpace Uploads (unsafe) → Allow**. ("Unsafe" only means you wrote the script
     yourself and Google hasn't reviewed it.)
   - This creates a `ScholarSpace Uploads` folder in your Drive with `Pending (private)`, `Approved (public)` and a
     log sheet.
5. Optional: choose **`renameOldDriveFiles`** and press **Run** once. It gives 12 older files in ScholarSpace
   Data their clean names.
6. **Deploy → New deployment →** gear icon **→ Web app**.
   - Description: `v1`
   - Execute as: **Me**
   - Who has access: **Anyone**
   - Press **Deploy** and copy the **Web app URL** (it ends in `/exec`).
7. Choose **`showReviewLink`** and press **Run**. Open **Execution log**: it prints your private review page
   link. Bookmark it and keep it secret.
8. Put the Web app URL in [`assets/js/config.js`](../../assets/js/config.js):
   ```js
   window.SS_CONFIG = {
     uploadsUrl: "https://script.google.com/macros/s/XXXX/exec"
   };
   ```
   Commit and push. The Contribute page now uploads directly. Until this is set, it falls back to email.

## Reviewing

- Every upload emails you a **Review and approve** button. The review page shows a preview, and you can fix the
  title or type before approving.
- **Approve and publish** moves the file to `Approved (public)/<subject id>/`, makes it viewable by link and
  lists it on the subject page as "Shared by <first name>".
- **Reject** moves the file to your Drive trash (restorable for 30 days).
- **Remove from site** (on an approved file) makes it private again and moves it back to Pending.
- The log sheet `ScholarSpace Uploads log` keeps every upload and decision.

## Updating the script later

Edit the code, then **Deploy → Manage deployments → ✏️ → Version: New version → Deploy**. The URL stays
the same.

## Limits and safety

- Up to 5 files per upload, 15 MB each; PDF, Word, PowerPoint, Excel, JPG and PNG only.
- At most 40 uploads per hour across everyone, plus a hidden field that catches simple bots.
- Nothing becomes public until you approve it. Uploaders' email addresses are never shown on the site.
