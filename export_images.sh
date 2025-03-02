#!/bin/bash

# Function to get the list of running container IDs
get_running_containers() {
    # Get the list of running container IDs
    container_ids=$(docker ps -q)
    # Convert the string into an array
    IFS=' ' read -r -a ids_array <<< "$container_ids"
    echo "${ids_array[@]}"
}

# Function to export a specific container to a file
export_container() {
    container_id=$1
    output_file=$2
    # Run the docker export command
    if docker export "$container_id" -o "$output_file"; then
        echo "Container $container_id exported to $output_file"
    else
        echo "An error occurred while exporting container $container_id"
    fi
}

# Function to export all running containers
export_all_running_containers() {
    container_ids=( $(get_running_containers) )
    if [ ${#container_ids[@]} -eq 0 ]; then
        echo "No running containers found."
        return
