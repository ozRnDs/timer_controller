# Overview
The timer controller component is part of the timer_project.

The component's responsibility is to extract _waiting_ tasks from the db and create webhooks.

Multiple components (pods) can work simultaneously. 

## Component Logic
1. _(INITIALIZE)_ The component will try to create connection to the set MySQL Server.
1. _(INITIALIZE)_ If the database or table in the server don't exist, the component will create them.
1. Every 0.5 seconds the component fetches and locks a list of unlocked waiting tasks from MySQL Server.
1. Each task invokes async http request.
1. Each task status is updated in the MySQL (done/failed) and the lock is released.

## Environment Variables

| Environment Variable Name | Description | Optional/Mandatory |Notes |
| -- | -- | -- | -- |
| DB_HOST | The MySQL Server's host address (ip/dns/service name) | Mandatory |The MySQL port should be 3306 in order to enable the component to connect. |
| DB_USER | The user name the component should log to the MySQL Server | Mandatory | **For production should be passed through secrets** |
| DB_PASSWORD | The password for the MySQL Server| Mandatory | **For production should be passed through secrets** |
| DB_NAME | The name of the project DB | Optional | Default: _timer_db_ |
| BATCH_SIZE | The number of tasks to pull from the DB | Optional | Default: _10_ |
| RETRY_NUMBER | Number of retries the service will do before self shutdown | Optional | Default: _10_ |
| RECONNECT_WAIT_TIME | Number of seconds to wait between reconnect retries | Optional | Default: _1_ |

## Future upgrades
1. Delete and clean old tasks after a period of time (prevent from the DB to explode)
1. Add timeouts to the webhook - to prevent handing urls from delaying other tasks.

# Quick Start
## System Compose
The component is containerized using docker. It should be deployed using the timer_project compose file with the other components of the system.
## Component Docker
The component can be deployed using docker command:
```bash
export COMPONENT_NAME=timer_controller_1
export DB_HOST=timer-db
export DB_USER=root
export DB_PASSWORD=1234
export IMAGE_NAME=timer_controller
export IMAGE_TAG=0.0.1
docker run -d --rm --name $COMPONENT_NAME -e DB_HOST=$DB_HOST -e DB_USER=$DB_USER -e DB_PASSWORD=$DB_PASSWORD $IMAGE_NAME:$IMAGE_TAG
```