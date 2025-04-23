from ..config.provision import provision

if __name__ == '__main__':    
    try:
        provision()  # Safe to call multiple times
    except RuntimeError:
        # Handle provisioning failure (e.g., exit app)
        exit(1)