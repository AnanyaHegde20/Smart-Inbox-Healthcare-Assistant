"""
Docker Configuration Validation Script
Validates that all Docker configuration files are correctly structured.
"""

import os
import sys
import yaml
import json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def check_file_exists(path, description):
    """Check if a file exists and report status."""
    full_path = os.path.join(PROJECT_ROOT, path)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        print(f"  [OK] {description}: {path} ({size} bytes)")
        return True
    else:
        print(f"  [FAIL] {description}: {path} - NOT FOUND")
        return False


def validate_docker_compose():
    """Validate docker-compose.yml structure."""
    print("\n=== Validating docker-compose.yml ===")
    path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
    
    if not os.path.exists(path):
        print("  [FAIL] docker-compose.yml not found")
        return False
    
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required top-level keys
        required_keys = ['version', 'services', 'volumes', 'networks']
        for key in required_keys:
            if key in config:
                print(f"  [OK] Has '{key}' section")
            else:
                print(f"  [FAIL] Missing '{key}' section")
                return False
        
        # Check services
        services = config['services']
        required_services = ['ai-service', 'backend', 'frontend']
        for service in required_services:
            if service in services:
                print(f"  [OK] Service '{service}' defined")
                svc = services[service]
                
                # Check required fields
                if 'build' in svc:
                    print(f"    [OK] Has build configuration")
                else:
                    print(f"    [WARN] No build configuration")
                
                if 'ports' in svc:
                    print(f"    [OK] Has ports: {svc['ports']}")
                
                if 'environment' in svc:
                    print(f"    [OK] Has environment variables")
                
                if 'healthcheck' in svc:
                    print(f"    [OK] Has health check")
                else:
                    print(f"    [WARN] No health check defined")
            else:
                print(f"  [FAIL] Service '{service}' not defined")
                return False
        
        print("  [OK] docker-compose.yml is valid")
        return True
        
    except yaml.YAMLError as e:
        print(f"  [FAIL] Invalid YAML: {e}")
        return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def validate_dockerfiles():
    """Validate Dockerfiles exist and have correct structure."""
    print("\n=== Validating Dockerfiles ===")
    
    dockerfiles = [
        ("ai-service/Dockerfile", "Python AI Service"),
        ("backend/Dockerfile", "Spring Boot Backend"),
        ("frontend/Dockerfile", "Angular Frontend")
    ]
    
    all_valid = True
    for path, description in dockerfiles:
        full_path = os.path.join(PROJECT_ROOT, path)
        if not os.path.exists(full_path):
            print(f"  [FAIL] {description}: {path} not found")
            all_valid = False
            continue
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Check for required instructions
        checks = {
            'FROM': 'Base image',
            'WORKDIR': 'Working directory',
            'EXPOSE': 'Exposed port',
            'CMD': 'Start command'
        }
        
        print(f"  [OK] {description}: {path}")
        for instruction, desc in checks.items():
            if instruction in content:
                print(f"    [OK] Has {desc} ({instruction})")
            else:
                print(f"    [WARN] Missing {desc} ({instruction})")
        
        # Check for multi-stage build
        from_count = content.count('\nFROM ') + (1 if content.startswith('FROM ') else 0)
        if from_count > 1:
            print(f"    [OK] Multi-stage build ({from_count} stages)")
        
        # Check for non-root user
        if 'USER' in content:
            print(f"    [OK] Runs as non-root user")
        else:
            print(f"    [WARN] No USER instruction (runs as root)")
        
        # Check for health check
        if 'HEALTHCHECK' in content:
            print(f"    [OK] Has health check")
        else:
            print(f"    [WARN] No health check defined")
    
    return all_valid


def validate_env_files():
    """Validate .env.example and .dockerignore files."""
    print("\n=== Validating Environment Files ===")
    
    files = [
        (".env.example", "Environment template"),
        ("ai-service/.dockerignore", "AI Service .dockerignore"),
        ("backend/.dockerignore", "Backend .dockerignore"),
        ("frontend/.dockerignore", "Frontend .dockerignore"),
        ("frontend/nginx.conf", "Nginx configuration")
    ]
    
    all_valid = True
    for path, description in files:
        if check_file_exists(path, description):
            if path.endswith('.dockerignore'):
                with open(os.path.join(PROJECT_ROOT, path), 'r') as f:
                    content = f.read()
                    if 'node_modules' in content or '__pycache__' in content or 'target' in content:
                        print(f"    [OK] Has appropriate ignore patterns")
        else:
            all_valid = False
    
    return all_valid


def validate_port_configuration():
    """Validate port mappings are consistent."""
    print("\n=== Validating Port Configuration ===")
    
    path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    expected_ports = {
        'ai-service': '8001:8001',
        'backend': '8000:8000',
        'frontend': '80:80'
    }
    
    all_valid = True
    for service, expected_port in expected_ports.items():
        actual_ports = config['services'][service].get('ports', [])
        if expected_port in actual_ports:
            print(f"  [OK] {service}: {expected_port}")
        else:
            print(f"  [FAIL] {service}: Expected {expected_port}, got {actual_ports}")
            all_valid = False
    
    return all_valid


def validate_networking():
    """Validate networking configuration."""
    print("\n=== Validating Networking ===")
    
    path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check services use the same network
    network_name = 'smart-inbox-network'
    for service_name, service_config in config['services'].items():
        networks = service_config.get('networks', [])
        if network_name in networks:
            print(f"  [OK] {service_name} connected to {network_name}")
        else:
            print(f"  [FAIL] {service_name} not connected to {network_name}")
            return False
    
    # Check dependencies
    backend_deps = config['services']['backend'].get('depends_on', {})
    frontend_deps = config['services']['frontend'].get('depends_on', {})
    
    if 'ai-service' in backend_deps:
        print(f"  [OK] Backend depends on ai-service")
    else:
        print(f"  [WARN] Backend doesn't depend on ai-service")
    
    if 'backend' in frontend_deps:
        print(f"  [OK] Frontend depends on backend")
    else:
        print(f"  [WARN] Frontend doesn't depend on backend")
    
    print("  [OK] Networking configuration is valid")
    return True


def validate_security():
    """Validate security best practices."""
    print("\n=== Validating Security ===")
    
    # Check no secrets in docker-compose.yml
    path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
    with open(path, 'r') as f:
        content = f.read()
    
    secret_patterns = ['password123', 'secret_key', 'api_key=']
    for pattern in secret_patterns:
        if pattern in content:
            print(f"  [FAIL] Secret found in docker-compose.yml: {pattern}")
            return False
    
    print("  [OK] No hardcoded secrets in docker-compose.yml")
    
    # Check .env.example doesn't have real values
    env_path = os.path.join(PROJECT_ROOT, ".env.example")
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        if 'your-openai-api-key-here' in env_content:
            print(f"  [OK] .env.example has placeholder values")
        else:
            print(f"  [WARN] .env.example might have real values")
    
    print("  [OK] Security checks passed")
    return True


def main():
    """Run all validations."""
    print("=" * 60)
    print("Docker Configuration Validation")
    print("=" * 60)
    
    results = []
    
    # Run all validations
    results.append(("Docker Compose", validate_docker_compose()))
    results.append(("Dockerfiles", validate_dockerfiles()))
    results.append(("Environment Files", validate_env_files()))
    results.append(("Port Configuration", validate_port_configuration()))
    results.append(("Networking", validate_networking()))
    results.append(("Security", validate_security()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All validations passed! Docker configuration is ready.")
        print("\nTo start the application:")
        print("  docker-compose up -d")
        print("\nTo view logs:")
        print("  docker-compose logs -f")
    else:
        print("Some validations failed. Please fix the issues above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
