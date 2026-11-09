# TeachUs

A complete classroom attendance workspace built with Streamlit. Teachers create subjects, invite a class, enrol students, and review attendance suggested from class photos or a recorded roll call. Students join with a code, contribute face photos, and follow their own attendance.

## Features

- Separate Teacher and Student entry, email/password accounts, salted PBKDF2-SHA256 password hashes, and session-based sign-in.
- Unique subject join codes and copyable invitation links. A link pre-fills the student join form after sign-in.
- Manual enrolment by name and email, or group-photo enrolment with a teacher-confirmed identity for every selected face. A manually enrolled student claims their existing roster profile by signing up with the same email.
- Single-person photo upload or camera capture; multiple SFace embeddings per student improve recognition across angles. Group enrolment stores aligned face crops rather than the whole group image.
- Attendance from multiple class photos, voice roll calls, or a manual roll call. A results dialog shows present/absent suggestions; teachers enable overrides, review the date, and explicitly save.
- Per-subject history, date filters, CSV export, student attendance percentages, and private student history downloads.
- One database interface with SQLite/files locally or Supabase Postgres/private Storage in the cloud. UI components do not issue database or storage queries.
- Responsive theme, subject cards, empty states, camera/audio inputs, dialogs, and toast feedback.

## Local setup

Use Python **3.11** (the tested runtime), with a working internet connection for first-use model downloads.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`. Select Teacher or Student and create an account. Create a subject as a teacher; open it and share its join code. Use a separate browser session or sign out to try the student experience.

Without Supabase secrets, the app creates `data/teachus.db`, `data/photos/`, and model caches under `data/`. Set `TEACHUS_DATA_DIR` to an absolute directory to change that location. SQLite is useful for local use; files on Streamlit Community Cloud are ephemeral, so configure Supabase for durable deployed data.

The source repository starts without data. If you ran an earlier stub version, back up and remove its incompatible local `data/teachus.db` before running this implementation; this app does not silently migrate or delete old databases.

## Supabase setup

1. Create a Supabase project and keep its database credentials private.
2. Open the project's **SQL Editor**, paste all of [`supabase/schema.sql`](supabase/schema.sql), and run it. It creates `users`, `subjects`, `students`, `enrollments`, `photos`, and `attendance`, their constraints/indexes, and the private `face-photos` bucket.
3. In the Supabase project settings, copy the project URL and the **service_role** API key (legacy JWT service role key). The app needs server database/storage privileges. An anon or publishable key will not work with this schema.
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in:

   ```toml
   SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
   SUPABASE_KEY = "YOUR_SERVICE_ROLE_KEY"
   APP_URL = "https://YOUR_APP.streamlit.app"
   ```

5. Restart Streamlit. Its sidebar should say **Cloud database connected**. Create teacher/student accounts, join a subject, upload a face photo, and save attendance to verify both database and Storage access.

Both Supabase credentials must be present to enable the cloud backend. A partial configuration produces an error rather than silently writing to local storage. `APP_URL` is optional and sets the canonical invitation-link host; without it links use localhost and the join code still works.

**Security model:** this app uses its own password authentication; it does not use Supabase Auth. All data access runs on the Streamlit server with the service role key. Row-level security and revoked grants deny direct access by `anon` and `authenticated` clients. Application methods restrict teachers to their subjects and students to their own history/photos. The private Storage policy allows the server role only. Never give the service key to students, embed it in a URL, or expose it through frontend code. Do not add permissive public policies.

## Streamlit Community Cloud deployment

Deployment and repository publication are performed by the project owner; no accounts or deployment are created by this repository.

1. Commit the app to your GitHub repository, including `requirements.txt`, `packages.txt`, `.streamlit/config.toml`, and `supabase/schema.sql`. Do **not** commit `.streamlit/secrets.toml`, face images, local databases, or model files.
2. Set up Supabase using the steps above. Use a separate project for production if you have test records.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with access to the repository. Choose **Create app** and select the repository, deployment branch, and main file **`app.py`**.
4. Open **Advanced settings**, choose Python **3.11**, and paste the Supabase values into the **Secrets** field. Include the eventual public app URL as `APP_URL` (you can update it after deployment).
5. Deploy. Community Cloud installs the pinned Python packages and the libraries in `packages.txt`. Models are loaded only when photo/voice processing is first requested.
6. Set `APP_URL` to the final `https://…streamlit.app` address in app settings and restart if needed.
7. Verify: teacher sign-up → create subject → enrol student → add photo → class-photo attendance → review/override/save → history/CSV. In another session, verify student sign-up → join code → own photo upload → own attendance. Record a voice roll call and verify the displayed transcript before saving.
8. Keep Supabase backups configured for your needs and restrict access to Streamlit app secrets. A sleeping/restarted Cloud app keeps its Supabase records but may need to download model caches again.

## Recognition and roll calls

Face processing uses the official [OpenCV Zoo YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) `2023mar` and [SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface) `2021dec` ONNX model artifacts, hosted in the OpenCV Zoo GitHub repository. Downloads are verified against their published LFS SHA-256 digests before atomic cache installation. YuNet is about 233 KB; SFace about 39 MB. No dlib, GPU, or external face-recognition service is used.

The default cosine threshold is **0.50**, more conservative than the SFace example's 0.363 benchmark threshold. Matches within 0.06 of another student are treated as ambiguous. Each student's best enrolled embedding is compared. Thresholds are implementation defaults, not a guarantee of classroom accuracy: lighting, image quality, pose, and similar faces affect results. Use clear photos with consent and review every suggestion. The app never saves an automatic attendance decision without teacher confirmation.

Voice input is transcribed with **faster-whisper tiny**, CPU/int8, English, then full names are matched using RapidFuzz at an 86-point cutoff. Short names require exact tokens to avoid matching “Ann” inside “Joanne.” Read **only the full names of present students**, with pauses. This is spoken-name matching, not speaker identification or proof of presence. It cannot understand “Alice is absent”; saying an absent student's name can suggest that student as present. Identical names need manual review. The review dialog displays the transcript, including when no roster names match.

The first voice operation downloads the tiny model (roughly 75 MB). CPU transcription can take time on free-tier resources. Files and recordings are limited to 10 MB; at most ten class photos or five enrolment photos can be processed per action. Audio and class images are processed in memory/temporary files and are not saved; enrolled face crops and embeddings are stored privately.

## Privacy and operational limits

Use the app in a trusted classroom with permission to store face photos and appropriate institutional approval. Account emails are not verified and password reset/email delivery are not implemented: protect public access according to your institution's requirements. Session throttling slows repeated login attempts within one browser session; this is not a replacement for a production identity provider or network-level rate limits.

Attendance is one record per student, subject, and local server date. A second save replaces that day's status rather than adding another class period. Overrides and input source are retained on the current record; this is not a full immutable audit log. The roster is checked again on save, and a changed roster requires a fresh review. Student percentages use recorded attendance days, excluding days with no record.

Face photos follow the student profile across their joined subjects so teachers can reuse enrolment images. Teachers can only read embeddings for students in their own roster. The app has no self-service account deletion or recovery; the operator must handle retention, deletion, and forgotten-password requests in the database and private bucket according to school policy. Do not treat this prototype as a verified identity system.

## Tests and checks

```bash
python -m pytest -q
streamlit run app.py --server.headless true
```

Tests use isolated SQLite files and synthetic embeddings; they do not download models or require Supabase credentials. They cover authentication, enrolment/claiming, access restrictions, atomic date upserts, persistence, storage, CSV escaping, face ambiguity/thresholds, model checksum handling, fuzzy name boundaries, transcription error reporting, and Streamlit AppTest home/role workspace smoke tests.

No live Supabase integration test is possible without an operator-provided project. Run the deployment verification steps after setting credentials. Recognition tests with synthetic embeddings validate the matching rules; they do not measure real-world recognition accuracy.
