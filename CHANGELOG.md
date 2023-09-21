## 0.1.0 (2023-09-21)

### Feat

- **config**: Enable to set RECONNECT and RETRY consts through ENVs
- **task_executer.py**: Create async task executer that fires the post requests
- **db_api.py**: Create the mysql api with LOCK for the get tasks

### Fix

- **main,db_api,task_executer**: Release the rows lock before the http requests are being made. Updating the tasks status as executing to prevent from other controller to pull them

### Refactor

- **project**: Create project base folders structure
