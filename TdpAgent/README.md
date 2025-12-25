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









mysql -u root -p -h 127.0.0.1 -P 3306
password : Hashim#06


fastapi_app.service
fastapi_worker.service


sudo nano /etc/systemd/system/worker-poller.service
sudo nano /etc/systemd/system/fastapi-server.service


sudo systemctl daemon-reload


sudo systemctl stop worker-poller.service
sudo systemctl restart worker-poller.service

sudo systemctl stop fastapi-server.service
sudo systemctl restart fastapi-server.service
