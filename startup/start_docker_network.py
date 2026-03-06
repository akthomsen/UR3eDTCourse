import docker

def start_docker_network(network_name="shared-communication"):
    """
    Creates a Docker bridge network if it doesn't already exist.
    Equivalent to: docker network create shared-communication
    """
    client = docker.from_env()

    try:
        # Check if the network already exists
        existing_networks = client.networks.list(names=[network_name])
        if existing_networks:
            print(f"ℹ Network '{network_name}' already exists.")
            return existing_networks[0]

        # Create the network
        network = client.networks.create(
            name=network_name,
            driver="bridge",
            check_duplicate=True
        )
        print(f"✓ Successfully created network: {network_name}")
        return network

    except docker.errors.APIError as e:
        print(f"✗ Failed to create network: {e}")
        return None

if __name__ == "__main__":
    start_docker_network()