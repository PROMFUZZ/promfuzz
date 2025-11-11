# Fuzzing Engine — Build Instructions



## 1. Build the Docker image

```bash
cd ./Engine/ityfuzz
docker build -t dockerfile -t <IMAGE NAME> .
```


## 2. Run the container

```bash
docker run -it -v <YOUR WORKSPACE PATH>/promfuzz/:/bins/dataset/ -p 8000:8000 --name <CONTAINER NAME> <IMAGE NAME> /bin/bash
```


## 3. Get the container ID

```bash
docker inspect --format="{{.Id}}" <CONTAINER NAME>
```


## 4. Stop the container

```bash
docker stop <CONTAINER ID>
```


## Done

You can now return to the main README to continue configuring PROMFUZZ:  [Back](../README.md)
