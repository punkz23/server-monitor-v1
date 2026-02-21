import paramiko
from paramiko.ssh_exception import AuthenticationException, SSHException
import logging

logger = logging.getLogger(__name__)

class SSHService:
    def __init__(self):
        pass

    def execute_command(self, server, command, timeout=60):
        """
        Executes a command on a remote server using Paramiko.

        Args:
            server (projects_management.models.Server): The Server object containing
                                                       hostname, user, and password.
            command (str): The command string to execute.
            timeout (int): Timeout for the SSH connection and command execution in seconds.

        Returns:
            dict: A dictionary with 'stdout', 'stderr', and 'exit_code'.
                  Returns None for all if connection or execution fails.
        """
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Be cautious with AutoAddPolicy in production

        stdout_data = ""
        stderr_data = ""
        exit_code = None

        try:
            client.connect(
                hostname=server.hostname,
                username=server.user,
                password=server.password,
                timeout=timeout,
                auth_timeout=timeout # Added auth_timeout
            )
            
            # Combine cd into the command to ensure it's executed in the correct path
            full_command = f"cd {server.path} && {command}"
            
            stdin, stdout, stderr = client.exec_command(full_command, timeout=timeout)
            
            stdout_data = stdout.read().decode().strip()
            stderr_data = stderr.read().decode().strip()
            exit_code = stdout.channel.recv_exit_status()

            logger.info(f"Command '{command}' on {server.user}@{server.hostname} exited with {exit_code}")
            if stdout_data:
                logger.debug(f"STDOUT: {stdout_data}")
            if stderr_data:
                logger.warning(f"STDERR: {stderr_data}")

        except AuthenticationException as e:
            logger.error(f"SSH Authentication failed for {server.user}@{server.hostname}: {e}")
            stderr_data = f"Authentication failed: {e}"
            exit_code = 255 # Standard exit code for authentication failures
        except SSHException as e:
            logger.error(f"SSH error for {server.user}@{server.hostname}: {e}")
            stderr_data = f"SSH error: {e}"
            exit_code = 255
        except TimeoutError:
            logger.error(f"SSH connection or command execution timed out for {server.user}@{server.hostname}")
            stderr_data = "SSH connection or command execution timed out."
            exit_code = 255
        except Exception as e:
            logger.error(f"An unexpected error occurred during SSH connection or command execution: {e}")
            stderr_data = f"Unexpected error: {e}"
            exit_code = 255
        finally:
            client.close()

        return {
            "stdout": stdout_data,
            "stderr": stderr_data,
            "exit_code": exit_code
        }

# Instantiate the service for easy import
ssh_service = SSHService()
