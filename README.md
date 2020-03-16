## Run db and python application containers with Docker

#### specifications

1) The python application accepts a `--add` flag which triggers read data from a file and inserts it in postgres, and a 
`--dump` flag which reads data from pg table and dumps it to file. 

2) We want data persistence through the use of volumes:  

    **a.** ability to create a new postgres container with the data of a previous one.   
    **b.** ability to create a new postgres container with a new empty volume.    
    
#### 1) ch_app + optional flags.
Let's run the ch_app service, which will automatically trigger the creation of the pg_app service. 
This is because of lines 39-40 in the `docker-compose.yml`, stating that the ch_app depends on the db_app
so the latter will be run first. 
 
`$ docker-compose run ch_app --add`

```
The --add flag was passed, reading and inserting these lines in the db:

a linea
b lineb
c linec
```

In case you realise you made a mistake in the script and need to modify it, you'll need to remove container and image 
and re run. 
  
`docker-compose down && docker image rm -f project_ch_app`

or use the Makefile command `make clean_app`.

Let's run the ch_app service again with both the --add and the --dump flag. The expected behaviour is that

(1) the lines of the file will be added to the database whose data is preserved through the use of volume the 
`postgres_data` folder which was bind-mounted by the Docker daemon to the file system of the container. 

(2) the new dump.txt (if you don't want to overwrite it, change name of the file before re running command)
will contain 6 lines. 

`docker-compose run ch_app --add --dump`

```
The --add flag was passed, reading and inserting these lines in the db:

a linea
b lineb
c linec

The --dump flag was passed.

the following lines were written to file

(1, 'a', 'linea')
(2, 'b', 'lineb')
(3, 'c', 'linec')
(4, 'a', 'linea')
(5, 'b', 'lineb')
(6, 'c', 'linec')
```

let's check the file:
`cd code && cat dump.txt`  
>(1, 'a', 'linea')  
(2, 'b', 'lineb')  
(3, 'c', 'linec')  
(4, 'a', 'linea')  
(5, 'b', 'lineb')  
(6, 'c', 'linec')  

Good!

let's check the database by using the `make psql` command (the IP of the db has been hardcoded in the Makefile)

```
ch_db=# select * from test_app;  
 id | alpha_ls | data  
----+----------+-------  
  1 | a        | linea  
  2 | b        | lineb  
  3 | c        | linec  
  4 | a        | linea  
  5 | b        | lineb  
  6 | c        | linec  
(6 rows)  
```

#### 2) Leverage volumes flexibility.

Say we want to start a database container from scratch, but do not want to lose the data in the db have built so far. 

- first we need to dump existing dockerized database to a file. 
Find the name of the container: `docker container ls -a`

```textmate
CONTAINER ID        IMAGE               COMMAND                  CREATED              STATUS                          PORTS                    NAMES
9fde8061d1b2        project_ch_app      "python3 /code/app.p…"   About a minute ago   Exited (0) About a minute ago                            project_ch_app_run_2
8216c3ffffcd        project_ch_app      "python3 /code/app.p…"   About a minute ago   Exited (0) About a minute ago                            project_ch_app_run_1
3769931f8dcd        postgres            "docker-entrypoint.s…"   About a minute ago   Up About a minute               0.0.0.0:5432->5432/tcp   project_ch_pg_1
```

Note the two exited containers, from when we run the `docker-compose run ch_app` twice. 

- dump the data from the `project_ch_pg_1` container. 

```docker exec -t project_ch_pg_1 pg_dumpall -c -U ch_user > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql```

- delete all existing containers, volumes, images and delete and recreate the folder to bind-mount for the 
postgres volume. 

`make clean_all`

Now imagine that after some work, we want to pick up where we left, restoring the dump file. 
- restart the postgres container in detached mode:  
`docker-compose run -d ch_pg`

- check this worked by listing all containers with  
`docker container ls -a`
```textmate
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
3ddf957f2498        postgres            "docker-entrypoint.s…"   9 seconds ago       Up 8 seconds        5432/tcp            project_ch_pg_run_1
```
**Note** that the named volumes declared at the bottom of the `docker-compose.yml` have been created too:  
`docker volume ls`
```textmate
DRIVER              VOLUME NAME
local               project_ch_app_data
local               project_postgres_data
```
- find the volumes available in the Docker container (assume you have `jq` installed - otherwise pipe to `python -m json.tool`)  
`docker inspect -f '{{ json .Mounts }}' 3ddf957f2498 | jq .`
```textmate
[
  {
    "Type": "volume",
    "Name": "project_postgres_data",
    "Source": "/var/lib/docker/volumes/project_postgres_data/_data",
    "Destination": "/var/lib/postgresql/data",
    "Driver": "local",
    "Mode": "rw",
    "RW": true,
    "Propagation": ""
  }
]
```
The volume path is `/var/lib/postgresql/data`

- copy dump into one of the volumes (`docker cp </path/to/dump/in/host> <container_name>:<path_to_volume>`):
`docker cp ./dump_16-03-2020_13_26_13.sql project_ch_pg_run_1:/var/lib/postgresql/data`

- get the database owner to run pg_restore command:  
`docker exec project_ch_pg_run_1 psql -U ch_user -l `  # remember that the user is not `postgres` but `ch_user`. 
```textmate
                               List of databases
   Name    |  Owner  | Encoding |  Collate   |   Ctype    |  Access privileges  
-----------+---------+----------+------------+------------+---------------------
 ch_db     | ch_user | UTF8     | en_US.utf8 | en_US.utf8 | 
 postgres  | ch_user | UTF8     | en_US.utf8 | en_US.utf8 | 
 template0 | ch_user | UTF8     | en_US.utf8 | en_US.utf8 | =c/ch_user         +
           |         |          |            |            | ch_user=CTc/ch_user
 template1 | ch_user | UTF8     | en_US.utf8 | en_US.utf8 | =c/ch_user         +
           |         |          |            |            | ch_user=CTc/ch_user
(4 rows)

```
- run pg_restore from within the containerized database (use psql + absolute path to the dump file):

 `docker exec project_ch_pg_run_1 psql -U ch_user -d ch_db -1 -f var/lib/postgresql/data/dump_16-03-2020_13_26_13.sql`
 
 - check that the data is in the table by running the `ch_app` service with the `--dump` flag.  
 `docker-compose run ch_app --dump`
 
 ```textmate
The --dump flag was passed.
the following lines were written to file

(1, 'a', 'linea')
(2, 'b', 'lineb')
(3, 'c', 'linec')
(4, 'a', 'linea')
(5, 'b', 'lineb')
(6, 'c', 'linec')
```

It worked! 

- clean everything:  
`make clean_all`
