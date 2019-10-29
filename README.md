### [Kaniko](https://github.com/GoogleContainerTools/kaniko) is a tool to build container images from a Dockerfile

---

#### How to install
For installation kaniko add in your Dockerfile the next lines
```
FROM gcr.io/kaniko-project/executor:v0.12.0 AS kaniko

FROM <your docker repo>

ENV DOCKER_CONFIG /kaniko/.docker

COPY --from=kaniko /kaniko /kaniko
...
```

**pip**
```
pip install kaniko
```

---

#### How to use:
```python
from kaniko import Kaniko, KanikoSnapshotMode

kaniko = Kaniko()
kaniko.dockerfile = '/path/to/Dockerfile'
kaniko.no_push = True
kaniko.snapshot_mode = KanikoSnapshotMode.full

build_logs = kaniko.build()  # List[str]
```

Another way:
```python
from kaniko import Kaniko, KanikoSnapshotMode

kaniko = Kaniko()
build_logs = kaniko.build(
    docker_registry_uri='https://index.docker.io/v1/',
    registry_username='username',
    registry_password='password',
    destination='path-to-repo:tag',
    dockerfile='/path/to/Dockerfile',
    snapshot_mode=KanikoSnapshotMode.full,
)
```