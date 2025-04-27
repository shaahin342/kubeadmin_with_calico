import os
import docker

# Create a directory to store the images
os.makedirs('docker_images', exist_ok=True)

# Initialize the Docker client
client = docker.from_env()

# Get a list of all Docker images
images = client.images.list()

# Iterate over each image
for image in images:
    # Get the image tags
    tags = image.tags
    if not tags:
        # Skip images without tags
        continue

    for tag in tags:
        # Replace any slashes in the image name with underscores for the filename
        filename = tag.replace('/', '_') + '.tar'

        # Save the Docker image to a file
        print(f"Saving {tag} to docker_images/{filename}")
        with open(f'docker_images/{filename}', 'wb') as f:
            for chunk in image.save(named=True):
                f.write(chunk)

print("All images have been saved.")