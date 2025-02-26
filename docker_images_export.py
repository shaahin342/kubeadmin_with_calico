import subprocess

def get_running_containers():
    try:
        # Get the list of running container IDs
        result = subprocess.run(
            ['docker', 'ps', '-q'],
            check=True,
            capture_output=True,
            text=True
        )
        container_ids = result.stdout.strip().split('\n')
        return [cid for cid in container_ids if cid]
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while listing containers: {e}")
        return []

def export_container(container_id, output_file):
    try:
        # Run the docker export command
        subprocess.run(
            ['docker', 'export', container_id, '-o', output_file],
            check=True
        )
        print(f"Container {container_id} exported to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while exporting container {container_id}: {e}")

def export_all_running_containers():
    container_ids = get_running_containers()
    if not container_ids:
        print("No running containers found.")
        return

    for container_id in container_ids:
        output_file = f"{container_id}_backup.tar"
        export_container(container_id, output_file)

if __name__ == "__main__":
    export_all_running_containers()