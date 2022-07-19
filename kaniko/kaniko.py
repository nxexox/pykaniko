import os
import json
import subprocess
from enum import Enum
from typing import List, Optional, AnyStr, Callable
from base64 import b64encode


class KanikoSnapshotMode(Enum):
    full = 'full'
    time = 'time'


class KanikoVerbosity(Enum):
    panic = 'panic'
    fatal = 'fatal'
    error = 'error'
    warn = 'warn'
    info = 'info'
    debug = 'debug'


class KanikoBuildException(Exception):
    exit_code: int
    body: List[str]

    def __init__(self, exit_code: int, body: List[str]):
        self.exit_code = exit_code
        self.body = body

        body_string = "\n".join(body)
        super().__init__(f'Kaniko failed with exit code {exit_code}: {body_string}')


class Kaniko(object):
    """
    Service for building images without Docker

    For installation kaniko add in your Dockerfile the next lines
    >>> FROM gcr.io/kaniko-project/executor:v0.12.0 AS kaniko
    >>>
    >>> FROM <your docker repo>
    >>>
    >>> ENV DOCKER_CONFIG /kaniko/.docker
    >>>
    >>> COPY --from=kaniko /kaniko /kaniko
    >>>
    >>> ...
    """

    """
    Path to registry for auth config
    """
    docker_registry_uri: Optional[str] = None

    """
    Login for auth config
    """
    registry_username: Optional[str] = None

    """
    Password for auth config
    """
    registry_password: Optional[str] = None

    """
    This flag allows you to pass in ARG values at build time, similarly to Docker. You can set it multiple times for
    multiple arguments.
    """
    build_args: List[str] = []

    """
    Set context dir
    """
    context: Optional[str] = None

    """
    Set this flag as --cache=true to opt in to caching with kaniko.
    """
    cache: bool = False

    """
    Set this flag to specify a local directory cache for base images. Defaults to /cache.

    This flag must be used in conjunction with the --cache=true flag.
    """
    cache_dir: Optional[str] = None

    """
    Set this flag to specify a remote repository which will be used to store cached layers.

    If this flag is not provided, a cache repo will be inferred from the --destination flag.
    If --destination=gcr.io/kaniko-project/test, then cached layers will be stored in gcr.io/kaniko-project/test/cache.

    This flag must be used in conjunction with the --cache=true flag.
    """
    cache_repo: Optional[str] = None

    """
    Destination of final image.
    Example: gcr.io/my-repo/my-image
    """
    destination: Optional[str] = None

    """
    Set this flag to specify a file in the container. This file will receive the digest of a built image.
    This can be used to automatically track the exact image built by Kaniko.

    For example, setting the flag to --digest-file=/dev/termination-log will write the digest to that file,
    which is picked up by Kubernetes automatically as the {{.state.terminated.message}} of the container.
    """
    digest_file: Optional[str] = None

    """
    Path to Dockerfile
    """
    dockerfile: Optional[str] = None

    """
    To run kaniko locally
    """
    force: bool = False

    """
    Set this flag to specify a directory in the container where the OCI image layout of a built image will be placed.
    This can be used to automatically track the exact image built by Kaniko.

    For example, to surface the image digest built in a Tekton task,
    this flag should be set to match the image resource outputImageDir.

    Note: Depending on the built image, the media type of the image manifest might be either
    `application/vnd.oci.image.manifest.v1+json` or `application/vnd.docker.distribution.manifest.v2+json`.
    """
    oci_layout_path: Optional[str] = None

    """
    Set this flag to use plain HTTP requests when accessing a registry.
    It is supposed to be used for testing purposes only and should not be used in production!
    You can set it multiple times for multiple registries.
    """
    insecure_registry: List[str] = []

    """
    Set this flag to skip TLS cerificate validation when accessing a registry.
    It is supposed to be used for testing purposes only and should not be used in production!
    You can set it multiple times for multiple registries.
    """
    skip_tls_verify_registry: List[str] = []

    """
    Set this flag to clean the filesystem at the end of the build.
    """
    cleanup: bool = False

    """
    Set this flag if you want to push images to a plain HTTP registry.
    It is supposed to be used for testing purposes only and should not be used in production!
    """
    insecure: bool = False

    """
    Set this flag if you want to pull images from a plain HTTP registry.
    It is supposed to be used for testing purposes only and should not be used in production!
    """
    insecure_pull: bool = False

    """
    Set this flag if you only want to build the image, without pushing to a registry.
    """
    no_push: bool = False

    """
    Set this flag to strip timestamps out of the built image and make it reproducible.
    """
    reproducible: bool = False

    """
    This flag takes a single snapshot of the filesystem at the end of the build,
    so only one layer will be appended to the base image.
    """
    single_snapshot: bool = False

    """
    Set this flag to skip TLS certificate validation when pushing to a registry.
    It is supposed to be used for testing purposes only and should not be used in production!
    """
    skip_tls_verify: bool = False

    """
    Set this flag to skip TLS certificate validation when pulling from a registry.
    It is supposed to be used for testing purposes only and should not be used in production!
    """
    skip_tls_verify_pull: bool = False

    """
    You can set the --snapshotMode=<full (default), time> flag to set how kaniko will snapshot the filesystem.
    If --snapshotMode=time is set, only file mtime will be considered when snapshotting
    (see limitations related to mtime).
    """
    snapshot_mode: Optional[KanikoSnapshotMode] = None

    """
    Set this flag to indicate which build stage is the target build stage.
    See more: https://docs.docker.com/engine/reference/commandline/build/#specifying-target-build-stage---target
    """
    target: Optional[str] = None

    """
    Set this flag as --tarPath=<path> to save the image as a tarball at path instead of pushing the image.
    """
    tar_path: Optional[str] = None

    """
    Set this flag as --verbosity=<panic|fatal|error|warn|info|debug> to set the logging level. Defaults to info.
    """
    verbosity: Optional[KanikoVerbosity] = None

    """
    Path to kaniko
    """
    kaniko_path: str = '/kaniko'

    def __init__(self):
        self._configure_attribute_names = tuple([
            key
            for key in self.__class__.__dict__.keys()
            if not key.startswith('_')
        ])

    def build(self, **kwargs) -> List[str]:
        """
        Build docker image

        :return: kaniko logs
        :rtype: str

        :raise KanikoBuildException: if kaniko failed
        """
        self.configure(**kwargs)
        self._write_config()

        res = subprocess.Popen(self.shell_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        res.wait()

        exit_code = res.returncode
        body = self._parse_logs(res.stdout.read())
        if exit_code != 0:
            raise KanikoBuildException(exit_code=exit_code, body=body)

        return body

    def configure(self, **kwargs):
        """
        Sets parameters from kwargs
        """
        for key, value in kwargs.items():
            if key not in self._configure_attribute_names or self._is_callable(key):
                continue

            setattr(self, key, value)

    @property
    def shell_command(self) -> List[str]:
        """
        :return: shell command arguments to invoke subprocess.Popen
        :rtype: List[str]
        """
        executor_path = self.kaniko_path + '/executor'

        command = [executor_path]
        for handler in self._shell_part_handlers:
            getattr(self, handler)(command)

        return command

    def _is_callable(self, attribute_name: str):
        attribute = getattr(self, attribute_name, None)
        return isinstance(attribute, Callable)

    def _make_config(self):
        return {
            'auths': {
                self.docker_registry_uri: {
                    'auth': b64encode(f'{self.registry_username}:{self.registry_password}'.encode('ascii')).decode('ascii')
                }
            }
        }

    def _write_config(self):
        config_folder_path = os.path.join(self.kaniko_path, '.docker')
        os.makedirs(config_folder_path, exist_ok=True)
        with open(os.path.join(config_folder_path, 'config.json'), 'w') as config:
            config.write(json.dumps(self._make_config()))

    def _parse_logs(self, logs: AnyStr) -> List[str]:
        rows = logs.decode('utf-8').strip().split('\n')
        return list(map(str.strip, rows))

    @property
    def _shell_part_handlers(self) -> List[str]:
        return [method for method in dir(self) if method.startswith('_get_shell_part_')]

    def _get_shell_part_build_args(self, command: List[str]):
        for arg in self.build_args:
            command.append(f'--build-arg={arg}')

    def _get_shell_part_context(self, command: List[str]):
        if self.context:
            command.append(f'--context={self.context}')

    def _get_shell_part_cache(self, command: List[str]):
        if self.cache:
            command.append('--cache')

    def _get_shell_part_cache_dir(self, command: List[str]):
        if self.cache_dir:
            command.append(f'--cache-dir={self.cache_dir}')

    def _get_shell_part_cache_repo(self, command: List[str]):
        if self.cache_repo:
            command.append(f'--cache-repo={self.cache_repo}')

    def _get_shell_part_destination(self, command: List[str]):
        if self.destination:
            if isinstance(self.destination, list):
                for _destination in self.destination:
                    command.append(f'--destination={_destination}')
            else:
                command.append(f'--destination={self.destination}')

    def _get_shell_part_digest_file(self, command: List[str]):
        if self.digest_file:
            command.append(f'--digest-file={self.digest_file}')

    def _get_shell_part_dockerfile(self, command: List[str]):
        if self.dockerfile:
            command.append(f'--dockerfile={self.dockerfile}')

    def _get_shell_part_force(self, command: List[str]):
        if self.force:
            command.append('--force')

    def _get_shell_part_oci_layout_path(self, command: List[str]):
        if self.oci_layout_path:
            command.append(f'--oci-layout-path={self.oci_layout_path}')

    def _get_shell_part_insecure_registry(self, command: List[str]):
        for arg in self.insecure_registry:
            command.append(f'--insecure-registry={arg}')

    def _get_shell_part_skip_tls_verify_registry(self, command: List[str]):
        for arg in self.skip_tls_verify_registry:
            command.append(f'--skip-tls-verify-registry={arg}')

    def _get_shell_part_cleanup(self, command: List[str]):
        if self.cleanup:
            command.append('--cleanup')

    def _get_shell_part_insecure(self, command: List[str]):
        if self.insecure:
            command.append('--insecure')

    def _get_shell_part_insecure_pull(self, command: List[str]):
        if self.insecure_pull:
            command.append('--insecure-pull')

    def _get_shell_part_no_push(self, command: List[str]):
        if self.no_push:
            command.append('--no-push')

    def _get_shell_part_reproducible(self, command: List[str]):
        if self.reproducible:
            command.append('--reproducible')

    def _get_shell_part_single_snapshot(self, command: List[str]):
        if self.single_snapshot:
            command.append('--single-snapshot')

    def _get_shell_part_skip_tls_verify(self, command: List[str]):
        if self.skip_tls_verify:
            command.append('--skip-tls-verify')

    def _get_shell_part_skip_tls_verify_pull(self, command: List[str]):
        if self.skip_tls_verify_pull:
            command.append('--skip-tls-verify-pull')

    def _get_shell_part_snapshot_mode(self, command: List[str]):
        if self.snapshot_mode:
            command.append(f'--snapshotMode={self.snapshot_mode.value}')

    def _get_shell_part_target(self, command: List[str]):
        if self.target:
            command.append(f'--target={self.target}')

    def _get_shell_part_tar_path(self, command: List[str]):
        if self.tar_path:
            command.append(f'--tarPath={self.tar_path}')

    def _get_shell_part_verbosity(self, command: List[str]):
        if self.verbosity:
            command.append(f'--verbosity={self.verbosity.value}')
