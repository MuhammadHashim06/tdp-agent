DROP DATABASE tdpagent;
CREATE DATABASE tdpagent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


python -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
python -m app.worker.poller  
python -m app.worker.case_watcher 

Initialize DB
python -m app.db_init 

Remove all Attachments Fetched
Remove-Item -Recurse -Force .\storage\attachments\* 

Check all Attachments Fetched
dir .\storage\attachments -Recurse -File | select FullName, Length | more